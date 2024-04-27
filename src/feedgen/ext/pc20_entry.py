import sys  # noqa: F401
from .pc20 import Pc20BaseExtension, PC20_NS
from feedgen.util import ensure_format, xml_elem


def to_lower_camel_case(snake_str):
    cs = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return snake_str[0].lower() + cs[1:]


class Pc20EntryExtension(Pc20BaseExtension):
    '''Podcasting 2.0 Elements extension for podcasts.

    Tags that are only direct children of <item> go in this class.
    '''
    def __init__(self):
        super().__init__()
        self.__pc20_transcript = None
        self.__pc20_chapters = None
        self.__pc20_soundbite = None
        self.__pc20_season = None
        self.__pc20_episode = None
        self.__pc20_socialInteract = None
        self.__pc20_person = None
        self.__pc20_location = None
        self.__pc20_license = None
        self.__pc20_images = None
        self.__pc20_txt = None

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

    def transcript(self, *args, **kwargs):
        '''This tag is used to link to a transcript or closed captions file.
        Multiple tags can be present for multiple transcript formats.

        Detailed file format information and example files are at
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/transcripts/transcripts.md

        Dict keys are as follows
            - url (required): URL of the podcast transcript.
            - type (required): Mime type of the file such as text/plain,
            text/html, text/vtt, application/json, application/x-subrip
            - language (optional): The language of the linked transcript.
            If there is no language attribute given, the linked file is
            assumed to be the same language that is specified by the
            RSS <language> element.
            - rel (optional): If the rel="captions" attribute is present,
            the linked file is considered to be a closed captions file,
            regardless of what the mime type is. In that scenario, time
            codes are assumed to be present in the file in some capacity.

        :param: dict or array of dicts as described above
        :param replace: Add or replace old data. (default false)
        :return: List of transcript tags as dictionaries
        '''
        helper_args = {'_ensure': {
            'allowed': ['url', 'type', 'language', 'rel'],
            'required': ['url', 'type']
        }}
        helper_args.update(kwargs)
        self.simple_multi_helper(args, helper_args)

    def chapters(self, *args, **kwargs):
        '''Links to an external file (see example file) containing chapter
        data for the episode. See
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/chapters/jsonChapters.md
        for a description of the chapter file syntax. And, see
        https://github.com/Podcastindex-org/podcast-namespace/blob/main/chapters/example.json
        for a real world example.

        Benefits with this approach are that chapters do not require
        altering audio files, and the chapters can be edited after publishing,
        since they are a separate file that can be requested on playback (or
        cached with download). JSON chapter information also allows chapters
        to be displayed by a wider range of playback tools, including web
        browsers (which typically have no access to ID3 tags), thus greatly
        simplifying chapter support; and images can be retrieved on playback,
        rather than bloating the filesize of the audio. The data held is
        compatible with normal ID3 tags, thus requiring no additional work
        for the publisher.

        :param url: *REQUIRED* The URL where the chapters file is located.
        :param type: Mime type of file. If not specified, this library will
        use assume 'application/json+chapters'.
        :returns: the entry element
        '''

        if (args and len(args) > 1) or (args and kwargs):
            raise ValueError("ONE ARG ONLY")
        val = args[0] if (args and isinstance(args[0], dict)) else kwargs
        if val != {}:
            val = ensure_format(
                val,
                set(['url', 'type']),
                set(['url']),
                {},
                {'type': 'application/json+chapters'}
            )[0]
            node = xml_elem('{%s}%s' % (PC20_NS, 'chapters'))
            for k, v in val.items():
                node.attrib[k] = v
            self._nodes['chapters'] = node
            self.__pc20_chapters = val
        return self.__pc20_chapters

    def soundbite(self, *args, **kwargs):
        '''Points to one or more soundbites within a podcast episode. The
        intended use includes episodes previews, discoverability, audiogram
        generation, episode highlights, etc. It should be assumed that the
        audio/video source of the soundbite is the audio/video given in the
        item's <enclosure> element.

        Dict keys are as follows
            - text (optional): This is a free form string from the podcast
            creator to specify a title for the soundbite. If the podcaster
            does not provide a value for the soundbite title, then leave the
            value blank, and podcast apps can decide to use the episode title
            or some other placeholder value in its place. Please do not
            exceed 128 characters for the node value or it may be truncated
            by aggregators.
            - startTime (required): The time where the soundbite begins
            - duration (required): How long is the soundbite (recommended
            between 15 and 120 seconds)

        :param: dict or array of dicts as described above
        :param replace: Add or replace old data. (default false)
        :return: List of transcript tags as dictionaries
        '''
        helper_args = {'_ensure': {
            'allowed': ['text', 'start_time', 'duration'],
            'required': ['start_time', 'duration']
        }}
        helper_args.update(kwargs)
        self.simple_multi_helper(args, helper_args)

    def simple_multi_helper(self, l_args, kw_args):
        import inspect
        tag_name = inspect.stack()[1][3]
        attr_name = f"__pc20_{tag_name}"
        ensure = kw_args.pop('_ensure')
        replace = kw_args.pop('replace', False)

        if not (l_args or kw_args or replace):
            return getattr(self, attr_name, None)
        if (l_args and (kw_args or len(l_args) > 1)):
            raise ValueError("Too Many Args!")
        new_vals = l_args[0] if l_args else kw_args

        new_vals = ensure_format(
            new_vals,
            set(ensure['allowed']),
            set(ensure['required']),
            ensure.get('allowed_values', None),
            ensure.get('defaults', None)
        )
        if replace or (not getattr(self, attr_name, None)):
            nodes = []
            vals = []
        else:
            nodes = self._nodes[attr_name]
            vals = getattr(self, attr_name)
        for val in new_vals:
            node = xml_elem('{%s}%s' % (PC20_NS, tag_name))
            node.text = val.pop('text', None)
            for k, v in val.items():
                node.attrib[to_lower_camel_case(k)] = v
            nodes.append(node)
            vals.append(val)
        self._nodes[tag_name] = nodes
        setattr(self, attr_name, vals)

        return getattr(self, attr_name)
