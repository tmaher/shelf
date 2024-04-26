import pytest
import feedgen
import feedgen.ext
import pkgutil
from feedgen.feed import FeedGenerator
import sys  # noqa: F401

# FIXME: feedgen is not a namespaced package, hence the path manipulation
# Remove before submitting PR to upstream
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
        fg.link([
            {'href': 'https://bob.the.angry.podcast/rss', 'rel': 'self'},
            {'href': 'https://bob.the.angry.podcast/about'}
        ])
        fg.description('this is a fake podcast by a very angry flower')
        return fg

    @pytest.fixture
    def fe(self, fg):
        fe = fg.add_entry()
        fe.title('bob gets angry')
        with pytest.raises(AttributeError):
            fe.podcasting20.locked('yes', owner='bob@angry.podcast')
        return fe

    def test_poc(self, fg, fe):
        assert isinstance(fg, FeedGenerator)
        assert fe.title() == 'bob gets angry'

# ### SIMPLE tags
#    - only exist as children of item
#    - no children

#    def test_transcript():
#        assert False

#    def test_chapters():
#        assert False

#    def test_soundbite():
#        assert False

#    def test_season():
#        assert False

#    def test_episode():
#        assert False

#    def test_social_interact():
#        assert False


# #### DUAL-USE: these tags
#    - may be children of item **OR** channel, but...
#    - DO NOT have any children themselves

#    def test_person():
#        assert False

#    def test_location():
#        assert False

#    def test_license():
#        assert False

#    def test_images():
#        assert False

#    def test_txt():
#        assert False

# #### COMPLEX tags - these either...
#    - MAY have parents other than channel or item, *OR*
#    - MAY have children themselves

#    def test_alternate_enclosure():
#        assert False

#    def test_source():
#        assert False

#    def test_integrity():
#        assert False

#    def test_value():
#        assert False

#    def test_value_recipient():
#        assert False

#    def test_value_time_split():
#        assert False

#    def test_remote_item(self, fg):
#        assert False
