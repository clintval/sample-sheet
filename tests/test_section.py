from sample_sheet import Section


class TestSection(object):
    """Unit tests for ``Section``"""

    def test_default_getattr(self):
        """Test that accessing an unknown attribute returns None"""
        for key in ("not_real", "fake"):
            assert getattr(Section(), key) is None

    def test_that_getattr_returns_getitem(self):
        """Tests that we can access keys as atributes"""
        section = Section()
        section["PoolRNA"] = "temporary"
        assert section.PoolRNA == "temporary"
