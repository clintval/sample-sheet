from nose.tools import assert_is_none

from unittest import TestCase

from sample_sheet import Section


class TestSection(TestCase):
    """Unit tests for ``Section``"""

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None"""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(Section(), key))

    def test_that_getattr_returns_getitem(self):
        """Tests that we can access keys as atributes"""
        section = Section()
        section['PoolRNA'] = 'temporary'
        assert section.PoolRNA == 'temporary'
