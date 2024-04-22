from feedgen.ext.base import BaseExtension
from feedgen.util import xml_elem
# import sys


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

    def locked(self, locked=None, owner=None):
        '''This tag may be set to yes or no. The purpose is to tell other
        podcast hosting platforms whether they are allowed to import this feed.
        A value of yes means that any attempt to import this feed into a new
        platform should be rejected.

        :param locked: must be "yes" or "no"
        :param owner: (optional) The owner attribute is an email address that
        can be used to verify ownership of this feed during move and import
        operations. This could be a public email or a virtual email address
        at the hosting provider that redirects to the owner's true email
        address.
        :returns: dict of locked & owner email
        '''
        if locked is not None:
            if locked not in ('yes', 'no'):
                raise ValueError("Locked may only be 'yes' or 'no'")
            val = {'locked': locked}
            node = xml_elem('{%s}%s' % (self.PC20_NS, 'locked'))
            node.text = locked
            if owner:
                node.attrib['owner'] = owner
                val['owner'] = owner

            self._pc20elem_locked = val
            self._nodes['locked'] = node

        return self._pc20elem_locked

    def funding(self, fundings=[]):
        '''This tag lists possible donation/funding links for the podcast.
        The content of the tag is the recommended string to be used with
        the link.

        :param funding: array of dicts with two elements: 'text' and 'url'.
        'text' is a free form string supplied by the creator which they
        expect to be displayed in the app next to the link. Please do not
        exceed 128 characters for the node value or it may be truncated by
        aggregators. 'url' is the URL to be followed to fund the podcast.
        '''
        if fundings != []:
            if not isinstance(fundings, list):
                raise ValueError("funding takes an array of dicts")
            funding_nodes = []
            vals = []
            for fund in fundings:
                if not isinstance(fund, dict):
                    raise ValueError("funding takes an array of dicts")
                if (not fund['url']) or (not fund['text']):
                    raise ValueError("url and text are both required")
                val = {'url': fund['url'], 'text': fund['text']}
                vals.append(val)
                node = xml_elem('{%s}%s' % (self.PC20_NS, 'funding'))
                node.text = fund['text']
                node.attrib['url'] = fund['url']
                funding_nodes.append(node)
            self._nodes['funding'] = funding_nodes
            self._pc20elem_funding = vals

        return self._pc20elem_funding


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
