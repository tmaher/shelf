from feedgen.ext.base import BaseExtension
from feedgen.util import xml_elem


class Podcasting20Extension(BaseExtension):
    '''Podcasting 2.0 extension
    See https://podcasting2.org/podcast-namespace
    '''

    def __init__(self):
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
        return {'podcast': 'https://podcastindex.org/namespace/1.0'}

    def _extend_xml(self, xml_element):
        '''Extend xml_element with set Podcasting 2.0 fields.

        :param xml_element: etree element
        '''
        PC20ELEMENTS_NS = 'https://podcastindex.org/namespace/1.0'

        for elem in [
            'transcript',
            'chapters',
            'podroll',
            'locked',
            'funding',
            'soundbite',
            'person',
            'location',
            'season',
            'episode',
            'trailer',
            'license',
            'alternateEnclosure',
            'source',
            'integrity',
            'guid',
            'value',
            'valueRecipient',
            'medium',
            'images',
            'liveItem',
            'contentLink',
            'socialInteract',
            'block',
            'txt',
            'remoteItem',
            'updateFrequency',
            'podping',
            'valueTimeSplit'
        ]:
            if hasattr(self, '_pc20elem_%s' % elem):
                for val in getattr(self, '_pc20elem_%s' % elem) or []:
                    node = xml_elem('{%s}%s' % (PC20ELEMENTS_NS, elem),
                                    xml_element)
                    node.text = val

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
