from nose.tools import assert_false

from unittest import TestCase

from sample_sheet._sample_sheet import is_ipython_interpreter


class TestIsIpythonInterpreter(TestCase):
    """Unit tests for ``is_ipython_interpreter()``"""

    def test_is_ipython_interpreter(self):
        """Test if this test framework is run in an IPython interpreter."""
        assert_false(is_ipython_interpreter())
