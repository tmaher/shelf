import pytest
from shelf import ShelfFeedGenerator


class TestSFG:
    @pytest.fixture
    def my_sfg(self):
        sfg = ShelfFeedGenerator()
        sfg.title('bob the angry podcast')
        sfg.id('https://bob.the.angry.podcast/')
        return sfg

    def test_create(self, my_sfg):
        assert isinstance(my_sfg, ShelfFeedGenerator)

    def test_basic_attrs(self, my_sfg):
        assert my_sfg.title() == 'bob the angry podcast'
        assert my_sfg.id() == 'https://bob.the.angry.podcast/'

    def test_ext(self, my_sfg):
        True
