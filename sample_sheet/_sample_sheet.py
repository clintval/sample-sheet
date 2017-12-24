import csv
import io
import os
import re
import sys

from pathlib import Path
from textwrap import wrap

try:
    from smart_open import smart_open as open
except ImportError:
    raise

from tabulate import tabulate
from terminaltables import SingleTable

__all__ = [
    'ReadStructure',
    'Sample',
    'SampleSheet',
    'camel_case_to_snake_case']


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
            raise ValueError('Not a valid structure: {}'.format(structure))
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
        self._valid_index_value_pattern = re.compile('(^[ACGTN]+$)|(^$)')

        # Default attributes for recommended keys are empty strings.
        for key in self._recommended_keys:
            setattr(self, key, None)

        for key, value in mappable.items():
            # Convert whitepsace to a single underscore and lower case keys.
            key = self._whitespace_pattern.sub('_', key.lower())
            self._other_keys.add(key)

            # Promote a read_structure key to ReadStructure.
            value = ReadStructure(value) if key == 'read_structure' else value

            # If we have a sample index field, check to make sure the value
            # matches the required pattern.
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
        args = {k: getattr(self, k) for k in sorted(self._recommended_keys)}
        args = args.__repr__().replace('\'', '"')
        return f'{self.__class__.__name__}({args})'

    def __str__(self):
        return str(self.sample_id)


class SampleSheetSection:
    def __init__(self):
        self.keys = []

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

    A sample sheet document almost conform to the .ini standards but does not,
    so a custom parser is needed. Sample sheets are stored in plain text with
    comma-seperated values and string quoting around any field which contains a
    comma. The sample sheet is composed of four sections, maked by a header.

        [Header]   : .ini convention
        [Settings] : .ini convention
        [Reads]    : .ini convention as a vertical array of items
        [Data]     : table with header


    Notes
    -----
    1. Write better docstrings
    2. Cleanup and test parser
    3. Add tests and test sample sheets
    4. Add support for printing Picard files for libraries and barcodes

    """

    def __init__(self, path=None):
        """Constructs a ``SampleSheet`` from a file object.

        Parameters
        ----------
        path : str or pathlib.Path, optional
            Path to filesystem file or any path supported by ``smart_open``
                if installed.

        """
        self._samples = []

        self.path = path
        self.reads = []
        self.read_structure = None
        self.samples_have_index = False
        self.samples_have_index2 = False

        self.header, self.settings = Header(), Settings()

        if self.path:
            self._parse(self.path)

    @staticmethod
    def _path_to_csv_reader(path):
        """Return a ``csv.reader`` for a filepath.

        This helper method is required since ``smart_open.smart_open`` cannot
        decode to "utf8" on-the-fly. Instead, the path is opened, read,
        decoded, and then wrapped in a new handle for ``csv.reader``.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to filesystem file or any path supported by ``smart_open``
                if installed.

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
        return len(self.reads) == 2

    @property
    def is_single_end(self):
        """Return if the samples are single-end."""
        return len(self.reads) == 1

    @property
    def samples(self):
        """Return the samples present on this ``SampleSheet``."""
        return self._samples

    def _parse(self, path):
        sample_header = None
        header_pattern = re.compile(r'\[(.*)\]')

        for line in self._path_to_csv_reader(path):
            if all(field.strip() == '' for field in line):
                continue   # Skip all blank lines

            section_match = header_pattern.match(line[0])
            if section_match:
                section, *_ = section_match.groups()
                section = section.lower()
                continue

            if section in ('header', 'settings'):
                key, value, *_ = line
                attribute = getattr(self, section)
                attribute.keys.append(key)
                setattr(attribute, camel_case_to_snake_case(key), value)
                continue
            elif section == 'reads':
                read_cycle, *_ = line
                self.reads.append(int(read_cycle))
                continue
            elif section == 'data':
                if sample_header is None:
                    sample_header = line
                    continue

                if len(sample_header) != len(line):
                    raise ValueError(
                        'Sample header and sample are not the same length: '
                        '{}'.format(line))

                self.add_sample(Sample(dict(zip(sample_header, line))))

    def add_sample(self, sample):
        """Validate and add a ``Sample`` to this ``SampleSheet``.

        All samples are checked against the first sample added to ensure they
        all have the sample ``read_structure`` attribute, if supplied. The
        ``SampleSheet`` will inherit the same ``read_structure`` attribute.

        A ValueError is issued if a sample with the sample ``sample_id`` and
        ``sample_library`` are added.

        Parameters
        ----------
        sample : sample_sheet.Sample
            A sample to be added.

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
        # have equal ``sample_id`` or ``library_id`` attributes. Also make sure
        # that all samples have attributes ``index``, ``index2`` or both.
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

        self._samples.append(sample)

    @property
    def experimental_design(self):
        """Return a markdown summary of the samples on this sample sheet.

        This property supports displaying rendered markdown only when running
        within an IPython interpreter. This is achieved by checking the
        existance of the variable ``__IPYTHON__``. If we are not running in an
        IPython interpreter then print out a nicely formatted ASCII table.

        Returns
        -------
        markdown : str or IPython.core.display.Markdown
            Returns a rendered Markdown when not displayed in IPython.

        """
        header = ['sample_id', 'sample_name', 'library_id', 'description']
        table = [(getattr(s, h, '') for h in header) for s in self.samples]
        markdown = tabulate(table, headers=header, tablefmt='pipe')

        try:
            # The presence of this global name indicates we are in an
            # IPython interpreter and are safe to render Markdown.
            __IPYTHON__  # noqa
            from IPython.display import Markdown
            return Markdown(markdown)
        except (ImportError, NameError):
            return markdown

    def to_basecalling_params(self, path_prefix, lanes):
        """Used to generate files needed by picard ExtractIlluminaBarcodes.

        The output files are tab-delimited and have information regarding the
        barcode sequences, barcode names, and, optionally, the library name.
        Barcodes must be unique and all the same length.

        TODO: Validate barcodes are all same length.
        TODO: Refactor and document.
        TODO: Provide tests.

        """
        if not isinstance(lanes, (list, tuple)):
            raise ValueError(f'Lanes must be a list or tuple: {lanes}')
        if self.samples_have_index is None:
            raise ValueError(f'Samples must have at least ``index``')

        header = ['barcode_sequence_1', 'barcode_name', 'library_name']
        if self.samples_have_index2:
            header.insert(1, 'barcode_sequence_2')

        for lane in lanes:
            outfile = Path(path_prefix) / 'barcode_params.{}.txt'.format(lane)

            with open(str(outfile.expanduser().resolve()), 'w') as handle:
                writer = csv.writer(handle, delimiter='\t')
                writer.writerow(header)

                for sample in self.samples:
                    barcode_name = sample.index + (sample.index2 or '')
                    library_name = sample.library_id or ''
                    barcode_sequence_1 = sample.index

                    line = [barcode_sequence_1, barcode_name, library_name]
                    if self.samples_have_index2:
                        barcode_name = sample.index
                        line.insert(1, sample.index2)

                    writer.writerow(line)

    def _write_library_params(self, outdir, bam_out_prefix, lanes=4):
        """
        TODO: Refactor and document.
        TODO: Provide tests.
        TODO: Make public.
        """
        header = ['BARCODE_1', 'OUTPUT', 'SAMPLE_ALIAS', 'LIBRARY_NAME', 'DS']

        if not self.is_single_indexed:
            header.insert(1, 'BARCODE_2')

        for sample in self.samples:
            sub_directory = f'{sample.Sample_Name}.{sample.Library_ID}'
            bam_out = Path(bam_out_prefix) / sub_directory
            os.makedirs(bam_out.expanduser().resolve(), exist_ok=True)

        for lane in range(1, lanes + 1):
            outfile = Path(outdir) / 'library_params.{}.txt'.format(lane)
            with open(outfile.expanduser().resolve(), 'w') as handle:
                writer = csv.writer(handle, delimiter='\t')
                writer.writerow(header)

                for sample in self.samples:
                    filename = (
                        f'{sample.Sample_Name}'
                        f'.{sample.index}{sample.index2 or ""}'
                        f'.{lane}.bam')

                    line = [
                        sample.index,
                        bam_out.expanduser().resolve() / filename,
                        sample.Sample_Name,
                        sample.Library_ID,
                        sample.Description or '']

                    if not self.is_single_indexed:
                        line.insert(1, sample.index2)

                    writer.writerow(line)

                u_out = (
                    Path(bam_out_prefix).expanduser().resolve() /
                    f'unmatched.{lane}.bam')

                line = ['N', str(u_out), 'unmatched', 'unmatchedunmatched', '']

                if not self.is_single_indexed:
                    line.insert(1, 'N')

                writer.writerow(line)

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
        """Prints a summary unicode representation of a ``SampleSheet``.

        If the `__str__()` method is called on a device that identifies as a
        TTY then render a unicode representation. If no TTY is detected then
        return the invocable representation of this instance.

        """
        try:
            isatty = os.isatty(sys.stdout.fileno())
        except OSError:
            isatty = False

        return self.__unicode__() if isatty else self.__repr__()

    def __unicode__(self):
        """
        TODO: Refactor and document.
        TODO: Provide tests.
        """
        SAMPLE_IDENTIFIERS = [
            'sample_id',
            'sample_name',
            'library_id',
            'i7_index_id',
            'index',
            'i5_index_id',
            'index2']

        SAMPLE_DESCRIPTIONS = [
            'sample_id',
            'description']

        """Return summary unicode tables of this sample sheet."""
        header = SingleTable([], 'Header')
        header.inner_heading_row_border = False
        for key in self.header.keys:
            header.table_data.append((key, getattr(self.header, key) or ''))

        setting = SingleTable([], 'Settings')
        setting.inner_heading_row_border = False
        for key in self.settings.keys:
            setting.table_data.append((key, getattr(self.settings, key) or ''))
        setting.table_data.append(('Reads', ', '.join(map(str, self.reads))))

        sample_main = SingleTable([SAMPLE_IDENTIFIERS], 'Identifiers')
        sample_desc = SingleTable([SAMPLE_DESCRIPTIONS], 'Descriptions')
        description_width = sample_desc.column_max_width(-1)

        for sample in self.samples:
            sample_main.table_data.append(
                [getattr(sample, title) or '' for title in SAMPLE_IDENTIFIERS])

            sample_desc.table_data.append((
                sample.Sample_ID or '',
                '\n'.join(wrap(sample.Description or '', description_width))))

        tables = [
            header.table,
            setting.table,
            sample_main.table,
            sample_desc.table]

        return '\n'.join(tables)


def camel_case_to_snake_case(string):
    """Convert a string in camelCase format into snake_case.

    Supports multiple capital letters in a row, numerals, and any amount of
    whitespace.

    Examples
    --------
    >>> ...

    Notes
    -----
        TODO: Document.
        TODO: Provide doc examples.
    """
    grapheme_pattern = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')
    whitespace_pattern = re.compile('\s')
    name = whitespace_pattern.sub('', grapheme_pattern.sub(r'_\1', string))
    return name.lower()
