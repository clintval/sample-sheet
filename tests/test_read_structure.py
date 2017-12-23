#from unittest import TestCase

from nose.tools import eq_, assert_raises, assert_false, assert_true

from sample_sheet import *  # Test import of __all__


class TestReadStructure:
    """Unit tests for ``ReadStructure``"""

    def test_regex_validation(self):
        """Tests read structure pattern validation on init"""
        assert_raises(ValueError, ReadStructure, '200BAD')
        assert_raises(ValueError, ReadStructure, '141C28B')
        assert_raises(ValueError, ReadStructure, '151T20M8BB')

    def test_single_end_tokens(self):
        """Tests the tokens of an unpaired unindexed structure"""
        structure = '151T'
        read_structure = ReadStructure(structure)
        assert_false(read_structure.is_dual_indexed)
        assert_false(read_structure.is_paired)
        assert_false(read_structure.has_umi)

    def test_single_end_cycles(self):
        """Tests the cycles of an unpaired unindexed structure"""
        structure = '151T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.index_cycles, 0)
        eq_(read_structure.template_cycles, 151)
        eq_(read_structure.umi_cycles, 0)
        eq_(read_structure.total_cycles, 151)

    def test_single_end_single_index_umi(self):
        """Tests the tokens of a single-end single-indexed umi structure"""
        structure = '10M141T8B'
        read_structure = ReadStructure(structure)
        assert_false(read_structure.is_dual_indexed)
        assert_false(read_structure.is_paired)
        assert_true(read_structure.has_umi)

    def test_paired_end_dual_index_umi_tokens(self):
        """Tests the tokens of a paired-end dual-indexed umi structure"""
        structure = '10M141T8B8B10M141T'
        read_structure = ReadStructure(structure)
        assert_true(read_structure.is_dual_indexed)
        assert_true(read_structure.is_paired)
        assert_true(read_structure.has_umi)

    def test_paired_end_dual_index_umi_cycles(self):
        """Tests the cycles of a paired-end dual-indexed umi structure"""
        structure = '10M141T8B8B10M141T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.index_cycles, 16)
        eq_(read_structure.template_cycles, 282)
        eq_(read_structure.umi_cycles, 20)
        eq_(read_structure.total_cycles, 318)

    def test_all_tokens(self):
        """Tests all tokens of a paired-end dual-indexed umi structure"""
        structure = '10M141T8B8B10M141T'
        read_structure = ReadStructure(structure)
        eq_(read_structure.tokens, ['10M', '141T', '8B', '8B', '10M', '141T'])

    def test_repr(self):
        """Tests ``ReadStructure.__repr__()`` after initialization"""
        eq_(ReadStructure('51T').__repr__(), 'ReadStructure(structure="51T")')
