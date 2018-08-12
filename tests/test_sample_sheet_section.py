from nose.tools import assert_is_none

from unittest import TestCase

from sample_sheet._sample_sheet import SampleSheetSection


class TestSampleSheetSection(TestCase):
    """Unit tests for ``SampleSheetSection``"""

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None"""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(SampleSheetSection(), key))

    def test_that_getattr_returns_getitem(self):
        """Tests that we can access keys as atributes"""
        section = SampleSheetSection()
        section['PoolRNA'] = 'temporary'
        assert section.PoolRNA == 'temporary'
