from feedgen.ext.base import BaseExtension
from feedgen.util import xml_elem, ensure_format

from uuid import UUID, uuid5
from urllib.parse import urlsplit
import re
import sys  # noqa: F401


def url2guid(url):
    GUID_NS_PODCAST = UUID('ead4c236-bf58-58c6-a2c6-a6b28d128cb6')
    s = urlsplit(url)
    no_scheme_url = re.sub(
        r'/+\Z', '',
        ''.join([s.netloc, s.path, s.query, s.fragment])
    )
    return str(uuid5(GUID_NS_PODCAST, no_scheme_url))


class Podcasting20BaseExtension(BaseExtension):
    '''Podcasting 2.0 extension
    See https://podcasting2.org/podcast-namespace
    '''

    def __init__(self):
        self.PC20_NS = 'https://podcastindex.org/namespace/1.0'

        self._nodes = {}
        self._pc20elem_transcript = None
        self._pc20elem_chapters = None
        self._pc20elem_podroll = None
        self._pc20elem_locked = None
        self._pc20elem_funding = None
        self._pc20elem_soundbite = None
        self._pc20elem_person = None
        self._pc20elem_location = None
        self._pc20elem_season = None
        self._pc20elem_episode = None
        self._pc20elem_trailer = None
        self._pc20elem_license = None
        self._pc20elem_alternateEnclosure = None
        self._pc20elem_source = None
        self._pc20elem_integrity = None
        self._pc20elem_guid = None
        self._pc20elem_value = None
        self._pc20elem_valueRecipient = None
        self._pc20elem_medium = None
        self._pc20elem_images = None
        self._pc20elem_liveItem = None
        self._pc20elem_contentLink = None
        self._pc20elem_socialInteract = None
        self._pc20elem_block = None
        self._pc20elem_txt = None
        self._pc20elem_remoteItem = None
        self._pc20elem_updateFrequency = None
        self._pc20elem_podping = None
        self._pc20elem_valueTimeSplit = None

    def extend_ns(self):
        return {'podcast': self.PC20_NS}

    def _extend_xml(self, xml_element):
        '''Extend xml_element with set Podcasting 2.0 fields.

        :param xml_element: etree element
        '''
        for tag in self._nodes.keys():
            if isinstance(self._nodes[tag], list):
                for this_tag in self._nodes[tag]:
                    xml_element.append(this_tag)
            else:
                xml_element.append(self._nodes[tag])

    def extend_atom(self, atom_feed):
        '''Extend an Atom feed with the set Podcasting 2.0 fields.

        :param atom_feed: The feed root element
        :returns: The feed root element
        '''

        self._extend_xml(atom_feed)

        return atom_feed

    def extend_rss(self, rss_feed):
        '''Extend a RSS feed with the set Podcasting 2.0 fields.

        :param rss_feed: The feed root element
        :returns: The feed root element.
        '''
        channel = rss_feed[0]
        self._extend_xml(channel)

        return rss_feed

    # #### channel-only tags ####

    def locked(self, text=None, owner=None):
        '''This tag may be set to yes or no. The purpose is to tell other
        podcast hosting platforms whether they are allowed to import this feed.
        A value of yes means that any attempt to import this feed into a new
        platform should be rejected.

        :param text: must be "yes" or "no"
        :param owner: (optional) The owner attribute is an email address that
        can be used to verify ownership of this feed during move and import
        operations. This could be a public email or a virtual email address
        at the hosting provider that redirects to the owner's true email
        address.
        :returns: dict of locked & owner email
        '''
        if text is not None:
            if text not in ('yes', 'no'):
                raise ValueError("Locked may only be 'yes' or 'no'")
            val = {'text': text}
            node = xml_elem('{%s}%s' % (self.PC20_NS, 'locked'))
            node.text = text
            if owner:
                node.attrib['owner'] = owner
                val['owner'] = owner

            self._pc20elem_locked = val
            self._nodes['locked'] = node

        return self._pc20elem_locked

    def funding(self, fundings=[], replace=False):
        '''This tag lists possible donation/funding links for the podcast.
        The content of the tag is the recommended string to be used with
        the link.

        Funding dicts have two fields, both are required
            - 'text' is a free form string supplied by the creator which they
            expect to be displayed in the app next to the link. Please do not
            exceed 128 characters for the node value or it may be truncated by
            aggregators.
            - 'url' is the URL to be followed to fund the podcast.

        :param fundings: Dicitonary or list of dictionaries with text and url
        :param replace: Add or replace old data. (default false)
        :returns List of funding tags as dictionaries
        '''
        if fundings != []:
            fundings = ensure_format(
                fundings,
                set(['text', 'url']),
                set(['text', 'url'])
            )
            if replace or (not self._nodes.get('funding')):
                funding_nodes = []
                vals = []
            else:
                funding_nodes = self._nodes['funding']
                vals = self._pc20elem_funding
            for fund in fundings:
                val = fund
                vals.append(val)
                node = xml_elem('{%s}%s' % (self.PC20_NS, 'funding'))
                node.text = val['text']
                node.attrib['url'] = val['url']
                funding_nodes.append(node)
            self._nodes['funding'] = funding_nodes
            self._pc20elem_funding = vals
        return self._pc20elem_funding

    def trailer(self, trailers=[], replace=False):
        '''This element is used to define the location of an audio or video
        file to be used as a trailer for the entire podcast or a specific
        season. There can be more than one trailer present in the channel
        of the feed. This element is basically just like an <enclosure> with
        the extra pubdate and season attributes added.

        Dict keys are as follows. text, url, and pubdate are all required.
            - text (required): title of the trailer. It is required.
            Please do not exceed 128 characters for the node value or
            it may be truncated by aggregators.
            - url (required): This is a url that points to the audio or video
            file to be played. This attribute is a string.
            - pubdate (required): The date the trailer was published.
            This attribute is an RFC2822 formatted date string.
            - length (recommended): The length of the file in bytes.
            This attribute is a number.
            - type (recommended): The mime type of the file.
            This attribute is a string.
            - season: If this attribute is present it specifies that this
            trailer is for a particular season number.
            This attribute is a number.

        :param trailers: dict or array of dicts as described above
        :param replace: Add or replace old data. (default false)
        :returns List of funding tags as dictionaries
        '''
        if trailers != []:
            trailers = ensure_format(
                trailers,
                set(['text', 'url', 'pubdate', 'length', 'type', 'season']),
                set(['text', 'url', 'pubdate'])
            )
            if replace or (not self._nodes.get('trailer')):
                trailer_nodes = []
                vals = []
            else:
                trailer_nodes = self._nodes['trailer']
                vals = self._pc20elem_trailer
            for trail in trailers:
                val = trail
                node = xml_elem('{%s}%s' % (self.PC20_NS, 'trailer'))
                node.text = val['text']
                for attr in ['url', 'pubdate', 'length', 'type', 'season']:
                    if val.get(attr):
                        node.attrib[attr] = val[attr]
                trailer_nodes.append(node)
                vals.append(val)
            self._nodes['trailer'] = trailer_nodes
            self._pc20elem_trailer = vals
        return self._pc20elem_trailer

    def guid(self, guid=None, url=None):
        '''This element is used to declare a unique, global identifier for a
        podcast. The value is a UUIDv5, and is easily generated from the RSS
        feed url, with the protocol scheme and trailing slashes stripped off,
        combined with a unique "podcast" namespace which has a UUID of
        ead4c236-bf58-58c6-a2c6-a6b28d128cb6.

        *NOTE*: A podcast gets assigned a podcast:guid once in its lifetime
        using its current feed url (at the time of assignment) as the seed
        value. That GUID is then meant to follow the podcast from then on,
        for the duration of its life, even if the feed url changes. This
        means that when a podcast moves from one hosting platform to another,
        its podcast:guid should be discovered by the new host and imported
        into the new platform for inclusion into the feed.

        This method accepts *EITHER* a caller-provided GUID *OR* a feed
        URL. If you pass both guid & url, it will raise ValueError.

        :param guid: a UUIDv5 string to use as GUID. This will be used
            unmodified in the resulting XML.
        :param url: the feed URL, which will be used to compute the UUIDv5
            GUID. It is ok to include the protocol scheme and trailing
            slashes. They will be stripped off per the podcasting 2.0 spec.
            For example: https://podnews.net/rss , https://podnews.net/rss/ ,
            and podnews.net/rss will all result in the same GUID.
        :returns: the GUID string
        '''
        if guid and url:
            raise ValueError("use either guid or url, NOT BOTH")
            # node = xml_elem('{%s}%s' % (self.PC20_NS, 'guid'))
        return self._pc20elem_guid


class Podcasting20Extension(Podcasting20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.
    '''


class Podcasting20EntryExtension(Podcasting20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.
    '''
    def extend_atom(self, entry):
        '''Add podcasting 2.0 elements to an atom item. Alters the item itself.

        :param entry: An atom entry element.
        :returns: The entry element.
        '''
        self._extend_xml(entry)
        return entry

    def extend_rss(self, item):
        '''Add podcasting 2.0 elements to a RSS item. Alters the item itself.

        :param item: A RSS item element.
        :returns: The item element.
        '''
        self._extend_xml(item)
        return item

    def locked(*args, **kwargs):
        raise AttributeError('locked is channel level only')

    def funding(*args, **kwargs):
        raise AttributeError('funding is channel level only')

    def trailer(*args, **kwargs):
        raise AttributeError('trailer is channel level only')
