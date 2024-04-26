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


class TestPc20Ext:
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

    def test_entry_extension(self, fg):
        from feedgen.ext.podcasting20_entry import Podcasting20EntryExtension  # type: ignore # noqa: E402 E501

        ee = Podcasting20EntryExtension()
        assert isinstance(ee, Podcasting20EntryExtension)

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

    def test_locked(self, fg):
        fg.podcasting20.locked('yes', owner='bob@angry.podcast')
        assert fg.podcasting20.locked() == {
            'text': 'yes', 'owner': 'bob@angry.podcast'
        }
        with pytest.raises(ValueError):
            fg.podcasting20.locked('bogus')

        fe = fg.add_entry()
        fe.title('locked ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.locked('yes', owner='bob@angry.podcast')

        xml_frag = \
            '<podcast:locked owner="bob@angry.podcast">yes</podcast:locked>'

        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        assert xml_frag in fg_xml

    def test_funding(self, fg):
        test_fundings = [
            {'text': "mo' money",
                'url': 'https://funding2.angry.podcast/'},
            {'text': 'show me the money',
                'url': 'https://funding1.angry.podcast/'}
        ]
        with pytest.raises(ValueError):
            fg.podcasting20.funding('bogus')
        with pytest.raises(ValueError):
            fg.podcasting20.funding(['bogus'])
        with pytest.raises(ValueError):
            fg.podcasting20.funding([{'text': '1', 'url': '2', 'bogus': '3'}])

        fg.podcasting20.funding(test_fundings[0])
        assert fg.podcasting20.funding() == [test_fundings[0]]
        fg.podcasting20.funding(test_fundings, replace=True)
        assert fg.podcasting20.funding() == test_fundings

        fe = fg.add_entry()
        fe.title('funded ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.funding(test_fundings)

        xml_frag_0 = \
            '<podcast:funding url="https://funding1.angry.podcast/">'\
            'show me the money</podcast:funding>'
        xml_frag_1 = \
            '<podcast:funding url="https://funding2.angry.podcast/">'\
            "mo' money</podcast:funding>"

        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 in fg_xml
        assert xml_frag_1 in fg_xml

    def test_trailer(self, fg):
        test_trailers = [
            {'url': 'https://trailer420.angry.podcast/',
             'pubdate': 'Sun, 20 Apr 1969 16:20:00 GMT',
             'text': 'a real smoking trailer'},
            {'url': 'https://trailer0.angry.podcast/',
             'pubdate': 'Thu, 01 Jan 1970 00:00:00 GMT',
             'text': 'this trailer is epoch!'}
        ]
        with pytest.raises(ValueError):
            fg.podcasting20.trailer('bogus')
        with pytest.raises(ValueError):
            fg.podcasting20.trailer(['bogus'])
        with pytest.raises(ValueError):
            fg.podcasting20.trailer({'url': 'http://bogus/'})
        with pytest.raises(ValueError):
            fg.podcasting20.trailer({'url': 'http://bogus/', 'pubdate': 0})
        with pytest.raises(ValueError):
            fg.podcasting20.trailer(
                {'url': 'http://bogus/', 'pubdate': 0, 'text': 'fake', 'x': 1})

        fg.podcasting20.trailer(test_trailers[0])
        assert fg.podcasting20.trailer() == [test_trailers[0]]
        fg.podcasting20.trailer(test_trailers, replace=True)
        assert fg.podcasting20.trailer() == test_trailers

        fe = fg.add_entry()
        fe.title('trailer ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.trailer(test_trailers)

        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        xml_frag_0 = \
            f"<podcast:trailer url=\"{test_trailers[0]['url']}\""\
            f" pubdate=\"{test_trailers[0]['pubdate']}\">"\
            f"{test_trailers[0]['text']}</podcast:trailer>"
        xml_frag_1 = \
            f"<podcast:trailer url=\"{test_trailers[1]['url']}\""\
            f" pubdate=\"{test_trailers[1]['pubdate']}\">"\
            f"{test_trailers[1]['text']}</podcast:trailer>"
        # print(fg_xml)
        assert xml_frag_0 in fg_xml
        assert xml_frag_1 in fg_xml

    def test_url2guid(self, fg):
        from feedgen.ext.podcasting20 import url2guid  # type: ignore
        test_data = [
            {'url': 'https://mp3s.nashownotes.com/pc20rss.xml',
             'guid': '917393e3-1b1e-5cef-ace4-edaa54e1f810'},
            {'url': 'podnews.net/rss////',
             'guid': '9b024349-ccf0-5f69-a609-6b82873eab3c'},
            {'url': 'podnews.net/rss/',
             'guid': '9b024349-ccf0-5f69-a609-6b82873eab3c'}
        ]

        assert url2guid(test_data[0]['url']) == test_data[0]['guid']
        assert url2guid(test_data[1]['url']) == test_data[1]['guid']

    def test_guid(self, fg):
        test_data = [
            {'url': 'https://mp3s.nashownotes.com/pc20rss.xml',
             'guid': '917393e3-1b1e-5cef-ace4-edaa54e1f810'},
            {'url': 'podnews.net/rss////',
             'guid': '9b024349-ccf0-5f69-a609-6b82873eab3c'},
            {'url': 'podnews.net/rss/',
             'guid': '9b024349-ccf0-5f69-a609-6b82873eab3c'}
        ]

        with pytest.raises(ValueError):
            fg.podcasting20.guid(guid='bogus')

        with pytest.raises(ValueError):
            fg.podcasting20.guid(guid=test_data[0]['guid'],
                                 url=test_data[0]['url'])

        assert fg.podcasting20.guid(url=test_data[0]['url']) == \
            test_data[0]['guid']
        assert fg.podcasting20.guid(url=test_data[1]['url']) == \
            test_data[1]['guid']
        assert fg.podcasting20.guid(url=test_data[2]['url']) == \
            test_data[2]['guid']
        assert fg.podcasting20.guid(guid=test_data[0]['guid']) == \
            test_data[0]['guid']

        fe = fg.add_entry()
        fe.title('guid ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.guid(guid=test_data[0]['guid'])

        xml_frag_0 = \
            f"<podcast:guid>{test_data[0]['guid']}</podcast:guid>"
        xml_frag_1 = \
            f"<podcast:guid>{test_data[1]['guid']}</podcast:guid>"
        fg.podcasting20.guid(guid=test_data[1]['guid'])
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_1 in fg_xml
        assert xml_frag_0 not in fg_xml

    def test_medium(self, fg):
        with pytest.raises(ValueError):
            fg.podcasting20.medium('bogus')

        assert fg.podcasting20.medium('podcast') == 'podcast'
        assert fg.podcasting20.medium('music') == 'music'
        assert fg.podcasting20.medium('audiobookL') == 'audiobookL'

        fe = fg.add_entry()
        fe.title('medium ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.guid('music')

        xml_frag_0 = \
            "<podcast:medium>videoL</podcast:medium>"
        xml_frag_1 = \
            "<podcast:medium>film</podcast:medium>"
        fg.podcasting20.medium('film')
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_1 in fg_xml
        assert xml_frag_0 not in fg_xml

    def test_block_multi(self, fg):
        bad_test_blocks = [
            {'block': 'bogus'},
            {'id': 'rss'},
            {'block': 'yes', 'id': '_bogus'},
        ]
        with pytest.raises(ValueError):
            fg.podcasting20.block(bad_test_blocks)
        with pytest.raises(ValueError):
            fg.podcasting20.block(bad_test_blocks[0], replace=True)
        with pytest.raises(ValueError):
            fg.podcasting20.block(bad_test_blocks[1], replace=True)
        with pytest.raises(ValueError):
            fg.podcasting20.block(bad_test_blocks[2], replace=True)

        test_blocks = [
            {'block': 'yes', 'id': 'rss'},
            {'block': 'no', 'id': 'podcastindex'}
        ]
        fg.podcasting20.block(test_blocks[1])
        assert fg.podcasting20.block() == [test_blocks[1]]
        fg.podcasting20.block(test_blocks, replace=True)
        assert fg.podcasting20.block() == test_blocks

        override_test_blocks = [
            {'block': 'no', 'id': '_bogus'},
            {'block': 'yes', 'id': '_double_bogus'}
        ]
        fg.podcasting20.block(
            override_test_blocks,
            slug_override=True,
            replace=True
        )
        assert fg.podcasting20.block() == override_test_blocks
        fg.podcasting20.block(
            override_test_blocks[0],
            slug_override=True,
            replace=True
        )
        assert fg.podcasting20.block() == [override_test_blocks[0]]
        fg.podcasting20.block(
            override_test_blocks[1],
            slug_override=True,
            replace=True
        )
        assert fg.podcasting20.block() == [override_test_blocks[1]]

        with pytest.raises(ValueError):
            fg.podcasting20.block(override_test_blocks, replace=True)

        with pytest.raises(ValueError):
            fg.podcasting20.block(override_test_blocks[0], replace=True)
        with pytest.raises(ValueError):
            fg.podcasting20.block(override_test_blocks[1], replace=True)

        fe = fg.add_entry()
        fe.title('block ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.blocked(test_blocks)

        xml_frag_0 = \
            '<podcast:block id="rss">yes</podcast:block>'
        xml_frag_1 = \
            '<podcast:block id="podcastindex">no</podcast:block>'
        fg.podcasting20.block(test_blocks, replace=True)
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
        fg.podcasting20.block(test_blocks)
        fg.podcasting20.block(test_blocks[1], replace=True)
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
        fg.podcasting20.update_frequency(tcase[0])
        assert fg.podcasting20.update_frequency() == tcase[0]
        fg.podcasting20.update_frequency(tcase[1])
        assert fg.podcasting20.update_frequency() == tcase[1]
        fg.podcasting20.update_frequency(tcase[2])
        assert fg.podcasting20.update_frequency() == tcase[2]
        fg.podcasting20.update_frequency(tcase[3])
        assert fg.podcasting20.update_frequency() == tcase[3]
        fg.podcasting20.update_frequency(tcase[4])
        assert fg.podcasting20.update_frequency() == tcase[4]

        badcase_rrule = {'text': 'rr bogus text', 'rrule': 'freq=bogus'}
        badcase_dtstart = {'text': 'dt bogus text', 'dtstart': 'bogus dt'}
        badcase_complete = {'text': 'comp bogus text',
                            'complete': 'bogocomp'}
        with pytest.raises(ValueError):
            fg.podcasting20.update_frequency(badcase_rrule)
        with pytest.raises(ValueError):
            fg.podcasting20.update_frequency(badcase_dtstart)
        with pytest.raises(ValueError):
            fg.podcasting20.update_frequency(badcase_complete)

        xml_frag_0 = \
            '<podcast:updateFrequency rrule="FREQ=WEEKLY;INTERVAL=2">'\
            'fortnightly</podcast:updateFrequency>'
        xml_frag_1 = \
            '<podcast:updateFrequency rrule="FREQ=WEEKLY;BYDAY=MO,WE">'\
            'Every Monday and Wednesday</podcast:updateFrequency>'
        fg.podcasting20.update_frequency(tcase[0])
        fg.podcasting20.update_frequency(tcase[1])
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 not in fg_xml
        assert xml_frag_1 in fg_xml

    def test_podping(self, fg):
        tcase = [
            {'uses_podping': 'false'},
            {'uses_podping': 'true'},
            {'replace': True}
        ]

        fg.podcasting20.podping(**tcase[0])
        assert fg.podcasting20.podping() == tcase[0]
        fg.podcasting20.podping(**tcase[1])
        assert fg.podcasting20.podping() == tcase[1]
        fg.podcasting20.podping(**tcase[2])
        assert fg.podcasting20.podping() is None

        with pytest.raises(ValueError):
            fg.podcasting20.podping(uses_podping='bogus')

        xml_frag_0 = \
            '<podcast:podping usesPodping="false"/>'
        xml_frag_1 = \
            '<podcast:podping usesPodping="true"/>'
        fg.podcasting20.podping(**tcase[0])
        fg.podcasting20.podping(**tcase[1])
        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        # print(fg_xml)
        assert xml_frag_0 not in fg_xml
        assert xml_frag_1 in fg_xml

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
