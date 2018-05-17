import csv
import io
import json
import os
import re
import sys

from contextlib import ExitStack
from itertools import chain, repeat, islice
from pathlib import Path
from string import ascii_letters, digits, punctuation
from textwrap import wrap

from smart_open import smart_open
from tabulate import tabulate
from terminaltables import SingleTable
from typing import List, Mapping, TextIO, Union

__all__ = [
    'ReadStructure',
    'Sample',
    'SampleSheet']

DESIGN_HEADER = ['Sample_ID', 'Sample_Name', 'Library_ID', 'Description']
RECOMMENDED_KEYS = ['Sample_ID', 'Sample_Name', 'index']
REQUIRED_SECTIONS = ['Header', 'Settings', 'Reads', 'Data']

# The minimum column with of a detected TTY for wrapping text in CLI columns.
MIN_WIDTH = 10

# From the section "Character Encoding" in the Illumina format specification.
#
# https://www.illumina.com/content/dam/illumina-marketing/
#     documents/products/technotes/
#     sequencing-sheet-format-specifications-technical-note-970-2017-004.pdf
VALID_ASCII = set(ascii_letters + digits + punctuation + ' \n\r')


class ReadStructure(object):
    """An object describing the order, number, and type of bases in a read.

    A read structure is a sequence of tokens in the form <number><type> where
    <type> can describe template, skip, index, or UMI bases.

        - T: template base
        - S: skipped base
        - B: sample index
        - M: unique molecular identifer

    Parameters
    ----------
    structure : str
        String representation of a read structure.

    Examples
    --------
    >>> rs = ReadStructure("10M141T8B")
    >>> rs.is_paired_end
    False
    >>> rs.has_umi
    True
    >>> rs.tokens
    ['10M', '141T', '8B']

    Notes
    -----
    This class does not currently support read structures where the last token
    has ambiguous length by using the <+> operator preceding the <type>.

    Definitions of read structure types can be found at the following location:

        https://github.com/nh13/read-structure-examples

    Discussion on the topic in hts-specs:

        https://github.com/samtools/hts-specs/issues/270

    """
    _token_pattern = re.compile(r'(\d+[BMST])')

    # Token can repeat one or more times along the entire string.
    _valid_pattern = re.compile(r'^{}+$'.format(_token_pattern.pattern))

    _index_pattern = re.compile(r'(\d+B)')
    _umi_pattern = re.compile(r'(\d+M)')
    _skip_pattern = re.compile(r'(\d+S)')
    _template_pattern = re.compile(r'(\d+T)')

    def __init__(self, structure: str):
        if not bool(self._valid_pattern.match(structure)):
            raise ValueError(f'Not a valid read structure: "{structure}"')
        self.structure = structure

    @property
    def is_indexed(self) -> bool:
        """Return if this read structure has sample indexes."""
        return len(self._index_pattern.findall(self.structure)) > 0

    @property
    def is_single_indexed(self) -> bool:
        """Return if this read structure is single indexed."""
        return len(self._index_pattern.findall(self.structure)) == 1

    @property
    def is_dual_indexed(self) -> bool:
        """Return if this read structure is dual indexed."""
        return len(self._index_pattern.findall(self.structure)) == 2

    @property
    def is_single_end(self) -> bool:
        """Return if this read structure is single-end."""
        return len(self._template_pattern.findall(self.structure)) == 1

    @property
    def is_paired_end(self) -> bool:
        """Return if this read structure is paired-end."""
        return len(self._template_pattern.findall(self.structure)) == 2

    @property
    def has_indexes(self) -> bool:
        """Return if this read structure has any index tokens."""
        return len(self._index_pattern.findall(self.structure)) > 0

    @property
    def has_skips(self) -> bool:
        """Return if this read structure has any skip tokens."""
        return len(self._skip_pattern.findall(self.structure)) > 0

    @property
    def has_umi(self) -> bool:
        """Return if this read structure has any UMI tokens."""
        return len(self._umi_pattern.findall(self.structure)) > 0

    @property
    def index_cycles(self) -> int:
        """The number of cycles dedicated to indexes."""
        tokens = self._index_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def template_cycles(self) -> int:
        """The number of cycles dedicated to template."""
        tokens = self._template_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def skip_cycles(self) -> int:
        """The number of cycles dedicated to skips."""
        tokens = self._skip_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def umi_cycles(self) -> int:
        """The number of cycles dedicated to UMI."""
        tokens = self._umi_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def total_cycles(self) -> int:
        """The number of total number of cycles in the structure."""
        return sum((int(re.sub(r'\D', '', token)) for token in self.tokens))

    @property
    def tokens(self) -> List[str]:
        """Return a list of all tokens in the read structure."""
        return self._token_pattern.findall(self.structure)

    def copy(self):
        """Returns a deep copy of this read structure."""
        return ReadStructure(self.structure)

    def __eq__(self, other):
        """Read structures are equal if their string repr are equal."""
        return self.structure == other.structure

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'structure="{self.structure}")')

    def __str__(self):
        return self.structure


class Sample(object):
    """A single sample for a sample sheet.

    This class is built with the keys and values in the [Data] section of the
    sample sheet. Although no keys are explicitly required it is recommended to
    at least use "Sample_ID", "Sample_Name", and "index". All keys with
    whitespace will have the whitespace replaced with a single underscore. If
    the key "Read_Structure" is provided then its value is promoted to class
    ``ReadStructure`` and additional functionality is enabled.

    Parameters
    ----------
    mappable : dict, optional
        The key-value pairs describing this sample.

    Examples
    --------
    >>> sample = Sample({"Sample_ID": "87", "Sample_Name": "3T", "index": "A"})
    >>> sample
    Sample({"Sample_ID": "87", "Sample_Name": "3T", "index": "A"})
    >>> sample = Sample({'Read_Structure': '151T'})
    >>> sample.Read_Structure
    ReadStructure(structure="151T")

    """

    def __init__(self, mappable: Union[None, Mapping]=None):
        mappable = dict() if mappable is None else mappable
        self._other_keys = set()

        self._whitespace_re = re.compile(r'\s+')
        self._valid_index_key_pattern = re.compile(r'index2?')
        self._valid_index_value_pattern = re.compile(r'^[ACGTN]*$')

        # Explicitly define the recommended keys as None.
        for key in RECOMMENDED_KEYS:
            setattr(self, key, None)

        for key, value in mappable.items():
            # Convert whitepsace to a single underscore.
            key = self._whitespace_re.sub('_', key)
            self._other_keys.add(key)

            # Promote a ``Read_Structure`` key to ``ReadStructure``.
            value = ReadStructure(value) if key == 'Read_Structure' else value

            # Check to make sure the index is valid if it is supplied.
            if (
                self._valid_index_key_pattern.match(key) and
                not bool(self._valid_index_value_pattern.match(value))
            ):
                raise ValueError(f'Not a valid index: {value}')

            setattr(self, key, value)

        if (
            self.Read_Structure is not None and
            self.Read_Structure.is_single_indexed and
            self.index is None
        ):
            raise ValueError(
                f'If a single-indexed read structure is defined then a '
                f'sample `index` must be defined also: {self}')
        elif (
            self.Read_Structure is not None and
            self.Read_Structure.is_dual_indexed and
            self.index is None and
            self.index2 is None
        ):
            raise ValueError(
                f'If a dual-indexed read structure is defined then '
                f'sample `index` and sample `index2` must be defined '
                f'also: {self}')

    def keys(self):
        """Return all public attributes."""
        return set(RECOMMENDED_KEYS).union(self._other_keys)

    def to_dict(self):
        """Return the key value pairs associated with this ``Sample``"""
        return {key: str(getattr(self, key)) for key in self.keys()}

    def __getattr__(self, attr):
        """Return ``None`` if an attribute is undefined."""
        return self.__dict__.get(attr)

    def __eq__(self, other):
        """Samples are equal if ``Sample_ID``, ``Library_ID``, and ``Lane are
        equal.

        """
        return (
            self.Sample_ID == other.Sample_ID and
            self.Library_ID == other.Library_ID and
            self.Lane == other.Lane)

    def __repr__(self):
        """Shows a simplified constructor command to initialize this object."""
        args = {key: getattr(self, key) for key in RECOMMENDED_KEYS}
        args = args.__repr__().replace('\'', '"')
        return f'{self.__class__.__name__}({args})'

    def __str__(self):
        return str(self.Sample_ID)


class SampleSheetSection(object):
    def __init__(self):
        self.__dict__['keys'] = []
        self.__dict__['_key_map'] = {}

    def add_attr(self, attr, value, name=None):
        """Add an attribute to this class and optionally save an alternate key.

        Parameters
        ----------
        attr : str
            Any valid Python attribute name.
        value : any
            The attribute's value.
        name : str, optional
            An optional key with no restriction on formatting to be used as the
            key any written ``SampleSheet``.

        """
        if re.search(r'\s+', attr):
            raise ValueError('Attributes may not contain whitespace')
        setattr(self, attr, value)
        self._key_map[attr] = name or attr

    def to_dict(self) -> Mapping:
        """Return the key values pairs attached to this section."""
        return {self._key_map[attr]: getattr(self, attr) for attr in self.keys}

    def __getattr__(self, attr):
        """Return ``None`` If an attribute does not exist."""
        return self.__dict__.get(attr)

    def __setattr__(self, attr, value):
        """Save the keys to this object in the order they were assigned."""
        self.keys.append(attr)
        self._key_map[attr] = attr
        self.__dict__[attr] = value

    def __eq__(self, other):
        """Sections are equivalent if their dictionaries are equivalent."""
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return f'{self.__class__.__name__}'


class SampleSheet(object):
    """A representation of an Illumina sample sheet.

    A sample sheet document almost conform to the .ini standards, but does not,
    so a custom parser is needed. Sample sheets are stored in plain text with
    comma-seperated values and string quoting around any field which contains a
    comma. The sample sheet is composed of four sections, marked by a header.

        [Header]   : .ini convention
        [<Other>]  : .ini convention (optional, multiple, user-defined)
        [Settings] : .ini convention
        [Reads]    : .ini convention as a vertical array of items
        [Data]     : table with header

    Parameters
    ----------
    path : str or pathlib.Path, optional
        Any path supported by ``pathlib.Path`` and ``smart_open``.

    """
    _encoding = 'utf8'
    _section_header_re = re.compile(r'\[(.*)\]')
    _whitespace_re = re.compile(r'\s+')

    def __init__(self, path: Union[None, str, Path]=None):
        self.path = path

        self._samples = []
        self._sections = []

        self.Reads = []
        self.Read_Structure = None
        self.samples_have_index = None
        self.samples_have_index2 = None

        self.Header = SampleSheetSection()
        self.Settings = SampleSheetSection()

        if self.path:
            self._parse(str(self.path))

    @staticmethod
    def _make_csv_reader(path: Union[str, Path]) -> csv.reader:
        """Return a ``csv.reader`` for a filepath.

        This helper method is required since ``smart_open.smart_open`` cannot
        decode to "utf8" on-the-fly specifically for HTTPS. Instead, the path
        is opened, read, decoded, and then wrapped in a new handle for
        ``csv.reader``.

        Parameters
        ----------
        path : str or pathlib.Path
            Any path supported by ``pathlib.Path`` and ``smart_open``.

        Returns
        -------
        reader : csv.reader
            A configured ``csv.reader`` for iterating through the sample sheet.

        Notes
        -----
        A workaround will exist as long as this issue remains unsolved:

            https://github.com/RaRe-Technologies/smart_open/issues/146

        """
        string = smart_open(str(path)).read().decode(SampleSheet._encoding)
        handle = io.StringIO(string, newline='')
        reader = csv.reader(handle, skipinitialspace=True)
        return reader

    def add_section(self, section_name):
        """Add a section to the ``SampleSheet``."""
        section_name = self._whitespace_re.sub('_', section_name)
        self._sections.append(section_name)
        setattr(self, section_name, SampleSheetSection())

    @property
    def all_sample_keys(self) -> set:
        """Return the unique keys of all samples in this ``SampleSheet``."""
        return set(chain.from_iterable([sample.keys() for sample in self]))

    @property
    def experimental_design(self):
        """Return a markdown summary of the samples on this sample sheet.

        This property supports displaying rendered markdown only when running
        within an IPython interpreter. If we are not running in an IPython
        interpreter, then print out a nicely formatted ASCII table.

        Returns
        -------
        markdown : str, IPython.core.display.Markdown
            A visual table of IDs and names for all samples in Markdown.

        """
        if not self.samples:
            raise ValueError('No samples in sample sheet')

        markdown = tabulate(
            [[getattr(s, h, '') for h in DESIGN_HEADER] for s in self.samples],
            headers=DESIGN_HEADER,
            tablefmt='pipe')

        if is_ipython_interpreter():  # pragma:  no cover
            from IPython.display import Markdown
            return Markdown(markdown)
        else:
            return markdown

    @property
    def is_paired_end(self) -> Union[None, bool]:
        """Return if the samples are paired-end."""
        return None if not self.Reads else len(self.Reads) == 2

    @property
    def is_single_end(self) -> Union[None, bool]:
        """Return if the samples are single-end."""
        return None if not self.Reads else len(self.Reads) == 1

    @property
    def samples(self):
        """Return the samples present in this ``SampleSheet``."""
        return self._samples

    def _parse(self, path: Union[str, Path]):
        section_name = None
        sample_header = None

        for i, line in enumerate(self._make_csv_reader(path)):
            # Skip to next line if this line is empty to support formats of
            # sample sheets with multiple newlines as section seperators.
            #
            #   https://github.com/clintval/sample-sheet/issues/46
            #
            if not ''.join(line).strip():
                continue

            # Raise exception if we encounter invalid characters.
            if (
                any(character not in VALID_ASCII
                    for character in set(''.join(line)))
            ):
                raise ValueError(
                    f'Sample sheet contains invalid characters on line '
                    f'{i + 1}: {"".join(line)}')

            header_match = self._section_header_re.match(line[0])

            # If we enter a section save it's name and continue to next line.
            if header_match:
                section_name, *_ = header_match.groups()
                if not hasattr(self, section_name) and section_name != 'Data':
                    self.add_section(section_name)
                continue

            # [Reads] - vertical list of integers.
            if section_name == 'Reads':
                self.Reads.append(int(line[0]))
                continue

            # [Data] - delimited data with the first line a header.
            elif section_name == 'Data':
                if sample_header is not None:
                    self.add_sample(Sample(dict(zip(sample_header, line))))
                elif any(key == '' for key in line):
                    raise ValueError(
                        f'Header for [Data] section is not allowed to '
                        f'have empty fields: {line}')
                else:
                    sample_header = line
                continue

            # [<Other>] - keys in first column and values in second column.
            else:
                original_key, value, *_ = line
                getattr(self, section_name).add_attr(
                    attr=self._whitespace_re.sub('_', original_key),
                    value=value,
                    name=original_key)
                continue

    def add_sample(self, sample: Sample):
        """Add a ``Sample`` to this ``SampleSheet``.

        All samples are validated against the first sample added to the sample
        sheet to ensure there are no ID collisions or incompatible read
        structures (if supplied). All samples are also validated against the
        [Reads] section of the sample sheet if it has been defined.

        The following validation is performed when adding a sample:

            - ``Read_Structure`` is identical in all samples, if supplied
            - ``Read_Structure`` is comptaible with [Reads], if supplied
            - Samples on the same ``Lane`` cannot have the same ``Sample_ID``
                  and ``Library_ID``.
            - Samples cannot have the same ``Sample_ID`` if no ``Lane`` has
                  been defined.
            - The same ``index`` or ``index2`` combination cannot exist per
                  flowcell or per lane if lanes have been defined.
            - All samples have the same index design (index, index2) per
                  flowcell or per lane if lanes have been defined.

        Parameters
        ----------
        sample : Sample
            ``Sample`` to add to this sample sheet.

        """
        # Set whether the samples will have ``index`` or ``index2``.
        if len(self.samples) == 0:
            self.samples_have_index = sample.index is not None
            self.samples_have_index2 = sample.index2 is not None

        if (
            len(self.samples) == 0 and
            sample.Read_Structure is not None and
            self.Read_Structure is None
        ):
            # If this is the first sample added to the sample sheet then
            # assume the ``SampleSheet.Read_Structure`` inherits the
            # ``sample.Read_Structure`` only if ``SampleSheet.Read_Structure``
            # has not already been defined. If ``SampleSheet.reads`` has been
            # defined then validate the new read_structure against it.
            if (
                self.is_paired_end and not sample.Read_Structure.is_paired_end or  # noqa
                self.is_single_end and not sample.Read_Structure.is_single_end
            ):
                raise ValueError(
                    f'Sample sheet pairing has been set with '
                    f'Reads:"{self.Reads}" and is not compatible with sample '
                    f'read structure: {sample.Read_Structure}')

            # Make a copy of this samples read_structure for the sample sheet.
            self.Read_Structure = sample.Read_Structure.copy()

        # Validate this sample against the ``SampleSheet.Read_Structure``
        # attribute, which can be None, to ensure they are the same.
        if self.Read_Structure != sample.Read_Structure:
            raise ValueError(
                f'Sample read structure ({sample.Read_Structure}) different '
                f'than read structure in samplesheet ({self.Read_Structure}).')

        # Compare this sample against all those already defined to ensure none
        # have equal ``Sample_ID``, ``Library_ID``, and ``Lane`` attributes.
        # Ensure that all samples have attributes ``index``, ``index2``, or
        # both if they have been defined.
        for other in self.samples:
            if sample == other:
                raise ValueError(
                    f'Cannot add two samples with the same '
                    f'`Sample_ID`, `Library_ID`, and `Lane`: '
                    f'sample - {sample}, other - {other}')
            if sample.index is None and self.samples_have_index:
                raise ValueError(
                    f'Cannot add a sample without attribute `index` if a '
                    f'previous sample has `index` set: {sample})')
            if sample.index2 is None and self.samples_have_index2:
                raise ValueError(
                    f'Cannot add a sample without attribute `index2` if a '
                    f'previous sample has `index2` set: {sample})')

            # Prevent index collisions when samples are dual-indexed
            if (
                self.samples_have_index and self.samples_have_index2 and
                sample.index == other.index and
                sample.index2 == other.index2 and
                sample.Lane == other.Lane
            ):
                raise ValueError(
                    f'Sample index combination for {sample} has already been '
                    f'added on this lane or flowcell: {other}')

            # Prevent index collisions when samples are single-indexed (index)
            if (
                self.samples_have_index and not self.samples_have_index2 and
                sample.index == other.index and
                sample.Lane == other.Lane
            ):
                raise ValueError(
                    f'First sample index for {sample} has already been '
                    f'added on this lane or flowcell: {other}')

            # Prevent index collisions when samples are single-indexed (index2)
            if (
                not self.samples_have_index and self.samples_have_index2 and
                sample.index2 == other.index2 and
                sample.Lane == other.Lane
            ):
                raise ValueError(
                    f'Second sample index for {sample} has already been '
                    f'added on this lane or flowcell: {other}')

        sample.sample_sheet = self
        self._samples.append(sample)

    def add_samples(self, samples: List[Sample]):
        """Add samples in an iterable to this ``SampleSheet``."""
        for sample in samples:
            self.add_sample(sample)

    def to_json(self, **kwargs) -> str:
        """Write this ``SampleSheet`` to JSON.

        Return
        ------
        content : str
            The JSON dump of all entries in this sample sheet.

        """
        content = {
            'Header': self.Header.to_dict(),
            'Reads': self.Reads,
            'Settings': self.Settings.to_dict(),
            'Data': [sample.to_dict() for sample in self.samples],
            **{title: getattr(self, title).to_dict() for
               title in self._sections}
        }
        return json.dumps(content, **kwargs)

    def to_picard_basecalling_params(
        self,
        directory: Union[str, Path],
        bam_prefix: Union[str, Path],
        lanes: Union[int, List[int]]
    ):
        """Writes sample and library information to a set of files for a given
        set of lanes.

        BARCODE PARAMETERS FILES: Store information regarding the sample index
        sequences, sample index names, and, optionally, the library name. These
        files are used by Picard's `CollectIlluminaBasecallingMetrics` and
        Picard's `ExtractIlluminaBarcodes`. The output tab-seperated files are
        formatted as:

            <directory>/barcode_params.<lane>.txt

        LIBRARY PARAMETERS FILES: Store information regarding the sample index
        sequences, sample index names, and optionally sample library and
        descriptions. A path to the resulting demultiplexed BAM file is also
        stored which is used by Picard's `IlluminaBasecallsToSam`. The output
        tab-seperated files are formatted as:

            <directory>/library_params.<lane>.txt

        The format of the BAM file output paths in the library parameter files
        are formatted as:

            <bam_prefix>/<Sample_Name>.<Sample_Library>/
                <Sample_Name>.<index><index2>.<lane>.bam

        Two files will be written to `directory` for all `lanes` specified. If
        the path to `directory` does not exist, it will be created.

        Parameters
        ----------
        directory : str or pathlib.Path
            File path to the directory to write the parameter files.
        bam_prefix: str or pathlib.Path
            Where the demultiplexed BAMs should be written.
        lanes : int, or iterable of int
            The lanes to write basecalling parameters for.

        """
        if len(self.samples) == 0:
            raise ValueError('No samples in sample sheet')
        if not (
            isinstance(lanes, int) or
            isinstance(lanes, (list, tuple)) and
            len(lanes) > 0 and
            all(isinstance(lane, int) for lane in lanes)
        ):
            raise ValueError(f'Lanes must be an int or list of ints: {lanes}')
        if len(set(len(sample.index or '') for sample in self.samples)) != 1:
            raise ValueError('I7 indexes have differing lengths.')
        if len(set(len(sample.index2 or '') for sample in self.samples)) != 1:
            raise ValueError('I5 indexes have differing lengths.')
        for attr in ('Sample_Name', 'Library_ID', 'index'):
            if any(getattr(sample, attr) is None for sample in self.samples):
                raise ValueError(
                    'Samples must have at least `Sample_Name`, '
                    '`Sample_Library`, and `index` attributes')

        # Make lanes iterable if only an int was provided.
        lanes = [lanes] if isinstance(lanes, int) else lanes

        # Resolve path to basecalling parameter files.
        prefix = Path(directory).expanduser().resolve()
        prefix.mkdir(exist_ok=True, parents=True)

        # Promote bam_prefix to Path object.
        bam_prefix = Path(bam_prefix).expanduser().resolve()

        # Both headers are one column larger if an ``index2`` attribute is
        # present on all samples. Use list splatting to unpack the options.
        barcode_header = [
            *(['barcode_sequence_1'] if not self.samples_have_index2 else
              ['barcode_sequence_1', 'barcode_sequence_2']),
            'barcode_name',
            'library_name']
        # TODO: Remove description if none is provided on all samples.
        library_header = [
            *(['BARCODE_1'] if not self.samples_have_index2 else
              ['BARCODE_1', 'BARCODE_2']),
            'OUTPUT',
            'SAMPLE_ALIAS',
            'LIBRARY_NAME',
            'DS']

        for lane in lanes:
            barcode_out = prefix / f'barcode_params.{lane}.txt'
            library_out = prefix / f'library_params.{lane}.txt'

            # Enter into a writing context for both library and barcode params.
            with ExitStack() as stack:
                barcode_writer = csv.writer(
                    stack.enter_context(barcode_out.open('w')), delimiter='\t')
                library_writer = csv.writer(
                    stack.enter_context(library_out.open('w')), delimiter='\t')

                barcode_writer.writerow(barcode_header)
                library_writer.writerow(library_header)

                for sample in self.samples:
                    # The long name of a sample is a combination of the sample
                    # ID and the sample library.
                    long_name = '.'.join([
                        sample.Sample_Name,
                        sample.Library_ID])

                    # The barcode name is all sample indexes concatenated.
                    barcode_name = sample.index + (sample.index2 or '')
                    library_name = sample.Library_ID or ''

                    # Assemble the path to the future BAM file.
                    bam_file = (
                        bam_prefix / long_name /
                        f'{sample.Sample_Name}.{barcode_name}.{lane}.bam')

                    # Use list splatting to build the contents of the library
                    # and barcodes parameter files.
                    barcode_line = [
                        *([sample.index] if not self.samples_have_index2 else
                          [sample.index, sample.index2]),
                        barcode_name,
                        library_name]

                    library_line = [
                        *([sample.index] if not self.samples_have_index2 else
                          [sample.index, sample.index2]),
                        bam_file,
                        sample.Sample_Name,
                        sample.Library_ID,
                        sample.Description or '']

                    barcode_writer.writerow(map(str, barcode_line))
                    library_writer.writerow(map(str, library_line))

                # Dempultiplexing relys on an umatched file so append that,
                # but only to the library parameters file.
                unmatched_file = bam_prefix / f'unmatched.{lane}.bam'
                library_line = [
                    *(['N'] if not self.samples_have_index2 else
                      ['N', 'N']),
                    unmatched_file,
                    'unmatched',
                    'unmatchedunmatched',
                    '']
                library_writer.writerow(map(str, library_line))

    def write(self, handle: TextIO, blank_lines: int=1):
        """Write this ``SampleSheet`` to a file-like object.

        Parameters
        ----------
        handle : file-like object
            Object to wrap by csv.writer.
        blank_lines : int
            Number of blank lines to write between sections.

        """
        writer = csv.writer(handle)
        csv_width = max(len(RECOMMENDED_KEYS), len(self.all_sample_keys))
        section_order = ['Header', 'Reads'] + self._sections + ['Settings']

        if not isinstance(blank_lines, int) or blank_lines <= 0:
            raise ValueError('Number of blank lines must be a positive int.')

        def pad_iterable(iterable, size=csv_width, padding=''):
            return list(islice(chain(iterable, repeat(padding)), size))

        def write_blank_lines(writer, n=blank_lines, width=csv_width):
            for i in range(n):
                writer.writerow(pad_iterable([], width))

        for title in section_order:
            writer.writerow(pad_iterable([f'[{title}]'], csv_width))
            section = getattr(self, title)
            if title == 'Reads':
                for read in self.Reads:
                    writer.writerow(pad_iterable([read], csv_width))
            else:
                for key, value in section.to_dict().items():
                    writer.writerow(pad_iterable([key, value], csv_width))
            write_blank_lines(writer)

        writer.writerow(pad_iterable(['[Data]'], csv_width))
        other_keys = self.all_sample_keys - set(RECOMMENDED_KEYS)
        samples_header = RECOMMENDED_KEYS + sorted(other_keys)
        writer.writerow(pad_iterable(samples_header, csv_width))

        for sample in self.samples:
            line = [getattr(sample, key) for key in samples_header]
            writer.writerow(pad_iterable(line, csv_width))

    def __len__(self):
        """Return the number of samples on this ``SampleSheet``."""
        return len(self.samples)

    def __iter__(self):
        """Iterating over a ``SampleSheet`` will emit its samples."""
        yield from self.samples

    def __repr__(self):
        """Show the constructor command to initialize this object."""
        path = f'"{self.path}"' if self.path else 'None'
        return f'{self.__class__.__name__}({path})'

    def __str__(self):
        """Prints a summary representation of this ``SampleSheet``.

        If the ``__str__()`` method is called on a device that identifies as a
        TTY then render a TTY compatible representation. If no TTY is detected
        then return the invocable representation of this instance.

        """
        try:
            isatty = os.isatty(sys.stdout.fileno())
        except OSError:
            isatty = False

        return self._repr_tty_() if isatty else self.__repr__()

    def _repr_tty_(self):
        """Return a summary of this sample sheet in a TTY compatible codec."""
        header_description = ['Sample_ID', 'Description']
        header_samples = [
            'Sample_ID',
            'Sample_Name',
            'Library_ID',
            'index',
            'index2']

        header = SingleTable([], 'Header')
        setting = SingleTable([], 'Settings')
        sample_main = SingleTable([header_samples], 'Identifiers')
        sample_desc = SingleTable([header_description], 'Descriptions')

        # All key:value pairs found in the [Header] section.
        max_header_width = max(MIN_WIDTH, sample_desc.column_max_width(-1))
        for key in self.Header.keys:
            if 'Description' in key:
                value = '\n'.join(wrap(
                    getattr(self.Header, key),
                    max_header_width))
            else:
                value = getattr(self.Header, key)
            header.table_data.append([key, value])

        # All key:value pairs found in the [Settings] and [Reads] sections.
        for key in self.Settings.keys:
            setting.table_data.append((key, getattr(self.Settings, key) or ''))
        setting.table_data.append(('Reads', ', '.join(map(str, self.Reads))))

        # Descriptions are wrapped to the allowable space remaining.
        description_width = max(MIN_WIDTH, sample_desc.column_max_width(-1))
        for sample in self.samples:
            # Add all key:value pairs for this sample
            sample_main.table_data.append(
                [getattr(sample, title) or '' for title in header_samples])
            # Wrap and add the sample descrption
            sample_desc.table_data.append((
                sample.Sample_ID,
                '\n'.join(wrap(sample.Description or '', description_width))))

        # These tables do not have horizontal headers so remove the frame.
        header.inner_heading_row_border = False
        setting.inner_heading_row_border = False

        table = '\n'.join([
            header.table,
            setting.table,
            sample_main.table,
            sample_desc.table])

        return table


def is_ipython_interpreter() -> bool:  # pragma:  no cover
    """Return if we are in an IPython interpreter or not."""
    import __main__ as main
    return hasattr(main, '__IPYTHON__')
