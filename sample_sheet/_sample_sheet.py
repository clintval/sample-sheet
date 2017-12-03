import csv
import io
import os
import re
import sys

from textwrap import wrap

from smart_open import smart_open
from tabulate import tabulate
from terminaltables import SingleTable

__all__ = [
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
        self.path = path

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
