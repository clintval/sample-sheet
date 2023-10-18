from pytest import raises

from sample_sheet import RECOMMENDED_KEYS
from sample_sheet import ReadStructure, Sample


class TestSample(object):
    """Unit tests for ``Sample``"""

    def test_blank_init(self):
        """Test initialization with no parameters."""
        for key in RECOMMENDED_KEYS:
            assert getattr(Sample(), key) is None

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None."""
        for key in ("not_real", "fake"):
            assert getattr(Sample(), key) is None

    def test_promotion_of_read_structure(self):
        """Test that a Read_Structure key is promoted to ``ReadStructure``."""
        sample = Sample({"Read_Structure": "10M141T8B", "index": "ACGTGCNA"})
        assert isinstance(sample.Read_Structure, ReadStructure)

    def test_additional_key_is_added(self):
        """Test that an additional key is added to ``keys()`` method."""
        list(Sample({"Read_Structure": "151T"}).keys()) == ["Read_Structure"]

    def test_read_structure_with_single_index(self):
        """Test that ``index`` is present with  a single-indexed read
        structure.

        """
        with raises(ValueError):
            Sample({"Read_Structure": "141T8B"})

    def test_read_structure_with_dual_index(self):
        """Test that ``index`` and ``index2`` are present with dual-indexed
        read structure.

        """
        with raises(ValueError):
            Sample({"Read_Structure": "141T8B8B141T"})

    def test_valid_index(self):
        """Test "index" and "index2" value validation."""
        Sample({"index": "ACGTN"}).index = "ACGTN"
        Sample({"index": "SI-GA-H1"}).index = "SI-GA-H1"
        Sample({"index": "SI-NA-A8"}).index = "SI-NA-A8"
        Sample({"index": "SI-TT-A1"}).index = "SI-TT-A1"
        Sample({"index": "SI-TS-A1"}).index = "SI-TS-A1"
        with raises(ValueError):
            Sample({"index": "ACUGTN"})
        with raises(ValueError):
            Sample({"index2": "ACUGTN"})

    def test_eq(self):
        """Test equality based only on ``Sample_ID`` and ``Library_ID``."""
        fake1 = Sample({"Sample_ID": 1, "Library_ID": "10x"})
        fake2 = Sample({"Sample_ID": 1})

        assert fake1 != fake2

        fake1 = Sample({"Sample_ID": 1, "Library_ID": "10x"})
        fake2 = Sample({"Sample_ID": 1, "Library_ID": "10x"})

        assert fake1 == fake2

        fake1 = Sample({"Sample_ID": 1, "Library_ID": "10x", "Lane": "1"})
        fake2 = Sample({"Sample_ID": 1, "Library_ID": "10x", "Lane": "2"})

        assert fake1 != fake2
        with raises(NotImplementedError):
            fake1 == "random-string"

    def test_str(self):
        """Test ``sample.__str__()``"""
        assert str(Sample()) == ""
        assert str(Sample({"Sample_ID": 245})) == "245"

    def test_repr(self):
        """Test ``Sample.__repr__()`` after initialization."""

        assert Sample().__repr__() == ("Sample({'Sample_ID': None, " "'Sample_Name': None, 'index': None})")
