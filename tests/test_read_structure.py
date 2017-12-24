from nose.tools import assert_false
from nose.tools import assert_raises
from nose.tools import assert_true
from nose.tools import eq_

from sample_sheet import *  # Test import of __all__


class TestReadStructure:
    """Unit tests for ``ReadStructure``"""

    def test_regex_validation(self):
        """Test read structure pattern validation on init"""
        assert_raises(ValueError, ReadStructure, '200BAD')
        assert_raises(ValueError, ReadStructure, '141C28B')
        assert_raises(ValueError, ReadStructure, '151T20M8BB')

    def test_single_end_tokens(self):
        """Test the tokens of an unpaired unindexed structure"""
        structure = '151T'
        read_structure = ReadStructure(structure)
        assert_false(read_structure.is_indexed)
        assert_false(read_structure.is_dual_indexed)
        assert_true(read_structure.is_single_end)
        assert_false(read_structure.is_paired_end)
        assert_false(read_structure.has_skips)
        assert_false(read_structure.has_umi)

    def test_single_end_cycles(self):
        """Test the cycles of an unpaired unindexed structure"""
        structure = '151T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.index_cycles, 0)
        eq_(read_structure.template_cycles, 151)
        eq_(read_structure.umi_cycles, 0)
        eq_(read_structure.skip_cycles, 0)
        eq_(read_structure.total_cycles, 151)

    def test_single_end_single_index_umi(self):
        """Test the tokens of a single-end single-indexed umi structure"""
        structure = '10M141T8B'
        read_structure = ReadStructure(structure)
        assert_true(read_structure.is_indexed)
        assert_false(read_structure.is_dual_indexed)
        assert_true(read_structure.is_single_end)
        assert_false(read_structure.is_paired_end)
        assert_false(read_structure.has_skips)
        assert_true(read_structure.has_umi)

    def test_paired_end_dual_index_umi_tokens(self):
        """Test the tokens of a paired-end dual-indexed umi structure"""
        structure = '10M141T8B8B10M141T'
        read_structure = ReadStructure(structure)
        assert_true(read_structure.is_indexed)
        assert_true(read_structure.is_dual_indexed)
        assert_false(read_structure.is_single_end)
        assert_true(read_structure.is_paired_end)
        assert_false(read_structure.has_skips)
        assert_true(read_structure.has_umi)

    def test_paired_end_dual_index_umi_cycles(self):
        """Test the cycles of a paired-end dual-indexed umi structure"""
        structure = '10M141T8B8B10M141T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.index_cycles, 16)
        eq_(read_structure.template_cycles, 282)
        eq_(read_structure.umi_cycles, 20)
        eq_(read_structure.skip_cycles, 0)
        eq_(read_structure.total_cycles, 318)

    def test_paired_end_dual_index_umi_skips_cycles(self):
        """Test the cycles of a paired-end dual-indexed umi skip structure"""
        structure = '8M1S142T8B8B8M1S142T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.index_cycles, 16)
        eq_(read_structure.template_cycles, 284)
        eq_(read_structure.umi_cycles, 16)
        eq_(read_structure.skip_cycles, 2)
        eq_(read_structure.total_cycles, 318)

    def test_all_tokens(self):
        """Test all tokens of a paired-end dual-indexed umi skip structure"""
        structure = '8M1S142T8B8B8M1S142T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.tokens,
            ['8M', '1S', '142T', '8B', '8B', '8M', '1S', '142T'])

    def test_equal(self):
        """Test ``ReadStructure.__eq__()``"""
        structure = '10M141T8B8B10M141T'
        eq_(ReadStructure(structure), ReadStructure(structure))

    def test_repr(self):
        """Test ``ReadStructure.__repr__()`` after initialization"""
        eq_(ReadStructure('51T').__repr__(), 'ReadStructure(structure="51T")')

    def test_str(self):
        """Test ``ReadStructure.__str__()`` after initialization"""
        eq_(str(ReadStructure('51T')), '51T')
