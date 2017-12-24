from nose.tools import eq_

from sample_sheet import *  # Test import of __all__

to_snake_case = camel_case_to_snake_case


class TestCamelCaseToSnakeCase:
    """Unit tests for ``camel_case_to_snake_case()``"""

    def test_simple_conversion(self):
        """Test direct conversion from valid camelCase to snake_case"""
        eq_(to_snake_case('camelCase'), 'camel_case')

    def test_with_multiple_caps(self):
        """Test strings with multiple capitals in a row"""
        eq_(to_snake_case('getHTTPResponseCode'), 'get_http_response_code')

    def test_with_multiple_caps_and_numbers(self):
        """Test strings with multiple capitals in a row and numbers"""
        eq_(to_snake_case('get2HTTPResp123Code'), 'get2_http_resp123_code')
