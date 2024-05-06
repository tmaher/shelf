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
# from feedgen.ext.pc20 import (  # type: ignore # noqa: E402
#    PC20_NS, pc20_extend_ns, to_lower_camel_case
# )


class TestPc20Ext:
    @pytest.fixture
    def fg(self):
        fg = FeedGenerator()
        fg.load_extension('podcast', rss=True, atom=True)
        fg.load_extension('pc20', rss=True, atom=True)

        fg.podcast.itunes_explicit('yes')
        fg.title('bob the angry podcast')
        fg.link([
            {'href': 'https://bob.the.angry.podcast/rss', 'rel': 'self'},
            {'href': 'https://bob.the.angry.podcast/about'}
        ])
        fg.description('this is a fake podcast by a very angry flower')
        return fg

    def test_create(self, fg):
        assert isinstance(fg, FeedGenerator)

    def test_basic_attrs(self, fg):
        assert fg.title() == 'bob the angry podcast'
        assert fg.link() == [
            {'href': 'https://bob.the.angry.podcast/rss', 'rel': 'self'},
            {'href': 'https://bob.the.angry.podcast/about'}
        ]

    # ### SIMPLE tags
    #    - only exist as children of channel
    #    - no children

    def test_locked(self, helper, fg):
        bad_cases = [
            {'desc': 'bogus lock',
             'test': {
                 'locked': 'bogus'
             }},
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.locked(bad_case['test'])
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'simple yes',
             'spec':
                '''<podcast:locked>yes</podcast:locked>''',
             'test': {
                'locked': 'yes'
             }},
            {'desc': 'with owner',
             'spec':
                '''<podcast:locked owner="email@example.com">no</podcast:locked>''',
             'test': {
                'locked': 'no',
                'owner': 'email@example.com'
             }}
        ]
        helper.simple_single(fg, fg.pc20.locked, "locked", good_cases)

    def test_funding(self, helper, fg):
        bad_cases = [
            {'desc': 'bogus param',
             'test': {
                'bogustag': 'true'
             }},
            {'desc': 'funding no url',
             'test': {
                'funding': 'what is my url?'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.funding(bad_case['test'], replace=True)
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'support the show',
             'spec':
                '''<podcast:funding url="https://www.example.com/donations">Support the show!</podcast:funding>''',
             'test': {
                'url': 'https://www.example.com/donations',
                'funding': 'Support the show!'
                }},
            {'desc': 'become a member',
             'spec':
                '''<podcast:funding url="https://www.example.com/members">Become a member!</podcast:funding>''',
             'test': {
               'url': 'https://www.example.com/members',
               'funding': 'Become a member!'
             }}
        ]

        helper.simple_multi(fg, fg.pc20.funding, "funding", good_cases)

    def test_trailer(self, helper, fg):
        bad_cases = [
            {'desc': 'url only',
             'test': {
                'url': 'https://nodate.somedomain/'
             }},
            {'desc': 'bad date',
             'test': {
                'url': 'https://baddate.somedomain/',
                'pubdate': '-1'
             }},
            {'desc': 'bad param',
             'test': {
                'url': 'https://badparam.somedomain/',
                'pubdate': 'Thu, 01 Apr 2021 08:00:00 EST',
                'bogus': 'i am a bogon param'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.trailer(bad_case['test'], replace=True)
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'april 1',
             'spec':
             '''<podcast:trailer
        pubdate="Thu, 01 Apr 2021 08:00:00 EST"
        url="https://example.org/trailers/teaser"
        length="12345678"
        type="audio/mp3"
>Coming April 1st, 2021</podcast:trailer>''',
             'test': {
                'pubdate': "Thu, 01 Apr 2021 08:00:00 EST",
                'url': 'https://example.org/trailers/teaser',
                'length': '12345678',
                'type': 'audio/mp3',
                'trailer': 'Coming April 1st, 2021'
             }},
            {'desc': 'white HOUSE',
             'spec':
             '''<podcast:trailer
        pubdate="Thu, 01 Apr 2021 08:00:00 EST"
        url="https://example.org/trailers/season4teaser"
        length="12345678"
        type="video/mp4"
        season="4"
>Season 4: Race for the Whitehouse</podcast:trailer>''',
             'test': {
                'pubdate': 'Thu, 01 Apr 2021 08:00:00 EST',
                'url': 'https://example.org/trailers/season4teaser',
                'length': '12345678',
                'type': 'video/mp4',
                'season': '4',
                'trailer': 'Season 4: Race for the Whitehouse'
             }},
            {'desc': 'whitehouse with iso time',
             'spec':
                '''<podcast:trailer
        pubdate="Thu, 01 Apr 2021 08:00:00 -0500"
        url="https://example.org/trailers/season4teaser"
        length="12345678"
        type="video/mp4"
        season="4"
>Season 4: Race for the Whitehouse</podcast:trailer>''',
             'test': {
                'pubdate': '2021-04-01T08:00:00.000-05:00',
                'url': 'https://example.org/trailers/season4teaser',
                'length': '12345678',
                'type': 'video/mp4',
                'season': '4',
                'trailer': 'Season 4: Race for the Whitehouse'
             }}
        ]

        helper.simple_multi(fg, fg.pc20.trailer, "trailer", good_cases,
                            skip_modified=['pubdate'])

    def test_url_to_guid(self, fg):
        from feedgen.ext.pc20 import url_to_guid  # type: ignore
        good_cases = [
            {'desc': 'nashownotes',
             'spec': '917393e3-1b1e-5cef-ace4-edaa54e1f810',
             'test': {
                'url': 'mp3s.nashownotes.com/pc20rss.xml'
             }},
            {'desc': 'podnews',
             'spec': '9b024349-ccf0-5f69-a609-6b82873eab3c',
             'test': {
                'url': 'podnews.net/rss'
             }},
            {'desc': 'podnews with scheme',
             'spec': '9b024349-ccf0-5f69-a609-6b82873eab3c',
             'test': {
                'url': 'podnews.net/rss'
             }},
            {'desc': 'podnews trailing slash',
             'spec': '9b024349-ccf0-5f69-a609-6b82873eab3c',
             'test': {
                'url': 'podnews.net/rss/'
             }},
            {'desc': 'podnews scheme plus trailing slash',
             'spec': '9b024349-ccf0-5f69-a609-6b82873eab3c',
             'test': {
                'url': 'ftp://podnews.net/rss/'
             }},
        ]

        for case in good_cases:
            test_guid = url_to_guid(**case['test'])
            if case['spec'] != test_guid:
                pytest.fail(f"url {case['test']['url']}\n"
                            f"EXPECTED {case['spec']}\n"
                            f"BUT  GOT {test_guid}\n")

    def test_guid(self, helper, fg):
        bad_cases = [
            {'desc': 'bad param',
             'test': {
                 'bogus': 'bogus'
             }},
            {'desc': 'bad guid',
             'test': {
                 'guid': 'bogus'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.guid(bad_case['test'])
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'nashownotes',
             'spec':
             '''<podcast:guid>917393e3-1b1e-5cef-ace4-edaa54e1f810</podcast:guid>''',
             'test': {
                'guid': '917393e3-1b1e-5cef-ace4-edaa54e1f810'
             }},
            {'desc': 'podnews',
             'spec':
             '''<podcast:guid>9b024349-ccf0-5f69-a609-6b82873eab3c</podcast:guid>''',
             'test': {
                'guid': '9b024349-ccf0-5f69-a609-6b82873eab3c'
             }}
        ]
        helper.simple_single(fg, fg.pc20.guid, "guid", good_cases)

    def test_medium(self, helper, fg):
        bad_cases = [
            {'desc': 'bogus key',
             'test': {
                'bogus': 'bogus'
             }},
            {'desc': 'rant is bogus',
             'test': {
                 'medium': 'rant'
             }},
            {'desc': 'good medium, bogus key',
             'test': {
                 'medium': 'musicL',
                 'bogus': 'bogus'
             }}
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.medium(bad_case['test'])
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'podcast',
             'spec':
                '''<podcast:medium>podcast</podcast:medium>''',
             'test': {
                'medium': 'podcast'
             }},
            {'desc': 'music',
             'spec':
                '''<podcast:medium>music</podcast:medium>''',
             'test': {
                'medium': 'music'
             }},
            {'desc': 'musicL',
             'spec':
                '''<podcast:medium>musicL</podcast:medium>''',
             'test': {
                'medium': 'musicL'
             }},
        ]
        helper.simple_single(fg, fg.pc20.medium, "medium", good_cases)

    def test_block_multi(self, fg):
        bad_test_blocks = [
            {'block': 'bogus'},
            {'id': 'rss'},
            {'block': 'yes', 'id': '_bogus'},
        ]
        with pytest.raises(ValueError):
            fg.pc20.block(bad_test_blocks)
        with pytest.raises(ValueError):
            fg.pc20.block(bad_test_blocks[0], replace=True)
        with pytest.raises(ValueError):
            fg.pc20.block(bad_test_blocks[1], replace=True)
        with pytest.raises(ValueError):
            fg.pc20.block(bad_test_blocks[2], replace=True)

        test_blocks = [
            {'block': 'yes', 'id': 'rss'},
            {'block': 'no', 'id': 'podcastindex'}
        ]
        fg.pc20.block(test_blocks[1])
        assert fg.pc20.block() == [test_blocks[1]]
        fg.pc20.block(test_blocks, replace=True)
        assert fg.pc20.block() == test_blocks

        override_test_blocks = [
            {'block': 'no', 'id': '_bogus'},
            {'block': 'yes', 'id': '_double_bogus'}
        ]
        fg.pc20.block(
            override_test_blocks,
            slug_override=True,
            replace=True
        )
        assert fg.pc20.block() == override_test_blocks
        fg.pc20.block(
            override_test_blocks[0],
            slug_override=True,
            replace=True
        )
        assert fg.pc20.block() == [override_test_blocks[0]]
        fg.pc20.block(
            override_test_blocks[1],
            slug_override=True,
            replace=True
        )
        assert fg.pc20.block() == [override_test_blocks[1]]

        with pytest.raises(ValueError):
            fg.pc20.block(override_test_blocks, replace=True)

        with pytest.raises(ValueError):
            fg.pc20.block(override_test_blocks[0], replace=True)
        with pytest.raises(ValueError):
            fg.pc20.block(override_test_blocks[1], replace=True)

        fe = fg.add_entry()
        fe.title('block ep')
        with pytest.raises(AttributeError):
            fe.pc20.blocked(test_blocks)

        xml_frag_0 = \
            '<podcast:block id="rss">yes</podcast:block>'
        xml_frag_1 = \
            '<podcast:block id="podcastindex">no</podcast:block>'
        fg.pc20.block(test_blocks, replace=True)
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 in fg_xml
        assert xml_frag_1 in fg_xml

    def test_block_single(self, fg):
        test_blocks = [
            {'block': 'yes', 'id': 'rss'},
            {'block': 'no', 'id': 'podcastindex'}
        ]
        xml_frag_0 = \
            '<podcast:block id="rss">yes</podcast:block>'
        xml_frag_1 = \
            '<podcast:block id="podcastindex">no</podcast:block>'
        fg.pc20.block(test_blocks)
        fg.pc20.block(test_blocks[1], replace=True)
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 not in fg_xml
        assert xml_frag_1 in fg_xml

    def test_updateFrequency(self, fg):
        tcase = [
            {'text': 'fortnightly', 'rrule': 'FREQ=WEEKLY;INTERVAL=2'},
            {'text': 'Every Monday and Wednesday',
             'rrule': 'FREQ=WEEKLY;BYDAY=MO,WE'},
            {'text': 'US turkey day',
             'rrule': 'FREQ=YEARLY;BYDAY=+4TH;BYMONTH=11'},
            {'text': 'Alt Mondays for 10 episodes starting on Aug 28, 2023',
             'rrule': 'FREQ=WEEKLY;INTERVAL=2;BYDAY=MO;COUNT=10',
             'dtstart': '2023-08-28T00:00:00.000Z'
             },
            {'text': "That’s all folks!", 'complete': 'true'}
        ]
        fg.pc20.update_frequency(tcase[0])
        assert fg.pc20.update_frequency() == tcase[0]
        fg.pc20.update_frequency(tcase[1])
        assert fg.pc20.update_frequency() == tcase[1]
        fg.pc20.update_frequency(tcase[2])
        assert fg.pc20.update_frequency() == tcase[2]
        fg.pc20.update_frequency(tcase[3])
        assert fg.pc20.update_frequency() == tcase[3]
        fg.pc20.update_frequency(tcase[4])
        assert fg.pc20.update_frequency() == tcase[4]

        badcase_rrule = {'text': 'rr bogus text', 'rrule': 'freq=bogus'}
        badcase_dtstart = {'text': 'dt bogus text', 'dtstart': 'bogus dt'}
        badcase_complete = {'text': 'comp bogus text',
                            'complete': 'bogocomp'}
        with pytest.raises(ValueError):
            fg.pc20.update_frequency(badcase_rrule)
        with pytest.raises(ValueError):
            fg.pc20.update_frequency(badcase_dtstart)
        with pytest.raises(ValueError):
            fg.pc20.update_frequency(badcase_complete)

        xml_frag_0 = \
            '<podcast:updateFrequency rrule="FREQ=WEEKLY;INTERVAL=2">'\
            'fortnightly</podcast:updateFrequency>'
        xml_frag_1 = \
            '<podcast:updateFrequency rrule="FREQ=WEEKLY;BYDAY=MO,WE">'\
            'Every Monday and Wednesday</podcast:updateFrequency>'
        fg.pc20.update_frequency(tcase[0])
        fg.pc20.update_frequency(tcase[1])
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 not in fg_xml
        assert xml_frag_1 in fg_xml

    def test_podping(self, helper, fg):
        bad_cases = [
            {'desc': 'bogus ping',
             'test': {
                 'uses_podping': 'bogus'
             }},
        ]

        for bad_case in bad_cases:
            with pytest.raises(ValueError):
                fg.pc20.podping(bad_case['test'])
                pytest.fail(f"BAD CASE PASS\n{bad_case}\n")

        good_cases = [
            {'desc': 'simple true',
             'spec':
                '''<podcast:podping usesPodping="true"/>''',
             'test': {
                'uses_podping': 'true'
             }},
            {'desc': 'simple false',
             'spec':
                '''<podcast:podping usesPodping="false"/>''',
             'test': {
                'uses_podping': 'false'
             }}
        ]
        helper.simple_single(fg, fg.pc20.podping, "podping", good_cases)


# #### DUAL-USE: these tags
#    - may be children of item **OR** channel, but...
#    - DO NOT have any children themselves

#    def test_person(self, fg):
#        assert False

#    def test_location(self, fg):
#        assert False

#    def test_license(self, fg):
#        assert False

#    def test_images(self, fg):
#        assert False

#    def test_txt(self, fg):
#        assert False

# #### COMPLEX tags - these either...
#    - MAY have parents other than channel or item, *OR*
#    - MAY have children themselves

#    def test_podroll(self, fg):
#        assert False

#    def test_remote_item(self, fg):
#        assert False

# note - as of 2024-04-24
# https://podcasting2.org/podcast-namespace/tags/liveItem says liveItem
# is not used anywhere, so deferring this for now
#    def test_liveItem(self, fg):
#        assert False

#    def test_value():
#        assert False

#    def test_value_recipient():
#        assert False

#    def test_value_time_split():
#        assert False
