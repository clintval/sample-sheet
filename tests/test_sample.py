from nose.tools import assert_is_instance
from nose.tools import assert_is_none
from nose.tools import assert_not_equal
from nose.tools import assert_raises
from nose.tools import assert_set_equal
from nose.tools import eq_

from sample_sheet import *  # Test import of __all__


class TestSample:
    """Unit tests for ``Sample``"""

    def test_blank_init(self):
        """Test initialization with no parameters."""
        for key in Sample()._recommended_keys:
            assert_is_none(getattr(Sample(), key))

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None."""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(Sample(), key))

    def test_keys_on_blank_init(self):
        """Test that recommended keys exist on blank initialization."""
        sample = Sample()
        assert_set_equal(sample.keys(), sample._recommended_keys)

    def test_add_key_value(self):
        """Test that new keys are lowercase and \s are now underscores."""
        sample = Sample({'Sample ID': '2314'})
        eq_(sample.sample_id, '2314')

    def test_promotion_of_read_structure(self):
        """Test that a read_structure key is promoted to ``ReadStructure``."""
        sample = Sample({
            'read_structure': '10M141T8B',
            'index': 'ACGTGCNA'
        })
        assert_is_instance(sample.read_structure, ReadStructure)

    def test_additional_key_is_added(self):
        """Test that an additional key is added to ``keys()`` method."""
        assert_set_equal(
            Sample({'Read Structure': '151T'}).keys(),
            {'index', 'read_structure', 'sample_id', 'sample_name'})

    def test_read_structure_with_single_index(self):
        """Test that ``index`` is present with  asingle-indexed read
        structure.

        """
        assert_raises(ValueError, Sample, {'read_structure': '141T8B'})

    def test_read_structure_with_dual_index(self):
        """Test that ``index`` and ``index2`` are present with dual-indexed
        read structure.

        """
        assert_raises(ValueError, Sample, {'read_structure': '141T8B8B141T'})

    def test_valid_index(self):
        """Test "index" and "index2" value validation."""
        eq_(Sample({'index': 'ACGTN'}).index, 'ACGTN')
        assert_raises(ValueError, Sample, {'index': 'ACUGTN'})
        assert_raises(ValueError, Sample, {'index2': 'ACUGTN'})

    def test_eq(self):
        """Test equality  based only on ``sample_id`` and ``library_id``."""
        fake1 = Sample({'sample_id': 1, 'library_id': '10x'})
        fake2 = Sample({'sample_id': 1})

        assert_not_equal(fake1, fake2)

        fake1 = Sample({'sample_id': 1, 'library_id': '10x'})
        fake2 = Sample({'sample_id': 1, 'library_id': '10x'})
        eq_(fake1, fake2)

    def test_str(self):
        """Test ``sample.__str__()``"""
        eq_(str(Sample()), 'None')
        eq_(str(Sample({'sample_id': 245})), '245')

    def test_repr(self):
        """Test ``Sample.__repr__()`` after initialization."""
        eq_(Sample().__repr__(),
            'Sample({"index": None, "sample_id": None, "sample_name": None})')
