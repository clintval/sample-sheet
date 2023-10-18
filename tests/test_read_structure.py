from pytest import raises

from sample_sheet import ReadStructure


class TestReadStructure(object):
    """Unit tests for ``ReadStructure``"""

    def test_regex_validation(self):
        """Test read structure pattern validation on init"""
        with raises(ValueError):
            ReadStructure("200BAD")
        with raises(ValueError):
            ReadStructure("141C28B")
        with raises(ValueError):
            ReadStructure("151T20M8BB")

    def test_single_end_tokens(self):
        """Test the tokens of an unpaired unindexed structure"""
        structure = "151T"
        read_structure = ReadStructure(structure)
        assert read_structure.is_indexed is False
        assert read_structure.is_dual_indexed is False
        assert read_structure.is_single_end is True
        assert read_structure.is_paired_end is False
        assert read_structure.has_indexes is False
        assert read_structure.has_skips is False
        assert read_structure.has_umi is False

    def test_single_end_cycles(self):
        """Test the cycles of an unpaired unindexed structure"""
        structure = "151T"
        read_structure = ReadStructure(structure)
        assert read_structure.index_cycles == 0
        assert read_structure.template_cycles == 151
        assert read_structure.umi_cycles == 0
        assert read_structure.skip_cycles == 0
        assert read_structure.total_cycles == 151

    def test_single_end_single_index_umi(self):
        """Test the tokens of a single-end single-indexed umi structure"""
        structure = "10M141T8B"
        read_structure = ReadStructure(structure)
        assert read_structure.is_indexed is True
        assert read_structure.is_dual_indexed is False
        assert read_structure.is_single_end is True
        assert read_structure.is_paired_end is False
        assert read_structure.has_indexes is True
        assert read_structure.has_skips is False
        assert read_structure.has_umi is True

    def test_paired_end_dual_index_umi_tokens(self):
        """Test the tokens of a paired-end dual-indexed umi structure"""
        structure = "10M141T8B8B10M141T"
        read_structure = ReadStructure(structure)
        assert read_structure.is_indexed is True
        assert read_structure.is_dual_indexed is True
        assert read_structure.is_single_end is False
        assert read_structure.is_paired_end is True
        assert read_structure.has_indexes is True
        assert read_structure.has_skips is False
        assert read_structure.has_umi is True

    def test_paired_end_dual_index_umi_cycles(self):
        """Test the cycles of a paired-end dual-indexed umi structure"""
        structure = "10M141T8B8B10M141T"
        read_structure = ReadStructure(structure)
        assert read_structure.index_cycles == 16
        assert read_structure.template_cycles == 282
        assert read_structure.umi_cycles == 20
        assert read_structure.skip_cycles == 0
        assert read_structure.total_cycles == 318

    def test_paired_end_dual_index_umi_skips_cycles(self):
        """Test the cycles of a paired-end dual-indexed umi skip structure"""
        structure = "8M1S142T8B8B8M1S142T"
        read_structure = ReadStructure(structure)
        assert read_structure.index_cycles == 16
        assert read_structure.template_cycles == 284
        assert read_structure.umi_cycles == 16
        assert read_structure.skip_cycles == 2
        assert read_structure.total_cycles == 318

    def test_all_tokens(self):
        """Test all tokens of a paired-end dual-indexed umi skip structure"""
        structure = "8M1S142T8B8B8M1S142T"
        read_structure = ReadStructure(structure)
        read_structure.tokens == ["8M", "1S", "142T", "8B", "8B", "8M", "1S", "142T"]

    def test_copy(self):
        """Test a shallow copy with ``copy()``"""
        read_structure1 = ReadStructure("115T")
        read_structure2 = read_structure1.copy()
        assert id(read_structure1) != id(read_structure2)

    def test_equal(self):
        """Test ``ReadStructure.__eq__()``"""
        structure = "10M141T8B8B10M141T"
        assert ReadStructure(structure) == ReadStructure(structure)
        with raises(NotImplementedError):
            ReadStructure(structure) == "random-string"

    def test_repr(self):
        """Test ``ReadStructure.__repr__()`` after initialization"""
        assert ReadStructure("51T").__repr__() == "ReadStructure(structure='51T')"

    def test_str(self):
        """Test ``ReadStructure.__str__()`` after initialization"""
        assert str(ReadStructure("51T")) == "51T"
