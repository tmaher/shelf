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


class TestPc20EntryExt:
    @pytest.fixture
    def fg(self):
        fg = FeedGenerator()
        fg.load_extension('podcast', rss=True, atom=True)
        fg.load_extension('dc', rss=True, atom=True)
        fg.load_extension('pc20', rss=True, atom=True)

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
            fe.pc20.locked('yes', owner='bob@angry.podcast')
        return fe

    def test_poc(self, fg, fe):
        assert isinstance(fg, FeedGenerator)
        assert fe.title() == 'bob gets angry'

# ### SIMPLE tags
#    - parent is always <item>
#    - no children

    def test_transcript(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no url',
             'test': {
                'type': 'application/json',
                'language': 'es',
                'rel': 'captions'
                }},
            {'desc': 'no type',
             'test': {
                'url': 'https://example.com/episode1/transcript.json',
                'language': 'es',
                'rel': 'captions'
                }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.transcript(bad_case['test'], replace=True)

        good_cases = [
            {'desc': 'html',
             'spec':
                '''<podcast:transcript url="https://example.com/episode1/transcript.html" type="text/html" />''',
             'test': {
                'url': 'https://example.com/episode1/transcript.html',
                'type': 'text/html'
                }},
            {'desc': 'vtt',
             'spec':
                '''<podcast:transcript url="https://example.com/episode1/transcript.vtt" type="text/vtt" />''',
             'test': {
                'url': 'https://example.com/episode1/transcript.vtt',
                'type': 'text/vtt'
                }},
            {'desc': 'json',
             'spec':
                '''<podcast:transcript
        url="https://example.com/episode1/transcript.json"
        type="application/json"
        language="es"
        rel="captions"
/>''',
             'test': {
                'url': 'https://example.com/episode1/transcript.json',
                'type': 'application/json',
                'language': 'es',
                'rel': 'captions'
                }},
            {'desc': 'captions',
             'spec':
                '''<podcast:transcript url="https://example.com/episode1/transcript.srt" type="application/x-subrip" rel="captions" />''',
             'test': {
                'url': 'https://example.com/episode1/transcript.srt',
                'type': 'application/x-subrip',
                'rel': 'captions'
                }}
        ]

        helper.simple_multi(
            fg, fe.pc20.transcript, "transcript", good_cases)

    def test_chapters(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no url',
             'test': {
                'type': 'application/json+chapters',
                }},
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.chapters(bad_case['test'])

        good_cases = [
            {'desc': 'spec',
             'spec':
                '''<podcast:chapters url="https://example.com/episode1/chapters.json" type="application/json+chapters" />''',
             'test': {
                    'url': 'https://example.com/episode1/chapters.json',
                    'type': 'application/json+chapters'
                }
             }
        ]
        helper.simple_single(fg, fe.pc20.chapters, "chapters", good_cases,
                             parent="channel/item")

    def test_soundbite(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no startTime',
             'test': {
                 'duration': "101"
             }},
            {'desc': 'no duration',
             'test': {
                 'startTime': "200"
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.soundbite(bad_case['test'])

        good_cases = [
            {'desc': 'no text',
             'spec':
                '''<podcast:soundbite startTime="73.0" duration="60.0" />''',
             'test': {
                'start_time': '73.0',
                'duration': '60.0'
                }},
            {'desc': 'with soundbite text',
             'spec':
                '''<podcast:soundbite startTime="1234.5" duration="42.25">Why the Podcast Namespace Matters</podcast:soundbite>''',
             'test': {
                'start_time': '1234.5',
                'duration': '42.25',
                'soundbite': 'Why the Podcast Namespace Matters'
             }}
        ]

        helper.simple_multi(fg, fe.pc20.soundbite, "soundbite", good_cases)

    def test_season(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no text',
             'test': {
                'name': 'some name'
             }},
            {'desc': 'bogus attrib',
             'test': {
                'season': "5",
                'bogus': "bogus"
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.season(bad_case['test'])

        good_cases = [
            {'desc': 'season 5',
             'spec':
                '''<podcast:season>5</podcast:season>''',
             'test': {
                'season': "5"
             }},
            {'desc': 'whitehouse',
             'spec':
                '''<podcast:season name="Race for the Whitehouse 2020">3</podcast:season>''',
             'test': {
                'season': "3",
                'name': "Race for the Whitehouse 2020"
             }},
            {'desc': 'egypt',
             'spec':
                '''<podcast:season name="Egyptology: The 19th Century">1</podcast:season>''',
             'test': {
                'season': "1",
                'name': "Egyptology: The 19th Century"
             }},
            {'desc': 'yearling',
             'spec':
                '''<podcast:season name="The Yearling - Chapter 3">3</podcast:season>''',
             'test': {
                'season': "3",
                'name': "The Yearling - Chapter 3"
             }}
        ]

        helper.simple_single(fg, fe.pc20.season, "season", good_cases,
                             parent="channel/item")

    def test_episode(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no ep number',
             'test': {
                 'display': "bogus display"
             }},
            {'desc': 'invalid key',
             'test': {
                 'episode': "101",
                 'display': 'podcast 101',
                 'bogus': 'why am I here?'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.episode(bad_case['test'])

        good_cases = [
            {'desc': 'three',
             'spec':
                '''<podcast:episode>3</podcast:episode>''',
             'test': {
                'episode': "3",
             }},
            {'desc': 'three one five point five',
             'spec':
                '''<podcast:episode>315.5</podcast:episode>''',
             'test': {
                'episode': "315.5",
             }},
            {'desc': "chapter 3",
             'spec':
                '''<podcast:episode display="Ch.3">204</podcast:episode>''',
             'test': {
                'episode': "204",
                'display': "Ch.3"
             }},
            {'desc': "day five",
             'spec':
                '''<podcast:episode display="Day 5">9</podcast:episode>''',
             'test': {
                'episode': "9",
                'display': "Day 5"
             }}
        ]

        helper.simple_single(fg, fe.pc20.episode, "episode", good_cases,
                             parent="channel/item")

    def test_social_interact(self, helper, fg, fe):
        bad_cases = [
            {'desc': 'no protocol',
             'test': {
                 'uri': 'https://angry.podcast/456',
                 'account_id': 'bogus234',
                 'account_url': 'https://noproto.invalid/',
                 'priority': '1'
             }},
            {'desc': 'bogus attr',
             'test': {
                 'uri': 'https://angry.podcast/789',
                 'protocol': 'bluesky',
                 'account_id': 'zbogon567',
                 'account_url': 'https://bogusattr.invalid/',
                 'priority': '2',
                 'bogus': 'I should not exist'
             }},
            {'desc': 'bogus proto',
             'test': {
                 'protocol': 'bogusproto',
                 'uri': 'https://angry.podcast/0ab'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.social_interact(bad_case['test'])

        good_cases = [
            {'desc': 'simple',
             'spec':
                '''<podcast:socialInteract
        uri="https://podcastindex.social/web/@dave/108013847520053258"
        protocol="activitypub"
        accountId="@dave"
/>''',
             'test': {
                'uri': "https://podcastindex.social/web/@dave/108013847520053258",
                'protocol': "activitypub",
                'account_id': "@dave"
             }},
            {'desc': 'complex 1',
             'spec':
                '''<podcast:socialInteract
        priority="1"
        uri="https://podcastindex.social/web/@dave/108013847520053258"
        protocol="activitypub"
        accountId="@dave"
        accountUrl="https://podcastindex.social/web/@dave"
/>''',
             'test': {
                'uri': "https://podcastindex.social/web/@dave/108013847520053258",
                'protocol': "activitypub",
                'account_id': "@dave",
                'account_url': "https://podcastindex.social/web/@dave",
                'priority': "1"
             }},
            {'desc': 'complex 2',
             'spec':
                '''<podcast:socialInteract
        priority="2"
        uri="https://twitter.com/PodcastindexOrg/status/1507120226361647115"
        protocol="twitter"
        accountId="@podcastindexorg"
        accountUrl="https://twitter.com/PodcastindexOrg"
/>''',
             'test': {
                'uri': "https://twitter.com/PodcastindexOrg/status/1507120226361647115",
                'protocol': "twitter",
                'account_id': "@podcastindexorg",
                'account_url': "https://twitter.com/PodcastindexOrg",
                'priority': "2"

             }},
            {'desc': "disabled",
             'spec':
                '''<podcast:socialInteract protocol="disabled" />''',
             'test': {
                'protocol': "disabled",
             }}
        ]

        helper.simple_multi(
            fg, fe.pc20.social_interact, "socialInteract", good_cases
        )


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
