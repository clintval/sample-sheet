from nose.tools import assert_is_none, eq_

from sample_sheet._sample_sheet import SampleSheetSection, Header, Settings


class TestSampleSheetSectiont:
    """Unit tests for ``SampleSheetSection``"""

    def test_default_getattr(self):
        """Tests that accessing an unknown attribute returns None"""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(SampleSheetSection(), key))

    def test_repr(self):
        """Tests ``__repr__()``"""
        eq_(SampleSheetSection().__repr__(), 'SampleSheetSection')


class TestHeader:
    """Unit tests for ``Header``"""

    def test_repr(self):
        """Tests ``__repr__()``"""
        eq_(Header().__repr__(), 'Header')


class TestSettings:
    """Unit tests for ``Settings``"""

    def test_repr(self):
        """Tests ``__repr__()``"""
        eq_(Settings().__repr__(), 'Settings')
