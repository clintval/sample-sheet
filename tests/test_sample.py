import pytest

from nose.tools import assert_dict_equal
from nose.tools import assert_is_instance
from nose.tools import assert_is_none
from nose.tools import assert_list_equal
from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import eq_

from unittest import TestCase

from sample_sheet import *  # Test import of __all__
from sample_sheet import RECOMMENDED_KEYS


class TestSample(TestCase):
    """Unit tests for ``Sample``"""

    def test_blank_init(self):
        """Test initialization with no parameters."""
        for key in RECOMMENDED_KEYS:
            assert_is_none(getattr(Sample(), key))

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None."""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(Sample(), key))

    def test_promotion_of_read_structure(self):
        """Test that a Read_Structure key is promoted to ``ReadStructure``."""
        sample = Sample({'Read_Structure': '10M141T8B', 'index': 'ACGTGCNA'})
        assert_is_instance(sample.Read_Structure, ReadStructure)

    def test_additional_key_is_added(self):
        """Test that an additional key is added to ``keys()`` method."""
        assert_list_equal(
            list(Sample({'Read_Structure': '151T'}).keys()), ['Read_Structure']
        )

    def test_read_structure_with_single_index(self):
        """Test that ``index`` is present with  a single-indexed read
        structure.

        """
        assert_raises(ValueError, Sample, {'Read_Structure': '141T8B'})

    def test_read_structure_with_dual_index(self):
        """Test that ``index`` and ``index2`` are present with dual-indexed
        read structure.

        """
        assert_raises(ValueError, Sample, {'Read_Structure': '141T8B8B141T'})

    def test_valid_index(self):
        """Test "index" and "index2" value validation."""
        eq_(Sample({'index': 'ACGTN'}).index, 'ACGTN')
        eq_(Sample({'index': 'SI-GA-H1'}).index, 'SI-GA-H1')
        assert_raises(ValueError, Sample, {'index': 'ACUGTN'})
        assert_raises(ValueError, Sample, {'index2': 'ACUGTN'})

    def test_equal_to_dict(self):
        """Test that ``Sample`` is dict equivalent"""
        params = {
            'Sample_ID': '1',
            'Sample_Name': '1',
            'Library_ID': '10x',
            'Lane': '1',
            'index': 'ATCTG',
            'Read_Structure': ReadStructure('151T'),
        }
        assert_dict_equal(params, dict(Sample(params)))

    def test_eq(self):
        """Test equality based only on ``Sample_ID`` and ``Library_ID``."""
        fake1 = Sample({'Sample_ID': 1, 'Library_ID': '10x'})
        fake2 = Sample({'Sample_ID': 1})

        assert_not_equal(fake1, fake2)

        fake1 = Sample({'Sample_ID': 1, 'Library_ID': '10x'})
        fake2 = Sample({'Sample_ID': 1, 'Library_ID': '10x'})

        eq_(fake1, fake2)

        fake1 = Sample({'Sample_ID': 1, 'Library_ID': '10x', 'Lane': '1'})
        fake2 = Sample({'Sample_ID': 1, 'Library_ID': '10x', 'Lane': '2'})

        assert_not_equal(fake1, fake2)
        with pytest.raises(NotImplementedError):
            fake1 == 'random-string'

    def test_str(self):
        """Test ``sample.__str__()``"""
        eq_(str(Sample()), '')
        eq_(str(Sample({'Sample_ID': 245})), '245')

    def test_repr(self):
        """Test ``Sample.__repr__()`` after initialization."""
        eq_(
            Sample().__repr__(),
            (
                'Sample({\'Sample_ID\': None, '
                '\'Sample_Name\': None, \'index\': None})'
            ),
        )
