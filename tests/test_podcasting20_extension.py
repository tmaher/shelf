import pytest
import feedgen
import feedgen.ext
import pkgutil
from feedgen.feed import FeedGenerator

# GROSS
feedgen.__path__ = \
    pkgutil.extend_path(feedgen.__path__, feedgen.__name__)
feedgen.ext.__path__ = \
    pkgutil.extend_path(feedgen.ext.__path__, feedgen.ext.__name__)


class TestPodcasting20Extension:
    @pytest.fixture
    def fg(self):
        fg = FeedGenerator()
        fg.load_extension('podcast')
        fg.load_extension('dc')
        fg.load_extension('podcasting20')

        fg.podcast.itunes_explicit('yes')
        fg.title('bob the angry podcast')
        fg.id('https://bob.the.angry.podcast/')
        return fg

    def test_create(self, fg):
        assert isinstance(fg, FeedGenerator)

    def test_basic_attrs(self, fg):
        assert fg.title() == 'bob the angry podcast'
        assert fg.id() == 'https://bob.the.angry.podcast/'

    def test_itunes_explicit(self, fg):
        assert fg.podcast.itunes_explicit() == 'yes'

    def test_locked(self, fg):
        fg.podcasting20.locked('yes', owner='bob@angry.podcast')
        assert fg.podcasting20.locked() == {
            'locked': 'yes', 'owner': 'bob@angry.podcast'
        }
        with pytest.raises(ValueError):
            fg.podcasting20.locked('bogus')
