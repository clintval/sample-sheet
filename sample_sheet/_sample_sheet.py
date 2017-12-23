import csv
import io
import os
import re
import sys

from pathlib import Path
from textwrap import wrap

from smart_open import smart_open
from tabulate import tabulate
from terminaltables import SingleTable

__all__ = [
    'ReadStructure',
    'Sample',
    'SampleSheet']

DEFAULT_SAMPLE_KEYS = [
    'Sample_ID',
    'Sample_Name',
    'Library_ID',
    'Sample_Project',
    'Description',
    'Sample_Name',
    'I7_Index_ID',
    'index',
    'I5_Index_ID',
    'index2']

SUMMARY_HEADER = [
    'Sample_ID',
    'Sample_Name',
    'Library_ID',
    'Sample_Project',
    'Description']

SAMPLE_IDENTIFIERS = [
    'Sample_ID',
    'Sample_Name',
    'Library_ID',
    'I7_Index_ID',
    'index',
    'I5_Index_ID',
    'index2']

SAMPLE_DESCRIPTIONS = [
    'Sample_ID',
    'Description']


class Sample(object):
    def __init__(self):
        self._default_keys = DEFAULT_SAMPLE_KEYS[:]
        self._other_keys = []

        for key in self._default_keys:
            setattr(self, key, None)

    @classmethod
    def from_dict(self, dictionary):
        sample = self()

        for entry in dictionary.items():
            key, value = entry
            key = re.sub('\s', '_', key)

            if key not in sample._default_keys:
                sample._other_keys.append(key)

            setattr(sample, key, value)

        return sample

    @property
    def keys(self):
        return self._default_keys + self._other_keys

    @property
    def is_paired_end(self):
        return self.index is not None and self.index2 is not None

    def __getattr__(self, attr):
        """Return None if an attribute is unspecified"""
        return self.__dict__.get(attr, None)

    def __str__(self):
        return f'{self.__class__.__name__}("{self.Sample_Name or ""}")'

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'Sample_ID="{self.Sample_ID}", '
            f'Library_ID="{self.Library_ID}", '
            f'Paired={self.is_paired_end})')


class ReadStructure(object):
    """ Information regarding the order and number of cycles in a sequence of
    sample template bases, indexes, and unique molecular identifiers (UMI).

    The tokens follow this scheme:

        - T: template base
        - B: sample index
        - M: unique molecular identifer

    Examples
    --------
    >>> rs = ReadStructure("10M141T8B")
    >>> rs.is_paired
    False
    >>> rs.has_umi
    True
    >>> rs.tokens
    ["10M", "141T", "8B"]

    """
    _token_pattern = re.compile('(\d+[BMT])')

    # Token can repeat one or more times along the entire string.
    _valid_pattern = re.compile('^{}+$'.format(_token_pattern.pattern))

    _index_pattern = re.compile('(\d+B)')
    _umi_pattern = re.compile('(\d+M)')
    _template_pattern = re.compile('(\d+T)')

    def __init__(self, structure):
        if not bool(self._valid_pattern.match(structure)):
            raise ValueError('Not a valid structure: {}'.format(structure))
        self.structure = structure

    @property
    def is_dual_indexed(self):
        """Return if this read structure is dual indexed."""
        return len(self._index_pattern.findall(self.structure)) == 2

    @property
    def is_paired(self):
        """Return if this read structure is paired."""
        return len(self._template_pattern.findall(self.structure)) == 2

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

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'structure="{self.structure}")')

    def __str__(self):
        return self.structure


class SampleSheetSection(object):
    def __init__(self):
        self.keys = []

    def __repr__(self):
        return f'{self.__class__.__name__}'


class Header(SampleSheetSection):
    pass


class Settings(SampleSheetSection):
    pass


class SampleSheet():
    def __init__(self, path):
        """SampleSheet body nearly conform to the .ini standards but does not
        so a custom parser is needed. The SampleSheet is broken up into four
        sections each with different formatting.

            Header   - .ini convention
            Settings - .ini convention
            Reads    - .ini convention as a vertical array of items
            Data     - table with header

        Parameters
        ----------
        path : str
            The S3 / HDFS / local filepath or URI of the sample sheet file.

        TODO:
            1. Write better docstrings
            2. Cleanup and test parser
            3. Add tests and test sample sheets
            4. Add support for printing Picard files for libraries and barcodes
            5. Add support for more than one sample index

        """
        self.path = str(path)

        self.header = Header()
        self.settings = Settings()
        self.reads = []
        self._samples = []

        self._parse(self.path)

    def _parse(self, path):
        # Use `smart_open` to read in the entire file into a string, make that
        # string a file handle and wrap in a `csv.reader` instance.
        handle = csv.reader(
            io.StringIO(
                smart_open(path).read().decode('utf-8'),
                newline=''),
            skipinitialspace=True)

        sample_header = None

        for line in handle:

            # If this row matches a section pattern save header and advance.
            section_match = re.match(r'\[(.*)\]', line[0])
            if all(field.strip() == '' for field in line):
                continue
            elif section_match:
                section, *_ = section_match.groups()
                continue

            # [Header] and [Settings] follow .ini convention.
            if section == 'Header':
                key, value, *_ = line
                key = re.sub('\s', '', key)
                self.header.keys.append(key)
                setattr(self.header, key, value)
                continue
            elif section == 'Settings':
                key, value, *_ = line
                key = re.sub('\s', '', key)
                self.settings.keys.append(key)
                setattr(self.settings, key, value)
                continue

            # [Reads] are a vertical list of read lengths.
            elif section == 'Reads':
                read_cycle, *_ = line
                self.reads.append(int(read_cycle))
                continue

            # [Data] are represented as a table with a header
            elif section == 'Data':
                if sample_header is None:
                    sample_header = line
                    continue

                # TODO: Instead of appending samples use `add_sample()`
                sample = Sample().from_dict(dict(zip(sample_header, line)))
                self._samples.append(sample)

    def add_sample(self, mappable):
        # TODO: Add sample validation
        #    - Read structure is same for all
        #    - Has required fields
        #    - Does not have illegal characters
        #    - No duplicate Sample_Name / Sample_Library collisions
        #    - Assert there are samples
        pass

    @property
    def is_paired_end(self):
        return len(self.reads) == 2

    @property
    def is_single_indexed(self):
        return all(sample.index2 is None for sample in self.samples)

    @property
    def experimental_design(self):
        markdown = tabulate(
            [(getattr(sample, title) or '' for title in SUMMARY_HEADER)
             for sample in self.samples],
            headers=SUMMARY_HEADER,
            tablefmt='pipe')

        # If we are running in an IPython interpreter, then the variable
        # `__IPYTHON__` exists in the global namespace and we should render
        # the markdown. If not, return the formatted table as just a str.
        try:
            __IPYTHON__  # noqa
            from IPython.display import Markdown
            return Markdown(markdown)
        except (NameError, ImportError):
            return markdown

    @property
    def samples(self):
        return self._samples

    def write_basecalling_params(self, outdir, lanes=4):
        for lane in range(1, lanes + 1):
            header = ['barcode_sequence_1', 'barcode_name', 'library_name']

            if self.is_single_indexed:
                def params(s):
                    return s.index, s.index, s.Library_ID
            else:
                def params(s):
                    return s.index, s.index2, s.index + s.index2, s.Library_ID
                header.insert(1, 'barcode_sequence_2')

            table = [header, *[params(sample) for sample in self.samples]]

            outfile = Path(outdir) / 'barcode_params.{}.txt'.format(lane)

            with open(outfile.expanduser().resolve(), 'w') as handle:
                writer = csv.writer(handle, delimiter='\t')
                writer.writerows(table)

    def write_library_params(self, outdir, bam_out_prefix, lanes=4):
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

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.path}')"

    def __str__(self):
        """Prints a summary unicode representation of this sample sheet if the
        `__str__()` method is called on a device that identifies as a TTY.
        If no TTY is detected then return the invocable representation of this
        instance.

        """
        try:
            isatty = os.isatty(sys.stdout.fileno())
        except OSError:
            isatty = False

        return self.__unicode__() if isatty else self.__repr__()

    def __unicode__(self):
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
