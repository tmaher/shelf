import lxml.etree  # noqa: F401
from feedgen.ext.base import BaseExtension
from feedgen.util import xml_elem, ensure_format

import uuid
import urllib
import re
from datetime import datetime, timezone
import email
import icalendar
import sys  # noqa: F401

PC20_NS = 'https://podcastindex.org/namespace/1.0'
PC20_NS_GUID_UUID = uuid.UUID('ead4c236-bf58-58c6-a2c6-a6b28d128cb6')
# Canonical list of service slugs is at...
# https://github.com/Podcastindex-org/podcast-namespace/blob/main/serviceslugs.txt
PC20_SERVICE_SLUGS = [
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
# Canonical list of social protocols is at...
# https://github.com/Podcastindex-org/podcast-namespace/blob/main/socialprotocols.txt
PC20_SOCIAL_PROTOCOLS = [
    'disabled', 'activitypub', 'twitter', 'lightning', 'bluesky'
]


def pc20_extend_ns():
    return {'podcast': PC20_NS}


def to_lower_camel_case(snake_str):
    if "_" not in snake_str:
        return snake_str  # fake snake!

    cs = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return snake_str[0].lower() + cs[1:]


def url_to_guid(url):
    '''Generate a Podcasting 2.0-compliant GUID from an URL.

    :param url: (REQUIRED) The podcast feed URL. It is OK to include
        the protocol (e.g. "https://" or "http://"). Protocol and any
        trailing slashes will be stripped off before computing v5 UUID.
        For example, "https://podnews.net/rss", "podews.net/rss/", and
        "podnews.net/rss" will all result in the same GUID.
    :returns: a UUIDv5 GUID, computed using the Podcasting 2.0 namespace
    '''
    s = urllib.parse.urlsplit(url)
    no_scheme_url = re.sub(
        r'/+\Z', '',
        ''.join([s.netloc, s.path, s.query, s.fragment])
    )
    return str(uuid.uuid5(PC20_NS_GUID_UUID, no_scheme_url))


def date_to_rfc2822(ts):
    if isinstance(ts, datetime):
        return email.utils.format_datetime(ts)
    elif (isinstance(ts, int) or isinstance(ts, float)):
        return email.utils.formatdate(ts)
    elif isinstance(ts, str):
        try:
            email.utils.parsedate_to_datetime(ts)
        except ValueError:
            return email.utils.format_datetime(
                datetime.fromisoformat(re.sub(r"Z\Z", "+00:00", ts))
            )
    else:
        raise ValueError("need datetime, unix timestamp, or string")

    return ts


def validate_guid(guid):
    try:
        guid == str(uuid.UUID(guid))
    except Exception as e:
        raise ValueError(f"GUID {guid} invalid - {type(e).__name__}: {e}")
    return guid


class Pc20BaseExtension(BaseExtension):
    '''Podcasting 2.0 extension. See the following for specs:

        * https://podcasting2.org/podcast-namespace
        * https://podcastindex.org/namespace/1.0

    Tags shared <channel> and <item> go here.
    '''
    def __init__(self):
        self._nodes = {}

        # shared tags (channel & item)
        self.__pc20_person = None
        self.__pc20_location = None
        self.__pc20_license = None
        self.__pc20_images = None
        self.__pc20_txt = None

        # complex tags
        # they may have their own children
        # *OR* have a parent other than channel or item

        self.__pc20_alternateEnclosure = None  # parent => item or liveItem; has children
        self.__pc20_source = None     # parent => alternateEnclosure
        self.__pc20_integrity = None  # parent => alternateEnclosure

        self.__pc20_podroll = None  # parent => channel; has children
        self.__pc20_remoteItem = None  # parent => channel or podcast:podroll or podcast:valueTimeSplit
        self.__pc20_value = None  # parent => channel or item; has children
        self.__pc20_valueRecipient = None  # parent => podcast:value or valueTimeSplit
        self.__pc20_valueTimeSplit = None  # parent => podcast:value; has children

        # NOTE - liveItem appears to be un-implemented anywhere beyond
        # the spec, so defer for now
        self.__pc20_liveItem = None  # parent => channel; has children
        self.__pc20_contentLink = None  # parent => podcast:liveItem

    def extend_ns(self):
        return pc20_extend_ns()

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

    def getset_simple(self, l_args, kw_args, ensures={}, multi=False):
        '''Generic method to set values for "simple" tags, that is...
            - tags that always have either <channel> or <item> as the parent
            - tags that have no child tags under them

        There is some slight magic happening here, as the tag name is not
        passed as an explicit argument. Instead, it is inferred via
        inspecting the call stack, and using the calling function's name.

        *NOTE* is a ValueError to pass non-empty values to *BOTH* of
        l_args and kw_args. Choose only one!

        :param l_args: list argument. For tags with multiple count
            (e.g. <podcast:socialInteract>), this accepts a list
            of multiple dicts. This is to allow the same calls syntax
            as the "author" tag in the base FeedGenerator class
        :param kw_args:  dict of the attributes & text value
            for the tag.
        :param ensures: a dict with four keys, to be used for the
            `feedgen.util.ensure_format()` method
        :param multi: a bool indicating if this tag may occur more
            than once
            count=multiple (multi => True) or
            count=single (multi => False). For example,
            <podcast:chapters> is count=single, and
            <podcast:socialInteract> is count=multiple
        '''
        import inspect
        tag_name = inspect.stack()[1].function
        tag_name_camel = to_lower_camel_case(tag_name)
        attr_name = f"__pc20_{tag_name}"
        replace = kw_args.pop('replace', False) if multi else True

        if (l_args and (kw_args or len(l_args) > 1)):
            raise ValueError(f"Too Many Args!\nl: {l_args}\nkw: {kw_args}\n")
        new_vals = l_args[0] if l_args else kw_args

        new_vals = ensure_format(
            new_vals,
            set(ensures.get('allowed', []) + ensures['required']),
            set(ensures['required']),
            ensures.get('allowed_values', None),
            ensures.get('defaults', None)
        )
        for attr, vfunc in ensures.get('validators', {}).items():
            for val in new_vals:
                if val.get(attr, None):
                    val[attr] = vfunc(val[attr])

        if replace or (not getattr(self, attr_name, None)):
            nodes = []
            vals = []
        else:
            nodes = self._nodes[tag_name]
            vals = getattr(self, attr_name)

        for val in new_vals:
            node = xml_elem('{%s}%s' % (PC20_NS, tag_name_camel))
            node.text = val.get(tag_name, None)
            for k, v in val.items():
                if k == tag_name:
                    continue
                node.attrib[to_lower_camel_case(k)] = v
            nodes.append(node)
            vals.append(val)
        if not multi:
            nodes = nodes[0]
            vals = vals[0]

        self._nodes[tag_name] = nodes
        setattr(self, attr_name, vals)
        return getattr(self, attr_name)


class Pc20Extension(Pc20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.

    Tags that are only direct children of <channel> go in this class
    '''
    def __init__(self):
        super().__init__()
        self.__pc20_block = None
        self.__pc20_funding = None
        self.__pc20_guid = None
        self.__pc20_locked = None
        self.__pc20_medium = None
        self.__pc20_podping = None
        self.__pc20_trailer = None
        self.__pc20_updateFrequency = None

    def locked(self, *args, **kwargs):
        '''This tag may be set to yes or no. The purpose is to tell other
        podcast hosting platforms whether they are allowed to import this feed.
        A value of yes means that any attempt to import this feed into a new
        platform should be rejected.

        :param locked: must be "yes" or "no"
        :param owner: (optional) The owner attribute is an email address that
            can be used to verify ownership of this feed during move and
            import operations. This could be a public email or a virtual email
            address at the hosting provider that redirects to the owner's true
            email address.
        :returns: dict of locked & owner email
        '''
        if (args or kwargs):
            ensures = {
                'required': ['locked'],
                'allowed': ['owner'],
                'allowed_values': {'locked': ['yes', 'no']}
            }
            self.__pc20_locked = \
                self.getset_simple(args, kwargs, ensures=ensures)
        return self.__pc20_locked

    def funding(self, *args, **kwargs):
        '''This tag lists possible donation/funding links for the podcast.
        The content of the tag is the recommended string to be used with
        the link.

        :param url: (REQUIRED) The URL to be followed to fund the podcast.
        :param funding: (optional) This is a free form string supplied by the
        creator which they expect to be displayed in the app next to the link.
        Please do not exceed 128 characters for the node value or it may be
        truncated by aggregators.
        :param replace: (optional) Add or replace old data. (default false)
        :returns List of funding tags as dictionaries
        '''
        if (args or kwargs):
            ensures = {
                'required': ['url'],
                'allowed': ['funding']
            }
            self.__pc20_funding = \
                self.getset_simple(args, kwargs, ensures=ensures, multi=True)
        return self.__pc20_funding

    def trailer(self, *args, **kwargs):
        '''This element is used to define the location of an audio or video
        file to be used as a trailer for the entire podcast or a specific
        season. There can be more than one trailer present in the channel
        of the feed. This element is basically just like an <enclosure> with
        the extra pubdate and season attributes added.

        If there is more than one trailer tag present in the channel, the
        most recent one (according to its pubdate) should be chosen as the
        preview by default within podcast apps.

        :param url: (REQUIRED) This is a url that points to the audio or
            video file to be played. This attribute is a string.
        :param pubdate: (REQUIRED) The date the trailer was published.
            This attribute is an RFC2822 formatted date string.
            **IMPLEMENTATION NOTE**: this library will additionally accept
            DateTime objects, ISO8601 format strings, and Unix timestamps.
            Those formats will be converted to RFC2822 format date strings,
            defaulting to UTC unless otherwise specified.
        :param length: (optional) The length of the file in bytes. This
            attribute is a number.
        :param type: (optional) The mime type of the file. This attribute
            is a string.
        :param season: (optional) If this attribute is present it specifies
            that this trailer is for a particular season number. This
            attribute is a number.
        :param replace: Add or replace old data. (default false)
        :returns: List of trailer tags as dictionaries
        '''

        if (args or kwargs):
            ensures = {
                'required': ['url', 'pubdate'],
                'allowed': ['length', 'type', 'season', 'trailer'],
                'validators': {'pubdate': date_to_rfc2822}
            }
            self.__pc20_trailer = \
                self.getset_simple(args, kwargs, ensures=ensures, multi=True)
        return self.__pc20_trailer

    def guid(self, *args, **kwargs):
        '''This element is used to declare a unique, global identifier for a
        podcast. The value is a UUIDv5, and is easily generated from the RSS
        feed url, using helper feedgen.ext.pc20.url_to_guid()

        A podcast gets assigned a podcast:guid once in its lifetime using its
        current feed url (at the time of assignment) as the seed value. That
        GUID is then meant to follow the podcast from then on, for the
        duration of its life, even if the feed url changes. This means that
        when a podcast moves from one hosting platform to another, *YOU* are
        responsible for using the old GUID.

        :param guid: a UUIDv5 string, prefereably computed using
            feedgen.ext.pc20.url_to_guid()
        :returns: dictionary containing the GUID string
        '''
        if (args or kwargs):
            ensures = {
                'required': ['guid'],
                'validators': {'guid': validate_guid}
            }
            self.__pc20_guid = \
                self.getset_simple(args, kwargs, ensures=ensures)
        return self.__pc20_guid

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
            node = xml_elem('{%s}%s' % (PC20_NS, 'medium'))
            node.text = medium
            self._nodes['medium'] = node
            self.__pc20_medium = medium
        return self.__pc20_medium

    def block(self, blocks=None, slug_override=False, replace=False):
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

        dict keys are as follows. block is required
            - block (required): text value of node, must be yes or no
            - id (optional): A single entry from the service slug list, see
            https://github.com/Podcastindex-org/podcast-namespace/blob/main/serviceslugs.txt

        :param blocks: dict or array of dicts as described above
        :param slug_override: (optional, default False) normally id is
            checked against the list of service slugs, and if you use
            an id not on the list, you get a ValueError, to catch typos.
            If you want to ignore the list (e.g. new service hasn't been
            added yet, or a private service), set slug_override=True and
            then you can use anything for id
        :param replace: Add or replace old data. (default false)
        :returns: list of dicts of block and (optionally) id
        '''
        if blocks != []:
            valid_values = {'block': ['yes', 'no']}
            if not slug_override:
                valid_values['id'] = PC20_SERVICE_SLUGS
            blocks = ensure_format(
                blocks,
                set(['block', 'id']),
                set(['block']),
                valid_values
            )
            if replace or (not self._nodes.get('block')):
                block_nodes = []
                vals = []
            else:
                block_nodes = self._nodes['block']
                vals = self.__pc20_block
            for block in blocks:
                val = block
                node = xml_elem('{%s}%s' % (PC20_NS, 'block'))
                node.text = val['block']
                if val['id']:
                    node.attrib['id'] = val['id']
                block_nodes.append(node)
                vals.append(val)
            self._nodes['block'] = block_nodes
            self.__pc20_block = vals
        return self.__pc20_block

    def update_frequency(self, uf=None):
        ''' This element allows a podcaster to express their intended release
        schedule as structured data and text.

        dict keys are as follows. text is required

            - text: a free-form string, which might be displayed alongside
            other information about the podcast. Please do not exceed 128
            characters for the node value or it may be truncated by
            aggregators.
            - dtstart (optional): The date or datetime the recurrence rule
            begins as an ISO8601-fornmatted
            (https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date/toISOString)
            string. If the rrule contains a value for COUNT, then this
            attribute is required. If the rrule contains a value for UNTIL,
            then the value of this attribute must be formatted to the same
            date/datetime standard.
            - complete (optional): Boolean specifying if the podcast has no
            intention to release further episodes. If not set, this should be
            assumed to be false.
            - rrule (optional, recommended): A recurrence rule as defined
            in iCalendar RFC 5545 Section 3.3.10.

        :param uf: dict as described above
        :returns: the previously set dict
        '''
        if uf:
            if (not isinstance(uf, dict)):
                raise ValueError("only single dictionary allowed")
            val = ensure_format(
                uf,
                set(['text', 'dtstart', 'complete', 'rrule']),
                set(['text']),
                {'complete': ['true', 'false']}
            )[0]
            node = xml_elem('{%s}%s' % (PC20_NS, 'updateFrequency'))
            node.text = val['text']
            if val.get('dtstart'):
                # run dtstart through iso8601 parser to validate syntax
                # The podcasting 2.0 spec specifically notes
                # that they use the restricted JavaScript subset of
                # ISO 8601 (always miliseconds, always UTC), so
                # forcibly convert to that
                #
                # "Z" as timezone was only added in python 3.11 :(
                ts = re.sub(r"Z\Z", "+00:00", uf['dtstart'])
                dt_parsed = datetime.fromisoformat(ts)
                dt_parsed = dt_parsed.astimezone(timezone.utc)
                # if .isoformat() throws an exception here about timespec,
                # upgrade to python 3.6 or later. python 3.5 is EOL
                ts = dt_parsed.isoformat(timespec='milliseconds')
                val['dtstart'] = re.sub(r"\+00:00\Z", "Z", ts)
                node.attrib['dtstart'] = val['dtstart']
            if val.get('rrule'):
                # run rrule through the iCalendar parser to validate syntax
                icalendar.Event.from_ical(
                    'BEGIN:VTODO\nDTSTART:19700101T000000Z\n'
                    f"RRULE:{val['rrule']}\nEND:VTODO\n"
                )
                node.attrib['rrule'] = val['rrule']
            if val.get('complete'):
                node.attrib['complete'] = val['complete']
            self._nodes['update_frequency'] = node
            self.__pc20_updateFrequency = val

        return self.__pc20_updateFrequency

    def podping(self, *args, **kwargs):
        '''This element allows feed owners to signal to aggregators that the
        feed sends out Podping notifications when changes are made to it,
        reducing the need for frequent speculative feed polling.

        :param uses_podping: str - either "true" or "false"
        :param replace: Add or replace old data. (default false)
        '''
        if (args or kwargs):
            ensures = {
                'required': ['uses_podping'],
                'allowed_values': {'uses_podping': ['true', 'false']}
            }
            self.__pc20_podping = \
                self.getset_simple(args, kwargs, ensures=ensures)
        return self.__pc20_podping
