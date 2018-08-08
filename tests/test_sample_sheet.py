from nose.tools import assert_false
from nose.tools import assert_is_instance
from nose.tools import assert_is_none
from nose.tools import assert_list_equal
from nose.tools import assert_raises
from nose.tools import assert_true
from nose.tools import eq_

from io import StringIO
from itertools import groupby
from pathlib import Path
from tempfile import NamedTemporaryFile
from tempfile import TemporaryDirectory
from unittest import TestCase

from sample_sheet import *  # Test import of __all__

RESOURCES = (Path(__file__).absolute().resolve().parent / 'resources')

VT_100_MAPPING = {
    '0x71': '─',
    '0x74': '├',
    '0x75': '┤',
    '0x76': '┴',
    '0x77': '┬',
    '0x78': '│',
    '0x6a': '┘',
    '0x6b': '┐',
    '0x6c': '┌',
    '0x6d': '└',
    '0x6e': '┼',
}


def decode_vt_100(iterable, default_set='(B', alt_set='(0', escape='\x1b'):
    """Decodes a sequence of VT100 characters.
    https://stackoverflow.com/a/48046132/3727678

    """
    for is_escape, group in groupby(iterable, lambda _: _ == escape):
        if is_escape:
            continue

        characters = ''.join(group)

        if characters.startswith(default_set):
            yield characters[len(default_set):]

        elif characters.startswith(alt_set):
            for character in characters[len(alt_set):]:
                yield VT_100_MAPPING[hex(ord(character))]


def string_as_temporary_file(content):
    """Writes content to a temporary file."""
    handle = NamedTemporaryFile(mode='w+', delete=False)
    handle.write(content)
    handle.close()
    return handle.name


class TestSampleSheet(TestCase):
    """Unit tests for ``SampleSheet``"""

    def test_blank_init(self):
        """Test init when no path is provided and path is None"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.path)
        assert_is_none(sample_sheet.Read_Structure)
        assert_is_none(sample_sheet.samples_have_index)
        assert_is_none(sample_sheet.samples_have_index2)

    def test_blank_init_repr(self):
        """Test ``__repr__()`` for path=None returns an exec statement"""
        eq_(SampleSheet().__repr__(), 'SampleSheet(None)')

    def test_is_single_end(self):
        """Test ``single_end`` property of ``SampleSheet``"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.is_single_end)
        sample_sheet.Reads = [151]
        assert_true(sample_sheet.is_single_end)

        sample_sheet.Reads = [151, 151]
        assert_false(sample_sheet.is_single_end)

    def test_is_paired_end(self):
        """Test ``paired_end`` property of ``SampleSheet``"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.is_single_end)
        sample_sheet.Reads = [151]
        assert_false(sample_sheet.is_paired_end)

        sample_sheet.Reads = [151, 151]
        assert_true(sample_sheet.is_paired_end)

    def test_add_sample(self):
        """Test adding a single simple sample to a sample sheet"""
        sample = Sample({'Sample_ID': 49})
        sample_sheet = SampleSheet()

        eq_(len(sample_sheet.samples), 0)

        sample_sheet.add_sample(sample)

        eq_(len(sample_sheet.samples), 1)
        eq_(sample_sheet.samples[0], sample)

    def test_add_samples(self):
        """Test adding multiple simple samples to a sample sheet"""
        sample1 = Sample({'Sample_ID': 49})
        sample2 = Sample({'Sample_ID': 50})

        sample_sheet = SampleSheet()
        sample_sheet.add_samples([sample1, sample2])

        eq_(len(sample_sheet.samples), 2)
        eq_(sample_sheet.samples[0], sample1)

    def test_add_sample_with_index(self):
        """Test that the SampleSheet sets a sample with attribute ``index``"""
        sample = Sample({'index': 'ACGTTNAT'})
        sample_sheet = SampleSheet()

        sample_sheet.add_sample(sample)

        assert_true(sample_sheet.samples_have_index)
        assert_false(sample_sheet.samples_have_index2)

    def test_add_sample_with_index2(self):
        """Test that the SampleSheet sets a sample with attribute ``index2``"""
        sample = Sample({'index2': 'ACGTTNAT'})
        sample_sheet = SampleSheet()

        assert_is_none(sample_sheet.samples_have_index)
        assert_is_none(sample_sheet.samples_have_index2)

        sample_sheet.add_sample(sample)

        assert_false(sample_sheet.samples_have_index)
        assert_true(sample_sheet.samples_have_index2)

    def test_add_samples_with_same_index_different_index2(self):
        """Test that the SampleSheet sets samples if at least one index is
        different

        """
        sample1 = Sample({'Sample_ID': 0, 'index': 'AGGTA', 'index2': 'AGGTA'})
        sample2 = Sample({'Sample_ID': 1, 'index': 'AGGTA', 'index2': 'TTTTT'})
        sample_sheet = SampleSheet()

        sample_sheet.add_sample(sample1)

        assert_is_none(sample_sheet.add_sample(sample2))

    def test_add_sample_same_twice(self):
        """Test ``add_sample()`` when two samples having the same ``Sample_ID``
        and ``Library_ID`` are added.

        """
        sample = Sample()
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample)

        assert_raises(ValueError, sample_sheet.add_sample, sample)

        sample1 = Sample({'Sample_ID': 49, 'Library_ID': '234T'})
        sample2 = Sample({'Sample_ID': 49, 'Library_ID': '234T'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_same_indexes_same_lane(self):
        """Test ``add_sample()`` for same samples on different lanes."""
        sample1 = Sample({'Sample_ID': 12, 'index': 'AGGTA', 'Lane': '1'})
        sample2 = Sample({'Sample_ID': 49, 'index': 'AGGTA', 'Lane': '1'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_same_sample_different_lane(self):
        """Test ``add_sample()`` for same samples on different lanes."""
        sample1 = Sample({'Sample_ID': 49, 'Library_ID': '234T', 'Lane': '1'})
        sample2 = Sample({'Sample_ID': 49, 'Library_ID': '234T', 'Lane': '2'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_is_none(sample_sheet.add_sample(sample2))

    def test_add_sample_different_pairing(self):
        """Test ``add_sample()`` when ``reads`` have been specified in the
        sample sheet which indicate if the sample should be paired or not.

        """
        sample = Sample({'Sample_ID': 23, 'Read_Structure': '151T'})
        sample_sheet = SampleSheet()
        sample_sheet.Reads = [151, 151]
        assert_raises(ValueError, sample_sheet.add_sample, sample)

        sample = Sample({'Sample_ID': 26, 'Read_Structure': '151T151T'})
        sample_sheet = SampleSheet()
        sample_sheet.Reads = [151]
        assert_raises(ValueError, sample_sheet.add_sample, sample)

    def test_add_sample_different_read_structure(self):
        """Test ``add_sample()`` when two samples having different
        ``Read_Structure`` attributes are added.

        """
        sample1 = Sample({'Sample_ID': 49, 'Read_Structure': '115T'})
        sample2 = Sample({'Sample_ID': 23, 'Read_Structure': '112T'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_same_sample_index(self):
        """Test ``add_sample()`` when two samples have the same index."""
        sample1 = Sample({'Sample_ID': 49, 'index': 'ACGGTN'})
        sample2 = Sample({'Sample_ID': 23, 'index': 'ACGGTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_same_sample_index2(self):
        """Test ``add_sample()`` when two samples have the same index."""
        sample1 = Sample({'Sample_ID': 49, 'index2': 'ACGGTN'})
        sample2 = Sample({'Sample_ID': 23, 'index2': 'ACGGTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_same_sample_index_pair(self):
        """Test ``add_sample()`` when two samples have the same index pair."""
        sample1 = Sample({'Sample_ID': 49, 'index': 'ACG', 'index2': 'TTTN'})
        sample2 = Sample({'Sample_ID': 23, 'index': 'ACG', 'index2': 'TTTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_missing_index(self):
        """Test ``add_sample()`` when a sample has a missing index."""
        sample1 = Sample({'Sample_ID': 49, 'index': 'ACGTAC'})
        sample2 = Sample({'Sample_ID': 23})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_different_index_combination(self):
        """Test ``add_sample()`` improper index combinations in samples."""
        sample1 = Sample({'Sample_ID': 49, 'index2': 'ACGTAC'})
        sample2 = Sample({'Sample_ID': 23, 'index': 'ACGGTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_all_sample_keys(self):
        """Test ``all_sample_keys()`` to return set of all sample keys."""
        sample1 = Sample({'Sample_ID': 49, 'Key1': 1})
        sample2 = Sample({'Sample_ID': 23, 'Key2': 2})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)
        sample_sheet.add_sample(sample2)

        eq_(sample_sheet.all_sample_keys,
            {'Sample_ID', 'Sample_Name', 'index', 'Key1', 'Key2'})

    def test_parse_invalid_ascii(self):
        """Test exception with invalid characters"""
        filename = string_as_temporary_file(
            '[Header],\n'
            ',\n'
            '[Settings],\n'
            ',\n'
            '[Reads],\n'
            ',\n'
            '[Data],\n'
            'Sample_ID, Description\n'
            'test2, bad 😃 description\n')

        assert_raises(ValueError, SampleSheet, filename)

    def test_parse_different_length_header(self):
        """Test the need for the same length header as data"""
        filename = string_as_temporary_file(
            '[Header],,\n'
            ',,\n'
            '[Settings],,\n'
            ',,\n'
            '[Reads],,\n'
            ',,\n'
            '[Data],,\n'
            'Sample_ID, Description,\n'
            'test2, Sample Description, New Field\n')

        assert_raises(ValueError, SampleSheet, filename)

    def test_experiment_design_plain_text(self):
        """Test ``experimental_design()`` plain text output"""
        sample_sheet = SampleSheet()
        assert_raises(ValueError, lambda: sample_sheet.experimental_design)

        sample1 = Sample({
            'Sample_ID': 493,
            'Sample_Name': '10x-FA',
            'index': 'ACGGTNT',
            'Library_ID': 'exp001',
            'Description': 'A sentence!'}
        )
        sample2 = Sample({
            'Sample_ID': 207,
            'Sample_Name': '10x-FB',
            'index': 'TTGGTCT',
            'Library_ID': 'exp001',
            'Description': 'One more!'}
        )
        sample_sheet.add_sample(sample1)
        sample_sheet.add_sample(sample2)
        design = sample_sheet.experimental_design
        assert_is_instance(design, str)

        table = (
            '|   Sample_ID | Sample_Name   | Library_ID   | Description   |\n'
            '|------------:|:--------------|:-------------|:--------------|\n'
            '|         493 | 10x-FA        | exp001       | A sentence!   |\n'
            '|         207 | 10x-FB        | exp001       | One more!     |')

        self.assertMultiLineEqual(design, table)

    def test_to_picard_basecalling_params_no_samples(self):
        """Test ``to_picard_basecalling_params()`` without samples."""
        with TemporaryDirectory() as temp_dir:
            sample_sheet = SampleSheet()
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes=1)

    def test_to_picard_basecalling_params_incorrect_lanes_types(self):
        """Test ``to_picard_basecalling_params()`` incorrect lane types."""
        with TemporaryDirectory() as temp_dir:
            sample = Sample({
                'Sample_ID': 49,
                'Sample_Name': '49-tissue',
                'Library_ID': 'exp001',
                'Description': 'Lorum ipsum!',
                'index': 'GAACT',
                'index2': 'AGTTC'})
            sample_sheet = SampleSheet()
            sample_sheet.add_sample(sample)
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes='string')
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes=[0.2, 2])

    def test_to_picard_basecalling_params_insufficient_sample_attrs(self):
        """Test ``to_picard_basecalling_params()`` required sample attrs."""
        with TemporaryDirectory() as temp_dir:
            sample_sheet = SampleSheet()
            sample_sheet.add_sample(Sample({'Sample_ID': 23}))
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes=1)

    def test_to_picard_basecalling_params_different_index_sizes(self):
        """Test ``to_picard_basecalling_params()`` different index sizes."""
        with TemporaryDirectory() as temp_dir:
            sample_sheet = SampleSheet()
            sample1 = Sample({'Sample_ID': 21, 'index': 'ACGT'})
            sample2 = Sample({'Sample_ID': 22, 'index': 'ACG'})
            sample_sheet.add_sample(sample1)
            sample_sheet.add_sample(sample2)
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes=1)

    def test_to_picard_basecalling_params_different_index2_sizes(self):
        """Test ``to_picard_basecalling_params()`` different index2 sizes."""
        with TemporaryDirectory() as temp_dir:
            sample_sheet = SampleSheet()
            sample1 = Sample({'Sample_ID': 21, 'index2': 'ACGT'})
            sample2 = Sample({'Sample_ID': 22, 'index2': 'ACG'})
            sample_sheet.add_sample(sample1)
            sample_sheet.add_sample(sample2)
            assert_raises(
                ValueError,
                sample_sheet.to_picard_basecalling_params,
                temp_dir, temp_dir, lanes=1)

    def test_to_picard_basecalling_params_output_files(self):
        """Test ``to_picard_basecalling_params()`` output files"""
        bam_prefix = '/home/user'
        lanes = [1, 2]
        with TemporaryDirectory() as temp_dir:
            sample1 = Sample({
                'Sample_ID': 49,
                'Sample_Name': '49-tissue',
                'Library_ID': 'exp001',
                'Description': 'Lorum ipsum!',
                'index': 'GAACT',
                'index2': 'AGTTC'})
            sample2 = Sample({
                'Sample_ID': 23,
                'Sample_Name': '23-tissue',
                'Library_ID': 'exp001',
                'Description': 'Test description!',
                'index': 'TGGGT',
                'index2': 'ACCCA'})

            sample_sheet = SampleSheet()
            sample_sheet.add_sample(sample1)
            sample_sheet.add_sample(sample2)
            sample_sheet.to_picard_basecalling_params(
                directory=temp_dir, bam_prefix=bam_prefix, lanes=lanes)

            prefix = Path(temp_dir)
            assert_true((prefix / 'barcode_params.1.txt').exists())
            assert_true((prefix / 'barcode_params.2.txt').exists())
            assert_true((prefix / 'library_params.1.txt').exists())
            assert_true((prefix / 'library_params.2.txt').exists())

            barcode_params = (
                'barcode_sequence_1\tbarcode_sequence_2\tbarcode_name\tlibrary_name\n'  # noqa
                'GAACT\tAGTTC\tGAACTAGTTC\texp001\n'                                    # noqa
                'TGGGT\tACCCA\tTGGGTACCCA\texp001\n')                                   # noqa

            library_params = (
                'BARCODE_1\tBARCODE_2\tOUTPUT\tSAMPLE_ALIAS\tLIBRARY_NAME\tDS\n'                                                     # noqa
                'GAACT\tAGTTC\t/home/user/49-tissue.exp001/49-tissue.GAACTAGTTC.{lane}.bam\t49-tissue\texp001\tLorum ipsum!\n'       # noqa
                'TGGGT\tACCCA\t/home/user/23-tissue.exp001/23-tissue.TGGGTACCCA.{lane}.bam\t23-tissue\texp001\tTest description!\n'  # noqa
                'N\tN\t/home/user/unmatched.{lane}.bam\tunmatched\tunmatchedunmatched\t\n')                                          # noqa

            self.assertMultiLineEqual(
                (prefix / 'barcode_params.1.txt').read_text(), barcode_params)
            self.assertMultiLineEqual(
                (prefix / 'barcode_params.2.txt').read_text(), barcode_params)
            self.assertMultiLineEqual(
                (prefix / 'library_params.1.txt').read_text(),
                library_params.format(lane=1))
            self.assertMultiLineEqual(
                (prefix / 'library_params.2.txt').read_text(),
                library_params.format(lane=2))

    def test_add_section(self):
        """Test ``add_section()`` to add a section and bind key:values to it"""
        sample_sheet = SampleSheet()
        sample_sheet.add_section('Manifests')
        sample_sheet.Manifests.PoolRNA = 'RNAMatrix.txt'
        sample_sheet.Manifests.PoolDNA = 'DNAMatrix.txt'

        assert_list_equal(sample_sheet.Manifests.keys, ['PoolRNA', 'PoolDNA'])
        eq_(sample_sheet.Manifests.PoolRNA, 'RNAMatrix.txt')
        eq_(sample_sheet.Manifests.PoolDNA, 'DNAMatrix.txt')

    def test_to_json(self):
        """Test ``SampleSheet.to_json()`` all output"""
        sample_sheet = SampleSheet()
        sample_sheet.Header.IEM4FileVersion = 4
        sample_sheet.Header.add_attr(
            attr='Investigator_Name',
            value='jdoe',
            name='Investigator Name')
        sample_sheet.Settings.CreateFastqForIndexReads = 1
        sample_sheet.Settings.BarcodeMismatches = 2
        sample_sheet.add_section('Manifests')
        sample_sheet.Manifests.PoolDNA = "DNAMatrix.txt"
        sample_sheet.Reads = [151, 151]
        sample = Sample({
            'Sample_ID': '1823A',
            'Sample_Name': '1823A-tissue',
            'index': 'ACGT'
        })
        sample_sheet.add_sample(sample)
        actual = sample_sheet.to_json(indent=4, sort_keys=True)
        expected = (
            '{\n'
            '    "Data": [\n'
            '        {\n'
            '            "Sample_ID": "1823A",\n'
            '            "Sample_Name": "1823A-tissue",\n'
            '            "index": "ACGT"\n'
            '        }\n'
            '    ],\n'
            '    "Header": {\n'
            '        "IEM4FileVersion": 4,\n'
            '        "Investigator Name": "jdoe"\n'
            '    },\n'
            '    "Manifests": {\n'
            '        "PoolDNA": "DNAMatrix.txt"\n'
            '    },\n'
            '    "Reads": [\n'
            '        151,\n'
            '        151\n'
            '    ],\n'
            '    "Settings": {\n'
            '        "BarcodeMismatches": 2,\n'
            '        "CreateFastqForIndexReads": 1\n'
            '    }\n'
            '}'
        )
        eq_(expected, actual)

    def test_write(self):
        """Test ``write()`` by comparing a roundtrip of a sample sheet"""
        infile = RESOURCES / 'paired-end-single-index.csv'
        sample_sheet = SampleSheet(infile)

        string_handle = StringIO(newline=None)
        sample_sheet.write(string_handle)

        string_handle.seek(0)

        with open(infile, 'r', newline='\n', encoding='utf-8') as handle:
            self.assertMultiLineEqual(string_handle.read(), handle.read())

    def test_no_line_comma_pad_read_and_write_with_padding(self):
        """Test ``SampleSheet()`` for reading non-comma line padded input"""
        infile_pad = RESOURCES / 'paired-end-single-index.csv'
        infile_no_pad = RESOURCES / 'paired-end-single-index-no-pad.csv'
        sample_sheet = SampleSheet(infile_no_pad)

        string_handle = StringIO(newline=None)
        sample_sheet.write(string_handle)

        string_handle.seek(0)

        with open(infile_pad, 'r', newline='\n', encoding='utf-8') as handle:
            self.assertMultiLineEqual(string_handle.read(), handle.read())

    def test_read_with_additional_section(self):
        """"Test ``SampleSheet.read()`` for reading with a Manifests section"""
        infile = RESOURCES / 'paired-end-single-index-with-manifest.csv'
        sample_sheet = SampleSheet(infile)
        assert sample_sheet.Manifests.RNAPool == 'test'

    def test_write_custom_section(self):
        """Test ``write()`` when a custom section is defined"""
        # Create a ``SampleSheet`` with a [Manifests] section
        sample_sheet1 = SampleSheet()
        sample_sheet1.add_section('Manifests')
        sample_sheet1.Manifests.PoolRNA = 'RNAMatrix.txt'

        # Write to string and make temporary file
        string_handle = StringIO(newline=None)
        sample_sheet1.write(string_handle)
        string_handle.seek(0)
        filename = string_as_temporary_file(string_handle.read())

        # Read temporary file and confirm section and it's data exists.
        sample_sheet2 = SampleSheet(filename)
        assert_list_equal(sample_sheet2.Manifests.keys, ['PoolRNA'])
        eq_(sample_sheet2.Manifests.PoolRNA, 'RNAMatrix.txt')

    def test_write_custom_sections(self):
        """Test ``write()`` when multiple custom sections are defined"""
        # Create a ``SampleSheet`` with a [Manifests] section
        sample_sheet1 = SampleSheet()
        sample_sheet1.add_section('Manifests')
        sample_sheet1.Manifests.PoolRNA = 'RNAMatrix.txt'
        sample_sheet1.add_section('TestingSection')
        sample_sheet1.TestingSection.KeyNumber1 = 'DNAMatrix.txt'

        # Write to string and make temporary file
        string_handle = StringIO(newline=None)
        sample_sheet1.write(string_handle)
        string_handle.seek(0)
        filename = string_as_temporary_file(string_handle.read())

        # Read temporary file and confirm section and it's data exists.
        sample_sheet2 = SampleSheet(filename)
        assert_list_equal(sample_sheet2.Manifests.keys, ['PoolRNA'])
        eq_(sample_sheet2.Manifests.PoolRNA, 'RNAMatrix.txt')
        assert_list_equal(sample_sheet2.TestingSection.keys, ['KeyNumber1'])
        eq_(sample_sheet2.TestingSection.KeyNumber1, 'DNAMatrix.txt')

    def test_write_invalid_num_blank_lines(self):
        """Test ``write()`` when given invalid number of blank lines"""
        infile = RESOURCES / 'paired-end-single-index.csv'
        sample_sheet = SampleSheet(infile)

        string_handle = StringIO(newline=None)
        assert_raises(
            ValueError,
            lambda: sample_sheet.write(string_handle, blank_lines=0.4))
        assert_raises(
            ValueError,
            lambda: sample_sheet.write(string_handle, blank_lines=-1))

    def test_iter(self):
        """Test ``__iter__()`` and ``__next__()``"""
        fake1, fake2 = Sample({'Sample_ID': 1}), Sample({'Sample_ID': 2})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(fake1)
        sample_sheet.add_sample(fake2)
        iterator = iter(sample_sheet)
        eq_(next(iterator), fake1)
        eq_(next(iterator), fake2)

    def test_len(self):
        """Test ``__len__()``"""
        fake1, fake2 = Sample({'Sample_ID': 1}), Sample({'Sample_ID': 2})
        sample_sheet = SampleSheet()
        eq_(len(sample_sheet), 0)
        sample_sheet.add_sample(fake1)
        eq_(len(sample_sheet), 1)
        sample_sheet.add_sample(fake2)
        eq_(len(sample_sheet), 2)

    def test_str(self):
        """Test ``__str__()``, when not printing to a TTY"""
        infile = RESOURCES / 'paired-end-single-index.csv'
        eq_(SampleSheet(infile).__str__(), 'SampleSheet("{}")'.format(infile))

    def test_repr(self):
        """Test ``__repr__()``"""
        infile = RESOURCES / 'paired-end-single-index.csv'
        eq_(SampleSheet(infile).__repr__(), 'SampleSheet("{}")'.format(infile))

    def test_repr_tty(self):
        """Test ``_repr_tty_()``"""
        self.maxDiff = 3000
        sample_sheet = SampleSheet(RESOURCES / 'paired-end-single-index.csv')
        source = '\n' + ''.join(decode_vt_100(sample_sheet._repr_tty_()))
        target = (
            '\n┌Header─────────────┬─────────────────────────────────┐'
            '\n│ IEM1_File_Version │ 4                               │'
            '\n│ Investigator_Name │ jdoe                            │'
            '\n│ Experiment_Name   │ exp001                          │'
            '\n│ Date              │ 11/16/2017                      │'
            '\n│ Workflow          │ SureSelectXT                    │'
            '\n│ Application       │ NextSeq FASTQ Only              │'
            '\n│ Assay             │ SureSelectXT                    │'
            '\n│ Description       │ A description of this flow cell │'
            '\n│ Chemistry         │ Default                         │'
            '\n└───────────────────┴─────────────────────────────────┘'
            '\n┌Settings──────────────────────┬──────────┐'
            '\n│ create_fastq_for_index_reads │ 1        │'
            '\n│ barcode_mismatches           │ 2        │'
            '\n│ reads                        │ 151, 151 │'
            '\n└──────────────────────────────┴──────────┘'
            '\n┌Identifiers┬──────────────┬────────────┬──────────┬────────┐'
            '\n│ Sample_ID │ Sample_Name  │ Library_ID │ index    │ index2 │'
            '\n├───────────┼──────────────┼────────────┼──────────┼────────┤'
            '\n│ 1823A     │ 1823A-tissue │ 2017-01-20 │ GAATCTGA │        │'
            '\n│ 1823B     │ 1823B-tissue │ 2017-01-20 │ AGCAGGAA │        │'
            '\n│ 1824A     │ 1824A-tissue │ 2017-01-20 │ GAGCTGAA │        │'
            '\n│ 1825A     │ 1825A-tissue │ 2017-01-20 │ AAACATCG │        │'
            '\n│ 1826A     │ 1826A-tissue │ 2017-01-20 │ GAGTTAGC │        │'
            '\n│ 1826B     │ 1823A-tissue │ 2017-01-17 │ CGAACTTA │        │'
            '\n│ 1829A     │ 1823B-tissue │ 2017-01-17 │ GATAGACA │        │'
            '\n└───────────┴──────────────┴────────────┴──────────┴────────┘'
            '\n┌Descriptions──────────────────┐'
            '\n│ Sample_ID │ Description      │'
            '\n├───────────┼──────────────────┤'
            '\n│ 1823A     │ 0.5x treatment   │'
            '\n│ 1823B     │ 0.5x treatment   │'
            '\n│ 1824A     │ 1.0x treatment   │'
            '\n│ 1825A     │ 10.0x treatment  │'
            '\n│ 1826A     │ 100.0x treatment │'
            '\n│ 1826B     │ 0.5x treatment   │'
            '\n│ 1829A     │ 0.5x treatment   │'
            '\n└───────────┴──────────────────┘')

        # self.assertMultiLineEqual(source, target)
