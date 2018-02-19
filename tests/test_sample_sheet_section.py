from nose.tools import assert_is_none
from nose.tools import assert_raises
from nose.tools import eq_

from unittest import TestCase

from sample_sheet._sample_sheet import SampleSheet
from sample_sheet._sample_sheet import SampleSheetSection


class TestSampleSheetSection(TestCase):
    """Unit Test for ``SampleSheetSection``"""

    def test_add_attribute(self):
        """Test ``add_attr()`` to update ``_key_map`` appropriately"""
        sample_sheet = SampleSheet()
        sample_sheet.Header.add_attr(
            attr='Investigator_Name',
            value='jdoe',
            name='Investigator Name')

        eq_(sample_sheet.Header._key_map,
            {'Investigator_Name': 'Investigator Name'})

    def test_add_attribute_with_spaces(self):
        """Test ``add_attr()`` to raise exception with whitespace"""
        sample_sheet = SampleSheet()
        assert_raises(
            ValueError,
            lambda: sample_sheet.Header.add_attr(
                attr='Investigator Name',
                value='jdoe',
                name='Investigator Name'))

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None"""
        for key in ('not_real', 'fake'):
            assert_is_none(getattr(SampleSheetSection(), key))

    def test_eq(self):
        section1 = SampleSheetSection()
        section2 = SampleSheetSection()
        section1.test_key = 200
        section2.test_key = 200
        eq_(section1, section2)

    def test_repr(self):
        """Test ``__repr__()``"""
        eq_(SampleSheetSection().__repr__(), 'SampleSheetSection')
