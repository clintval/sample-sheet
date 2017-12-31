from nose.tools import assert_false
from nose.tools import assert_is_instance
from nose.tools import assert_is_none
from nose.tools import assert_raises
from nose.tools import assert_true
from nose.tools import eq_

from unittest import TestCase

from sample_sheet import *  # Test import of __all__


class TestSampleSheet(TestCase):
    """Unit tests for ``SampleSheet``"""

    def test_blank_init(self):
        """Test init when no path is provided and path is None"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.path)
        assert_is_none(sample_sheet.read_structure)
        assert_is_none(sample_sheet.samples_have_index)
        assert_is_none(sample_sheet.samples_have_index2)

    def test_blank_init_repr(self):
        """Test ``__repr__()`` for path=None returns an exec statement"""
        eq_(SampleSheet().__repr__(), 'SampleSheet(None)')

    def test_is_single_end(self):
        """Test ``single_end`` property of ``SampleSheet``"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.is_single_end)
        sample_sheet.reads = [151]
        assert_true(sample_sheet.is_single_end)

        sample_sheet.reads = [151, 151]
        assert_false(sample_sheet.is_single_end)

    def test_is_paired_end(self):
        """Test ``paired_end`` property of ``SampleSheet``"""
        sample_sheet = SampleSheet()
        assert_is_none(sample_sheet.is_single_end)
        sample_sheet.reads = [151]
        assert_false(sample_sheet.is_paired_end)

        sample_sheet.reads = [151, 151]
        assert_true(sample_sheet.is_paired_end)

    def test_add_sample(self):
        """Test adding a single simple sample to a sample sheet"""
        sample = Sample({'sample_id': 49})
        sample_sheet = SampleSheet()

        eq_(len(sample_sheet.samples), 0)

        sample_sheet.add_sample(sample)

        eq_(len(sample_sheet.samples), 1)
        eq_(sample_sheet.samples[0], sample)

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

    def test_add_sample_same_twice(self):
        """Test ``add_sample()`` when two samples having the same ``sample_id``
        and ``library_id`` are added.

        """
        sample = Sample()
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample)

        assert_raises(ValueError, sample_sheet.add_sample, sample)

        sample1 = Sample({'sample_id': 49, 'library_id': '234T'})
        sample2 = Sample({'sample_id': 49, 'library_id': '234T'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_different_pairing(self):
        """Test ``add_sample()`` when ``reads`` have been specified in the
        sample sheet which indicate if the sample should be paired or not.

        """
        sample = Sample({'sample_id': 23, 'read_structure': '151T'})
        sample_sheet = SampleSheet()
        sample_sheet.reads = [151, 151]
        assert_raises(ValueError, sample_sheet.add_sample, sample)

        sample = Sample({'sample_id': 26, 'read_structure': '151T151T'})
        sample_sheet = SampleSheet()
        sample_sheet.reads = [151]
        assert_raises(ValueError, sample_sheet.add_sample, sample)

    def test_add_sample_different_read_structure(self):
        """Test ``add_sample()`` when two samples having different
        ``read_structure`` attributes are added.

        """
        sample1 = Sample({'sample_id': 49, 'read_structure': '115T'})
        sample2 = Sample({'sample_id': 23, 'read_structure': '112T'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_same_sample_index(self):
        """Test ``add_sample()`` when two samples have the same index."""
        sample1 = Sample({'sample_id': 49, 'index': 'ACGGTN'})
        sample2 = Sample({'sample_id': 23, 'index': 'ACGGTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_same_sample_index_pair(self):
        """Test ``add_sample()`` when two samples have the same index pair."""
        sample1 = Sample({'sample_id': 49, 'index': 'ACG', 'index2': 'TTTN'})
        sample2 = Sample({'sample_id': 23, 'index': 'ACG', 'index2': 'TTTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_missing_index(self):
        """Test ``add_sample()`` to raise an exception when two samples having
        different ``read_structure`` attributes are added.

        """
        sample1 = Sample({'sample_id': 49, 'index': 'ACGTAC'})
        sample2 = Sample({'sample_id': 23})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_add_sample_with_different_index_combination(self):
        """Test ``add_sample()`` to raise an exception when two samples having
        different ``read_structure`` attributes are added.

        """
        sample1 = Sample({'sample_id': 49, 'index2': 'ACGTAC'})
        sample2 = Sample({'sample_id': 23, 'index': 'ACGGTN'})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(sample1)

        assert_raises(ValueError, sample_sheet.add_sample, sample2)

    def test_experiment_design_plain_text(self):
        """Test ``experimental_design()`` plain text output"""
        sample_sheet = SampleSheet()
        assert_raises(ValueError, lambda: sample_sheet.experimental_design)

        sample1 = Sample({
            'sample_id': 493,
            'sample_name': '10x-FA',
            'index': 'ACGGTNT',
            'library_id': 'exp001',
            'description': 'A sentence!'}
        )
        sample2 = Sample({
            'sample_id': 207,
            'sample_name': '10x-FB',
            'index': 'TTGGTCT',
            'library_id': 'exp001',
            'description': 'One more!'}
        )
        sample_sheet.add_sample(sample1)
        sample_sheet.add_sample(sample2)
        design = sample_sheet.experimental_design
        assert_is_instance(design, str)

        table = (
            '|   sample_id | sample_name   | library_id   | description   |\n'
            '|------------:|:--------------|:-------------|:--------------|\n'
            '|         493 | 10x-FA        | exp001       | A sentence!   |\n'
            '|         207 | 10x-FB        | exp001       | One more!     |')

        self.assertMultiLineEqual(design, table)

    def test_iter(self):
        """Test ``__iter__()`` and ``__next__()``"""
        fake1, fake2 = Sample({'sample_id': 1}), Sample({'sample_id': 2})
        sample_sheet = SampleSheet()
        sample_sheet.add_sample(fake1)
        sample_sheet.add_sample(fake2)
        iterator = iter(sample_sheet)
        eq_(next(iterator), fake1)
        eq_(next(iterator), fake2)

    def test_len(self):
        """Test ``__len__()``"""
        fake1, fake2 = Sample({'sample_id': 1}), Sample({'sample_id': 2})
        sample_sheet = SampleSheet()
        eq_(len(sample_sheet), 0)
        sample_sheet.add_sample(fake1)
        eq_(len(sample_sheet), 1)
        sample_sheet.add_sample(fake2)
        eq_(len(sample_sheet), 2)

    def test_str(self):
        """Test ``__str__()``, when not printing to a TTY"""
        infile = './tests/resources/paired-end-single-index.csv'
        eq_(SampleSheet(infile).__str__(), 'SampleSheet("{}")'.format(infile))

    def test_repr(self):
        """Test ``__repr__()``"""
        infile = './tests/resources/paired-end-single-index.csv'
        eq_(SampleSheet(infile).__repr__(), 'SampleSheet("{}")'.format(infile))
