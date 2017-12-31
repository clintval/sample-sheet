import csv
import io
import os
import re
import sys

from contextlib import ExitStack
from pathlib import Path
from textwrap import wrap

from smart_open import smart_open as open
from tabulate import tabulate
from terminaltables import SingleTable

__all__ = [
    'ReadStructure',
    'Sample',
    'SampleSheet',
    'camel_case_to_snake_case']

# The minimum column with of a detected TTY for wrapping text in CLI columns.
MIN_WIDTH = 10


class ReadStructure:
    """ Information regarding the order and number of cycles in a sequence of
    sample template bases, indexes, and unique molecular identifiers (UMI).

    The tokens follow this scheme:

        - T: template base
        - S: skipped base
        - B: sample index
        - M: unique molecular identifer

    Examples
    --------
    >>> rs = ReadStructure("10M141T8B")
    >>> rs.is_paired_end
    False
    >>> rs.has_umi
    True
    >>> rs.tokens
    ["10M", "141T", "8B"]

    """
    _token_pattern = re.compile('(\d+[BMST])')

    # Token can repeat one or more times along the entire string.
    _valid_pattern = re.compile('^{}+$'.format(_token_pattern.pattern))

    _index_pattern = re.compile('(\d+B)')
    _umi_pattern = re.compile('(\d+M)')
    _skip_pattern = re.compile('(\d+S)')
    _template_pattern = re.compile('(\d+T)')

    def __init__(self, structure):
        if not bool(self._valid_pattern.match(structure)):
            raise ValueError('Not a valid structure: "{}"'.format(structure))
        self.structure = structure

    @property
    def is_indexed(self):
        """Return if this read structure has sample indexes."""
        return len(self._index_pattern.findall(self.structure)) > 0

    @property
    def is_single_indexed(self):
        """Return if this read structure is single indexed."""
        return len(self._index_pattern.findall(self.structure)) == 1

    @property
    def is_dual_indexed(self):
        """Return if this read structure is dual indexed."""
        return len(self._index_pattern.findall(self.structure)) == 2

    @property
    def is_single_end(self):
        """Return if this read structure is single-end."""
        return len(self._template_pattern.findall(self.structure)) == 1

    @property
    def is_paired_end(self):
        """Return if this read structure is paired-end"""
        return len(self._template_pattern.findall(self.structure)) == 2

    @property
    def has_indexes(self):
        """Return if this read structure has any index tokens."""
        return len(self._index_pattern.findall(self.structure)) > 0

    @property
    def has_skips(self):
        """Return if this read structure has any skip tokens."""
        return len(self._skip_pattern.findall(self.structure)) > 0

    @property
    def has_umi(self):
        """Return if this read structure has any UMI tokens."""
        return len(self._umi_pattern.findall(self.structure)) > 0

    @property
    def index_cycles(self):
        """The number of cycles dedicated to indexes."""
        tokens = self._index_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def template_cycles(self):
        """The number of cycles dedicated to template."""
        tokens = self._template_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def skip_cycles(self):
        """The number of cycles dedicated to skips."""
        tokens = self._skip_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def umi_cycles(self):
        """The number of cycles dedicated to UMI."""
        tokens = self._umi_pattern.findall(self.structure)
        return sum((int(re.sub(r'\D', '', token)) for token in tokens))

    @property
    def total_cycles(self):
        """The number of total number of cycles in the structure."""
        return sum((int(re.sub(r'\D', '', token)) for token in self.tokens))

    @property
    def tokens(self):
        """Return a list of all tokens in the read structure."""
        return self._token_pattern.findall(self.structure)

    def copy(self):
        """Returns a shallow copy of this read structure."""
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


class Sample:
    """A single sample from a sample sheet.

    This class is built with the keys and values in the [Data] section of the
    sample sheet. Although no keys are explicitly required it is recommended to
    at least use "Sample_ID", "Sample_Name", and "index". All keys will be
    converted to lower case with whitespace replaced by underscores. If a key
    is found matching the case agnostic pattern "read_structure" then the the
    value is promoted to ``ReadStructure``.

    Examples
    --------
    >>> sample = Sample({'Sample_Name': '3T', 'Sample_ID': '87', 'index': 'A'})
    >>> sample
    Sample({"index": "A", "Sample_Name": "3T", "Sample_ID": "87"})
    >>> sample = Sample({'Read Structure': '151T'})
    >>> sample.read_structure
    ReadStructure("151T")

    """

    def __init__(self, mappable={}):
        """Initialize a ``Sample``.

        Parameters
        ----------
        mappable : dict
            The key-value pairs describing this sample.

        """
        self._recommended_keys = {'sample_id', 'sample_name', 'index'}
        self._other_keys = set()

        self._whitespace_pattern = re.compile('\s+')
        self._valid_index_key_pattern = re.compile('index2?')
        self._valid_index_value_pattern = re.compile('^[ACGTN]*$')

        # Default attributes for recommended keys are empty strings.
        for key in self._recommended_keys:
            setattr(self, key, None)

        for key, value in mappable.items():
            # Convert whitepsace to a single underscore and lower case keys.
            key = self._whitespace_pattern.sub('_', key.lower())
            self._other_keys.add(key)

            # Promote a ``read_structure`` key to ``ReadStructure``.
            value = ReadStructure(value) if key == 'read_structure' else value

            # Check to make sure the index is valid if it is supplied.
            if (
                self._valid_index_key_pattern.match(key) and
                not bool(self._valid_index_value_pattern.match(value))
            ):
                raise ValueError('Not a valid index: {}'.format(value))

            setattr(self, key, value)

        if (
            self.read_structure is not None and
            self.read_structure.is_single_indexed and
            self.index is None
        ):
            raise ValueError(
                f'If a single-indexed read structure is defined then a '
                f'sample ``index`` must be defined also: {self}')
        elif (
            self.read_structure is not None and
            self.read_structure.is_dual_indexed and
            self.index is None and
            self.index2 is None
        ):
            raise ValueError(
                f'If a dual-indexed read structure is defined then '
                f'sample ``index`` and sample ``index2`` must be defined '
                f'also: {self}')

    def keys(self):
        """Return all public attributes to this ``Sample``."""
        return self._recommended_keys.union(self._other_keys)

    def __getattr__(self, attr):
        """Return None if an attribute is undefined."""
        return self.__dict__.get(attr, None)

    def __eq__(self, other):
        """Samples are equal if ``sample_id`` and ``library_id`` are equal."""
        return (
            self.sample_id == other.sample_id and
            self.library_id == other.library_id)

    def __repr__(self):
        """Return an executeable representaiton of this Sample."""
        args = {k: getattr(self, k) for k in sorted(self._recommended_keys)}
        args = args.__repr__().replace('\'', '"')
        return f'{self.__class__.__name__}({args})'

    def __str__(self):
        return str(self.sample_id)


class SampleSheetSection:
    def __init__(self):
        self.keys = []
        self._key_map = {}

    def __getattr__(self, attr):
        """Return None if an attribute is undefined."""
        return self.__dict__.get(attr, None)

    def __repr__(self):
        return f'{self.__class__.__name__}'


class Header(SampleSheetSection):
    pass


class Settings(SampleSheetSection):
    pass


class SampleSheet:
    """A representation of an Illumina sample sheet.

    A sample sheet document almost conform to the .ini standards, but does not,
    so a custom parser is needed. Sample sheets are stored in plain text with
    comma-seperated values and string quoting around any field which contains a
    comma. The sample sheet is composed of four sections, marked by a header.

        [Header]   : .ini convention
        [Settings] : .ini convention
        [Reads]    : .ini convention as a vertical array of items
        [Data]     : table with header

    Parameters
    ----------
    path : str or pathlib.Path, optional
        Any path supported by ``pathlib.Path`` and ``smart_open``.

    """

    def __init__(self, path=None):
        self._samples = []

        self.path = path
        self.reads = []

        self.read_structure = None
        self.samples_have_index = None
        self.samples_have_index2 = None

        self.header, self.settings = Header(), Settings()

        if self.path:
            self._parse(self.path)

    @staticmethod
    def _make_csv_reader(path):
        """Return a ``csv.reader`` for a filepath.

        This helper method is required since ``smart_open.smart_open`` cannot
        decode to "utf8" on-the-fly. Instead, the path is opened, read,
        decoded, and then wrapped in a new handle for ``csv.reader``.

        Parameters
        ----------
        path : str or pathlib.Path
            Any path supported by ``pathlib.Path`` and ``smart_open``.

        Returns
        -------
        reader : csv.reader
            A configured ``csv.reader`` for iterating through the sample sheet.

        """
        handle = io.StringIO(open(str(path)).read().decode('utf8'), newline='')
        reader = csv.reader(handle, skipinitialspace=True)
        return reader

    @property
    def is_paired_end(self):
        """Return if the samples are paired-end."""
        if len(self.reads) == 0:
            return None
        return len(self.reads) == 2

    @property
    def is_single_end(self):
        """Return if the samples are single-end."""
        if len(self.reads) == 0:
            return None
        return len(self.reads) == 1

    @property
    def samples(self):
        """Return the samples present on this ``SampleSheet``."""
        return self._samples

    def _parse(self, path):
        section = sample_header = None
        header_pattern = re.compile(r'\[(.*)\]')

        for line in self._make_csv_reader(path):
            if all(field.strip() == '' for field in line):
                continue   # Skip all blank lines

            section_match = header_pattern.match(line[0])
            if section_match:
                section, *_ = section_match.groups()
                section = section.lower()

            elif section in ('header', 'settings'):
                key, value, *_ = line
                formatted_key = camel_case_to_snake_case(key)

                # ``object_attribute`` is either  self.header or self.settings.
                object_attribute = getattr(self, section)
                object_attribute.keys.append(formatted_key)
                object_attribute._key_map[key] = formatted_key
                setattr(object_attribute, formatted_key, value)

            elif section == 'reads':
                read_cycle, *_ = line
                self.reads.append(int(read_cycle))

            elif section == 'data':
                if sample_header is None:
                    sample_header = line
                    continue

                if len(sample_header) != len(line):
                    raise ValueError(
                        'Sample header and sample are not the same length: '
                        '{}'.format(line))

                self.add_sample(Sample(dict(zip(sample_header, line))))
            else:
                pass

    def add_sample(self, sample):
        """Validate and add a ``Sample`` to this ``SampleSheet``.

        All samples are checked against the first sample added to ensure they
        all have the sample ``read_structure`` attribute, if supplied. The
        ``SampleSheet`` will inherit the same ``read_structure`` attribute.

        Samples cannot be added if the following criteria is met:
            - ``sample_id`` and ``sample_library`` combination exists
            - ``index`` and/or ``index2`` combination exists
            - Samplesheet.reads and Sample.read_structure are incompatible
            - Sample does not have ``index`` defined but others do
            - Sample does not have ``index2`` defined but others do
            - If defined, sample ``read_structure`` is different than others

        Parameters
        ----------
        sample : Sample
            Sample to add to this sample sheet.

        """
        if len(self.samples) == 0:
            # Set whether the samples will have ``index ``or ``index2``.
            self.samples_have_index = sample.index is not None
            self.samples_have_index2 = sample.index2 is not None

        if (
            len(self.samples) == 0 and
            sample.read_structure is not None and
            self.read_structure is None
        ):
            # If this is the first sample added to the sample sheet then
            # assume the ``SampleSheet.read_structure`` inherits the
            # ``sample.read_structure`` only if ``SampleSheet.read_structure``
            # has not already been defined. If ``SampleSheet.reads`` has been
            # defined then validate the new read_structure against it.
            if (
                self.is_paired_end and not sample.read_structure.is_paired_end or  # noqa
                self.is_single_end and not sample.read_structure.is_single_end
            ):
                raise ValueError(
                    f'Sample sheet pairing has been set with '
                    f'Reads:"{self.reads}" and is not compatible with sample '
                    f'read structure: {sample.read_structure}')

            # Make a copy of this samples read_structure for the sample sheet.
            self.read_structure = sample.read_structure.copy()

        # Validate this sample against the ``SampleSheet.read_structure``
        # attribute, which can be None, to ensure they are the same.
        if self.read_structure != sample.read_structure:
            raise ValueError(
                f'Sample read structure ({sample.read_structure}) different '
                f'than read structure in samplesheet ({self.read_structure}).')

        # Compare this sample against all those already defined to ensure none
        # have equal ``sample_id`` or ``library_id`` attributes. Ensure that
        # all samples have attributes ``index``, ``index2`` or both. Check to
        # make sure this sample's index combination has not been added before.
        for other in self.samples:
            if sample == other:
                raise ValueError(
                    f'Cannot add two samples with the same ``sample_id`` and '
                    f'``library_id``: sample - {sample}, other - {other}')
            if sample.index is None and self.samples_have_index:
                raise ValueError(
                    f'Cannot add a sample without attribute ``index`` if a '
                    f'previous sample has ``index`` set: {sample})')
            if sample.index2 is None and self.samples_have_index2:
                raise ValueError(
                    f'Cannot add a sample without attribute ``index2`` if a '
                    f'previous sample has ``index2`` set: {sample})')
            if (
                (self.samples_have_index and not self.samples_have_index2 and
                 sample.index == other.index) or
                (self.samples_have_index and self.samples_have_index2 and
                 sample.index == other.index and
                 sample.index2 == sample.index2)
            ):
                raise ValueError(
                    f'Sample index combination for {sample} has already been '
                    f'added: {other}')

        self._samples.append(sample)

    @property
    def experimental_design(self):
        """Return a markdown summary of the samples on this sample sheet.

        This property supports displaying rendered markdown only when running
        within an IPython interpreter. If we are not running in an IPython
        interpreter, then print out a nicely formatted ASCII table.

        Returns
        -------
        markdown : str or IPython.core.display.Markdown
            Returns a rendered Markdown when not displayed in IPython.

        """
        if len(self.samples) == 0:
            raise ValueError('No samples in sample sheet')

        header = ['sample_id', 'sample_name', 'library_id', 'description']
        table = [[getattr(s, h, '') for h in header] for s in self._samples]
        markdown = tabulate(table, headers=header, tablefmt='pipe')
        if is_ipython_interpreter():
            from IPython.display import Markdown
            return Markdown(markdown)
        else:
            return markdown

    def to_picard_basecalling_params(self, directory, bam_prefix, lanes):
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

            <bam_prefix>/<sample_name>.<sample_library>/
                <sample_name>.<index><index2>.<lane>.bam

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
        for attr in ('sample_name', 'library_id', 'index'):
            if any(getattr(sample, attr) is None for sample in self.samples):
                raise ValueError(
                    'Samples must have at least `sample_name`, '
                    '`sample_library`, and `index` attributes')

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
                        sample.sample_name,
                        sample.library_id])

                    # The barcode name is all sample indexes concatenated.
                    barcode_name = sample.index + (sample.index2 or '')
                    library_name = sample.library_id or ''

                    # Assemble the path to the future BAM file.
                    bam_file = (
                        bam_prefix / long_name /
                        f'{sample.sample_name}.{barcode_name}.{lane}.bam')

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
                        sample.sample_name,
                        sample.library_id,
                        sample.description or '']

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

    def __len__(self):
        """Return the number of samples on this ``SampleSheet``."""
        return len(self.samples)

    def __iter__(self):
        """Iterating over a ``SampleSheet`` will emit it's samples."""
        self._iter = iter(self.samples)
        return self._iter

    def __next__(self):
        """If an iterator has been defined, get the next item."""
        return next(self._iter)

    def __repr__(self):
        """Show the constructor command used to initialize this object."""
        path = f'"{self.path}"' if self.path else 'None'
        return f'{self.__class__.__name__}({path})'

    def __str__(self):
        """Prints a summary representation of this sample sheet.

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
        header_description = ['sample_id', 'description']
        header_samples = [
            'sample_id',
            'sample_name',
            'library_id',
            'index',
            'index2']

        header = SingleTable([], 'Header')
        setting = SingleTable([], 'Settings')
        sample_main = SingleTable([header_samples], 'Identifiers')
        sample_desc = SingleTable([header_description], 'Descriptions')

        # All key:value pairs found in the [Header] section.
        max_header_width = max(MIN_WIDTH, sample_desc.column_max_width(-1))
        for key in self.header.keys:
            if 'description' in key:
                value = '\n'.join(wrap(
                    getattr(self.header, key),
                    max_header_width))
            else:
                value = getattr(self.header, key)
            header.table_data.append([key, value])

        # All key:value pairs found in the [Settings] and [Reads] sections.
        for key in self.settings.keys:
            setting.table_data.append((key, getattr(self.settings, key) or ''))
        setting.table_data.append(('reads', ', '.join(map(str, self.reads))))

        # Descriptions are wrapped to the allowable space remaining.
        description_width = max(MIN_WIDTH, sample_desc.column_max_width(-1))
        for sample in self.samples:
            # Add all key:value pairs for this sample
            sample_main.table_data.append(
                [getattr(sample, title) or '' for title in header_samples])
            # Wrap and add the sample descrption
            sample_desc.table_data.append((
                sample.sample_id,
                '\n'.join(wrap(sample.description or '', description_width))))

        # These tables do not have horizontal headers so remove the frame.
        header.inner_heading_row_border = False
        setting.inner_heading_row_border = False

        table = '\n'.join([
            header.table,
            setting.table,
            sample_main.table,
            sample_desc.table])

        return table


def is_ipython_interpreter():
    try:
        # The presence of this global name indicates we are in an
        # IPython interpreter and are safe to render Markdown.
        __IPYTHON__  # noqa
        # Attempt to import the IPython library
        import IPython  # noqa
        return True
    except (ImportError, NameError):
        return False


def camel_case_to_snake_case(string):
    """Convert a string in CamelCase format into snake_case.

    Supports multiple capital letters in a row, numerals, and any amount of
    whitespace.

    """
    grapheme_pattern = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
    whitespace_pattern = re.compile('\s')
    name = whitespace_pattern.sub('', grapheme_pattern.sub(r'_\1', string))
    return name.lower()
