import pytest
import feedgen
import feedgen.ext
import pkgutil
from lxml import etree
from feedgen.feed import FeedGenerator
import sys  # noqa: F401

# FIXME: feedgen is not a namespaced package, hence the path manipulation
# Remove before submitting PR to upstream
feedgen.__path__ = \
    pkgutil.extend_path(feedgen.__path__, feedgen.__name__)
feedgen.ext.__path__ = \
    pkgutil.extend_path(feedgen.ext.__path__, feedgen.ext.__name__)

from feedgen.ext.pc20 import PC20_NS, pc20_extend_ns  # type: ignore # noqa: E402 E501


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

    def test_transcript(self, fg, fe):
        tcase_html = {
            'url': 'https://example.com/episode1/transcript.html',
            'type': 'text/html'
        }
        tcase_vtt = {
            'url': 'https://example.com/episode1/transcript.vtt',
            'type': 'text/vtt'
        }
        tcase_json = {
            'url': 'https://example.com/episode1/transcript.json',
            'type': 'application/json',
            'language': 'es',
            'rel': 'captions'
        }
        tcase_srt = {
            'url': 'https://example.com/episode1/transcript.srt',
            'type': 'application/x-subrip',
            'rel': 'captions'
        }

        fe.pc20.transcript(tcase_html)
        assert fe.pc20.transcript() == [tcase_html]
        fe.pc20.transcript(tcase_vtt, replace=True)
        assert fe.pc20.transcript() == [tcase_vtt]
        fe.pc20.transcript(tcase_json, replace=True)
        assert fe.pc20.transcript() == [tcase_json]
        fe.pc20.transcript(tcase_srt, replace=True)
        assert fe.pc20.transcript() == [tcase_srt]

        bad_test_nourl = {
            'type': 'application/json',
            'language': 'es',
            'rel': 'captions'
        }
        bad_test_notype = {
            'url': 'https://example.com/episode1/transcript.json',
            'language': 'es',
            'rel': 'captions'
        }

        with pytest.raises(ValueError):
            fe.pc20.transcript(bad_test_nourl, replace=True)
        with pytest.raises(ValueError):
            fe.pc20.transcript(bad_test_notype, replace=True)

        cases = [
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

        open_dtag = f"<data xmlns:podcast=\"{PC20_NS}\">"
        close_dtag = "</data>"
        for case in cases:
            spec_xml = open_dtag + case['spec'] + close_dtag
            spec_root = etree.fromstring(spec_xml)

            fe.pc20.transcript(case['test'], replace=True)
            test_xml = fg.rss_str(pretty=True).decode('UTF-8')
            test_root = etree.XML(test_xml.encode('UTF-8'))
            # print("***********************************\n\n")
            # print(f"spec - {spec_xml}")
            # print(f"test - {test_xml}")
            # print("***********************************\n\n")

            for attr in case['test'].keys():
                test_attr = test_root.xpath(
                    f"/rss/channel/item/podcast:transcript/@{attr}",
                    namespaces=pc20_extend_ns()
                )
                spec_attr = spec_root.xpath(
                    f"/data/podcast:transcript/@{attr}",
                    namespaces=pc20_extend_ns()
                )
                assert spec_attr == test_attr

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
