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


def xml_simple_single_test(fg, tag_func, tag_name, cases):
    open_dtag = f"<data xmlns:podcast=\"{PC20_NS}\">"
    close_dtag = "</data>"

    for case in cases:
        spec_xml = open_dtag + case['spec'] + close_dtag
        spec_root = etree.fromstring(spec_xml)

        tag_func(case['test'], replace=True)
        test_xml = fg.rss_str(pretty=True).decode('UTF-8')
        test_root = etree.XML(test_xml.encode('UTF-8'))
        # print("***********************************\n\n")
        # print(f"spec - {spec_xml}")
        # print(f"test - {test_xml}")
        # print("***********************************\n\n")

        for attr in case['test'].keys():
            if attr == "text":
                xp_frag = "text()"
            else:
                xp_frag = f"@{attr}"

            test_attr = test_root.xpath(
                f"/rss/channel/item/podcast:{tag_name}/{xp_frag}",
                namespaces=pc20_extend_ns()
            )
            spec_attr = spec_root.xpath(
                f"/data/podcast:{tag_name}/{xp_frag}",
                namespaces=pc20_extend_ns()
            )
            assert spec_attr == test_attr


def xml_simple_multi_test(fg, tag_func, tag_name, cases):
    from xmldiff import main

    open_dtag = f"<data xmlns:podcast=\"{PC20_NS}\">"
    close_dtag = "</data>"

    spec_xml = open_dtag + \
        "".join(map(lambda x: x['spec'], cases)) + close_dtag

    tag_func(list(map(lambda x: x['test'], cases)), replace=True)
    test_kids = etree.XML(fg.rss_str(pretty=True))\
        .xpath(
            f"//podcast:{tag_name}",
            namespaces=pc20_extend_ns()
        )
    test_dtag = etree.fromstring(open_dtag + close_dtag)
    for kid in test_kids:
        test_dtag.append(kid)
    test_xml_rt = etree.tostring(test_dtag).decode('UTF-8')

    diff = main.diff_texts(spec_xml, test_xml_rt)
    assert diff == []


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

        # xml_simple_single_test(fg, fe.pc20.transcript, "transcript", good_cases)
        xml_simple_multi_test(
            fg, fe.pc20.transcript, "transcript", good_cases)

    def test_chapters(self, fg, fe):
        bad_cases = [
            {'desc': 'no url',
             'test': {
                'type': 'application/json+chapters',
                }},
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fe.pc20.chapters(bad_case['test'], replace=True)

        good_cases = [
            {'desc': 'spec', 'spec':
                '''<podcast:chapters url="https://example.com/episode1/chapters.json" type="application/json+chapters" />'''
             }
        ]
        xml_simple_single_test(fg, fe.pc20.chapters, "chapters", good_cases)

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
