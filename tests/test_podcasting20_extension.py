import pytest
import feedgen
import feedgen.ext
import pkgutil
from feedgen.feed import FeedGenerator
import sys  # noqa: F401

# GROSS
feedgen.__path__ = \
    pkgutil.extend_path(feedgen.__path__, feedgen.__name__)
feedgen.ext.__path__ = \
    pkgutil.extend_path(feedgen.ext.__path__, feedgen.ext.__name__)


class TestPodcasting20Extension:
    @pytest.fixture
    def fg(self):
        fg = FeedGenerator()
        fg.load_extension('podcast', rss=True, atom=True)
        fg.load_extension('dc', rss=True, atom=True)
        fg.load_extension('podcasting20', rss=True, atom=True)

        fg.podcast.itunes_explicit('yes')
        fg.title('bob the angry podcast')
        fg.link(href='https://bob.the.angry.podcast/', rel='self')
        fg.description('this is a fake podcast by a very angry flower')
        return fg

    def test_create(self, fg):
        assert isinstance(fg, FeedGenerator)

    def test_basic_attrs(self, fg):
        assert fg.title() == 'bob the angry podcast'
        assert fg.link() == [{'href': 'https://bob.the.angry.podcast/',
                             'rel': 'self'}]

    def test_itunes_explicit(self, fg):
        assert fg.podcast.itunes_explicit() == 'yes'

    def test_locked(self, fg):
        fg.podcasting20.locked('yes', owner='bob@angry.podcast')
        assert fg.podcasting20.locked() == {
            'locked': 'yes', 'owner': 'bob@angry.podcast'
        }
        with pytest.raises(ValueError):
            fg.podcasting20.locked('bogus')

        fe = fg.add_entry().title('locked ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.locked('yes', owner='bob@angry.podcast')

        xml_frag = \
            '<podcast:locked owner="bob@angry.podcast">yes</podcast:locked>'
        assert xml_frag in fg.rss_str().decode('UTF-8')
        # fg.rss_str
        # sys.stderr.write(fg.rss_str(pretty=True).decode('UTF-8'))
