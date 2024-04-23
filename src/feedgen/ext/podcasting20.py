from feedgen.ext.base import BaseExtension
from feedgen.util import xml_elem, ensure_format

import uuid
import urllib
import re
import sys  # noqa: F401


def url2guid(url):
    GUID_NS_PODCAST = uuid.UUID('ead4c236-bf58-58c6-a2c6-a6b28d128cb6')
    s = urllib.parse.urlsplit(url)
    no_scheme_url = re.sub(
        r'/+\Z', '',
        ''.join([s.netloc, s.path, s.query, s.fragment])
    )
    return str(uuid.uuid5(GUID_NS_PODCAST, no_scheme_url))


class Podcasting20BaseExtension(BaseExtension):
    '''Podcasting 2.0 extension. See the following for specs:

        * https://podcasting2.org/podcast-namespace
        * https://podcastindex.org/namespace/1.0

    Tags shared <channel> and <item> go here.
    '''

    def __init__(self):
        self.PC20_NS = 'https://podcastindex.org/namespace/1.0'

        # Canonical list of service slugs is at...
        # https://github.com/Podcastindex-org/podcast-namespace/blob/main/serviceslugs.txt
        self.SERVICE_SLUGS = [
            'acast', 'amazon', 'anchor', 'apple', 'audible', 'audioboom',
            'backtracks', 'bitcoin', 'blubrry', 'buzzsprout', 'captivate',
            'castos', 'castopod', 'facebook', 'fireside', 'fyyd', 'google',
            'gpodder', 'hypercatcher', 'kasts', 'libsyn', 'mastodon',
            'megafono', 'megaphone', 'omnystudio', 'overcast', 'paypal',
            'pinecast', 'podbean', 'podcastaddict', 'podcastguru',
            'podcastindex', 'podcasts', 'podchaser', 'podcloud',
            'podfriend', 'podiant', 'podigee', 'podnews', 'podomatic',
            'podserve', 'podverse', 'redcircle', 'relay',
            'resonaterecordings', 'rss', 'shoutengine', 'simplecast',
            'slack', 'soundcloud', 'spotify', 'spreaker', 'tiktok',
            'transistor', 'twitter', 'whooshkaa', 'youtube', 'zencast'
        ]

        self._nodes = {}
        self._pc20elem_transcript = None
        self._pc20elem_chapters = None
        self._pc20elem_podroll = None
        self._pc20elem_soundbite = None
        self._pc20elem_person = None
        self._pc20elem_location = None
        self._pc20elem_season = None
        self._pc20elem_episode = None
        self._pc20elem_license = None
        self._pc20elem_alternateEnclosure = None
        self._pc20elem_source = None
        self._pc20elem_integrity = None
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


class Podcasting20Extension(Podcasting20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.

    Tags that are only direct children of <channel> go in this class
    '''
    def __init__(self):
        super().__init__()
        self._pc20elem_locked = None
        self._pc20elem_funding = None
        self._pc20elem_trailer = None
        self._pc20elem_guid = None

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
        if guid or url:
            if guid:
                # validate guid is well-formated by parsing
                # if it isn't, this will raise ValueError
                guid = str(uuid.UUID(guid))
            elif url:
                guid = url2guid(url)
            node = xml_elem('{%s}%s' % (self.PC20_NS, 'guid'))
            node.text = guid
            self._nodes['guid'] = node
            self._pc20elem_guid = guid

        return self._pc20elem_guid

    def medium(self, medium=None):
        '''The medium tag tells an application what the content contained
        within the feed IS, as opposed to what the content is ABOUT in the
        case of a category. This allows a podcast app to modify it's behavior
        or UI to give a better experience to the user for this content. For
        example, if a podcast has <podcast:medium>music</podcast:medium> an
        app may choose to reset playback speed to 1x and adjust it's EQ
        settings to be better for music vs. spoken word.

        Accepted medium names are curated within a list maintained by the
        community as new mediums are discovered over time. Newly proposed
        mediums should require some level of justification to be added to
        this list. One may argue and/or prove use of a new medium even for
        only one application, should it prove different enough from existing
        mediums to have meaning.

        The node value is a string denoting one of the following possible
        values:

            - podcast (default) - Describes a feed for a podcast show. If no
            medium tag is present in the channel, this medium is assumed.
            - music - A feed of music organized into an "album" with each
            item a song within the album.
            - video - Like a "podcast" but used in a more visual experience.
            Something akin to a dedicated video channel like would be found on
            YouTube.
            - film - Specific types of videos with one item per feed. This is
            different than a video medium because the content is considered to
            be cinematic; like a movie or documentary.
            - audiobook - Specific types of audio with one item per feed, or
            where items represent chapters within the book.
            - newsletter - Describes a feed of curated written articles.
            Newsletter articles now sometimes have an spoken version audio
            enclosure attached.
            - blog - Describes a feed of informally written articles. Similar
            to newsletter but more informal as in a traditional blog platform
            style.

        In addition to the above mediums, each medium also has a counterpart
        "list" variant, where the original medium name is suffixed by the
        letter "L" to indicate that it is a "List" of that type of content.
        For example, podcast would become podcastL, music would become musicL,
        audiobook would become audiobookL, etc.

        There is also a dedicated list medium for mixed content:

            - mixed - This list medium type describes a feed of
            <podcast:remoteItem>'s that point to different remote medium
            types. For instance, a single list feed might point to music,
            podcast and audiobook items in other feeds. An example would be a
            personal consumption history feed.

        :param medium: the medium, as described above
        :returns the medium string
        '''
        if medium:
            ensure_format(
                {'medium': medium}, set(['medium']), set(['medium']),
                {'medium': [
                    'podcast', 'podcastL',
                    'music', 'musicL',
                    'video', 'videoL',
                    'film', 'filmL',
                    'audiobook', 'audiobookL',
                    'newsletter', 'newsletterL',
                    'blog', 'blogL',
                    'mixed'
                ]}
            )
            node = xml_elem('{%s}%s' % (self.PC20_NS, 'medium'))
            node.text = medium
            self._nodes['medium'] = node
            self._pc20elem_medium = medium
        return self._pc20elem_medium

    def block(self, block=None, id=None, slug_override=False):
        '''This element allows a podcaster to express which platforms are
        allowed to publicly display this feed and its contents. In its basic
        form, it is a direct drop-in replacement for the <itunes:block> tag,
        but allows for greater flexibility by the inclusion of the id
        attribute and by including multiple copies of itself in the feed.

        Platforms should not ingest a feed for public display/use if their
        slug exists in the id of a yes block tag, or if an unbounded yes block
        tag exists (meaning block all public ingestion). Conversely, if a
        platform finds their slug in the id of a no block tag, they are free
        to ingest that feed for public display/usage.

        In plain language, the sequence of discovery an ingesting platform
        should use is as follows:

        - Does <podcast:block id="[myslug]">no</podcast:block> exist in this
        feed? Safe to ingest.
        - Does <podcast:block id="[myslug]">yes</podcast:block> exist in this
        feed? Do not ingest.
        - Does <podcast:block>yes</podcast:block> exist in this feed? Do not
        ingest.

        :param block: (requied) text value for block tag, must be yes/no
        :param id: (optional) A single entry from the service slug list.
            See https://github.com/Podcastindex-org/podcast-namespace/blob/main/serviceslugs.txt  # noqa: E501
        :param slug_override: (optional, default False) normally id is
            checked against the list of service slugs, and if you use
            an id not on the list, you get a ValueError, to catch typos.
            If you want to ignore the list (e.g. new service hasn't been
            added yet, or a private service), set slug_override=True and
            then you can use anything for id
        :returns: dict of block and (optionally) id
        '''
        return self._pc20elem_block


class Podcasting20EntryExtension(Podcasting20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.

    Tags that are only direct children of <item> go in this class.
    '''
    def __init__(self):
        super().__init__()

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
