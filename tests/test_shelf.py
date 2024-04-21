import pytest
from feedgen.feed import FeedGenerator


class TestPC20FG:
    @pytest.fixture
    def my_fg(self):
        fg = FeedGenerator()
        fg.title('bob the angry podcast')
        fg.id('https://bob.the.angry.podcast/')
        return fg

    def test_create(self, my_fg):
        assert isinstance(my_fg, FeedGenerator)

    def test_basic_attrs(self, my_fg):
        assert my_fg.title() == 'bob the angry podcast'
        assert my_fg.id() == 'https://bob.the.angry.podcast/'

    def test_ext(self, my_fg):
        my_fg.load_extension('podcasting20')
