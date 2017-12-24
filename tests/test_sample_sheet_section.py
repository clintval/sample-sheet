from nose.tools import assert_is_none, eq_

from sample_sheet._sample_sheet import SampleSheetSection, Header, Settings


class TestSampleSheetSectiont:
    """Unit Test for ``SampleSheetSection``"""

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None"""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(SampleSheetSection(), key))

    def test_repr(self):
        """Test ``__repr__()``"""
        eq_(SampleSheetSection().__repr__(), 'SampleSheetSection')


class TestHeader:
    """Unit Test for ``Header``"""

    def test_repr(self):
        """Tests ``__repr__()``"""
        eq_(Header().__repr__(), 'Header')


class TestSettings:
    """Unit Test for ``Settings``"""

    def test_repr(self):
        """Test ``__repr__()``"""
        eq_(Settings().__repr__(), 'Settings')
