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

    def test_create(self, fg):
        assert isinstance(fg, FeedGenerator)

    def test_basic_attrs(self, fg):
        assert fg.title() == 'bob the angry podcast'
        assert fg.link() == [
            {'href': 'https://bob.the.angry.podcast/rss', 'rel': 'self'},
            {'href': 'https://bob.the.angry.podcast/about'}
        ]

    def test_itunes_explicit(self, fg):
        assert fg.podcast.itunes_explicit() == 'yes'

    # #### channel-only tags ####
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

    def test_block(self, fg):
        fg.podcasting20.block('yes', id='rss')
        assert fg.podcasting20.block() == \
            {'block': 'yes', 'id': 'rss'}
        fg.podcasting20.block('no', id='podcastindex')
        assert fg.podcasting20.block() == \
            {'block': 'no', 'id': 'podcastindex'}
        with pytest.raises(ValueError):
            fg.podcasting20.block('bogus')
        with pytest.raises(ValueError):
            fg.podcasting20.block('yes', id='__bogus')
        fg.podcasting20.block('yes', id='__bogus', slug_override=True)
        assert fg.podcasting20.block() == \
            {'block': 'yes', 'id': '__bogus'}

        fe = fg.add_entry()
        fe.title('block ep')
        with pytest.raises(AttributeError):
            fe.podcasting20.blocked('yes', id='rss')

        xml_frag_0 = \
            '<podcast:block id="rss">yes</podcast:block>'
        xml_frag_1 = \
            '<podcast:block id="rss">yes</podcast:block>'

        fg_xml = fg.rss_str(pretty=True).decode('UTF-8')
        print(fg_xml)
        assert xml_frag_1 in fg_xml
        assert xml_frag_0 not in fg_xml

#    def test_podroll(self, fg):
#        assert False

#    def test_updateFrequency(self, fg):
#        assert False

#    def test_podping(self, fg):
#        assert False

#    def test_liveItem(self, fg):
#        assert False
