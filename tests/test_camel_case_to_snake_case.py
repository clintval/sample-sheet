from nose.tools import eq_

from unittest import TestCase

from sample_sheet import *  # Test import of __all__


class TestCamelCaseToSnakeCase(TestCase):
    """Unit tests for ``camel_case_to_snake_case()``"""

    def test_simple_conversion(self):
        """Test direct conversion from valid camelCase to snake_case"""
        eq_(camel_case_to_snake_case('camelCase'), 'camel_case')

    def test_with_multiple_caps(self):
        """Test strings with multiple capitals in a row"""
        eq_(camel_case_to_snake_case('getHTTPRespCode'), 'get_http_resp_code')

    def test_with_multiple_caps_and_numbers(self):
        """Test strings with multiple capitals in a row and numbers"""
        eq_(camel_case_to_snake_case('get2HTTPRe123Co'), 'get2_http_re123_co')
