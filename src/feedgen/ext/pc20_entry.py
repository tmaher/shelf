from feedgen.util import ensure_format, xml_elem
import sys  # noqa: F401
from .pc20 import (
    Pc20BaseExtension,
    PC20_NS,
    PC20_SOCIAL_PROTOCOLS,
    to_lower_camel_case
)


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
        self.__pc20_social_interact = None

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
        if (args or kwargs):
            ensures = {
                'allowed': ['url', 'type', 'language', 'rel'],
                'required': ['url', 'type']
            }
            self.__pc20_transcript = \
                self.simple_multi_helper(ensures, True, args, kwargs)
        return self.__pc20_transcript

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
        if (args or kwargs):
            ensures = {
                'allowed': ['url', 'type'],
                'required': ['url'],
                'defaults': {'type': 'application/json+chapters'}
            }
            self.__pc20_chapters = \
                self.simple_single_helper(ensures, args, kwargs)
        return self.__pc20_chapters

    def soundbite(self, *args, **kwargs):
        '''Points to one or more soundbites within a podcast episode. The
        intended use includes episodes previews, discoverability, audiogram
        generation, episode highlights, etc. It should be assumed that the
        audio/video source of the soundbite is the audio/video given in the
        item's <enclosure> element.

        Dict keys are as follows
            - soundbite (optional): This is a free form string from the
            podcast creator to specify a title for the soundbite. If the
            podcaster does not provide a value for the soundbite title, then
            leave the value blank, and podcast apps can decide to use the
            episode title or some other placeholder value in its place.
            Please do not exceed 128 characters for the node value or it may
            be truncated by aggregators.
            - startTime (required): The time where the soundbite begins
            - duration (required): How long is the soundbite (recommended
            between 15 and 120 seconds)

        :param: dict or array of dicts as described above
        :param replace: Add or replace old data. (default false)
        :return: List of transcript tags as dictionaries
        '''
        if (args or kwargs):
            ensures = {
                'allowed': ['soundbite', 'start_time', 'duration'],
                'required': ['start_time', 'duration']
            }
            self.__pc20_soundbite = \
                self.simple_multi_helper(ensures, True, args, kwargs)
        return self.__pc20_soundbite

    def season(self, *args, **kwargs):
        '''This element allows for identifying which episodes in a podcast
        are part of a particular "season", with an optional season name
        attached.

        :param season: (required) The node value is an integer, and
        represents the season "number". It is required.
        :param name: (optional) This is the "name" of the season. If this
        attribute is present, applications are free to not show the season
        number to the end user, and may use it simply for chronological
        sorting and grouping purposes. Please do not exceed 128 characters
        for the name attribute.
        :return: dict with the current season & name
        '''
        if (args or kwargs):
            ensures = {
                'allowed': ['season', 'name'],
                'required': ['season']
            }
            self.__pc20_season = \
                self.simple_single_helper(ensures, args, kwargs)
        return self.__pc20_season

    def episode(self, *args, **kwargs):
        '''This element exists largely for compatibility with the season tag.
        But, it also allows for a similar idea to what "name" functions as in
        that element.

        :param episode: (required) A decimal number. Numbering such as 100.5
        is acceptable if there was a special mini-episode published between
        two other episodes. In that scenario, the number would help with
        proper chronological sorting, while the display attribute could
        specify an alternate special "number" (a moniker) to display for the
        episode in a podcast player app UI.
        :param display (optional): If this attribute is present, podcast
        apps and aggregators are encouraged to show its value instead of the
        purely numerical node value. This attribute is a string. Please do
        not exceed 32 characters
        :return: dict with the current episode number & display
        '''
        if (args or kwargs):
            ensures = {
                'allowed': ['episode', 'display'],
                'required': ['episode']
            }
            self.__pc20_episode = \
                self.simple_single_helper(ensures, args, kwargs)
        return self.__pc20_episode

    def social_interact(self, *args, **kwargs):
        '''The socialInteract tag allows a podcaster to attach the url of a
        "root post" of a comment thread to an episode.

        This "root post" is treated as the canonical location of where the
        comments and discussion around this episode will take place. This
        can be thought of as the "official" social media comment space for
        this episode. If a protocol such as "activitypub" is used, or some
        other protocol that allows programmatic API access, these comments
        can be directly pulled into the app, and replies can be posted back
        to the thread from the app itself.

        If multiple socialInteract tags are given for an <item>, the priority
        attribute is strongly recommended to give the app an indication as to
        which comments to display first.

        This tag can also be used as a signal to platforms and apps that the
        podcaster does not want public comments shown alongside this episode.
        For this purpose a protocol value of "disabled" can be specified,
        with no other attributes or node value present.

        **NOTE** Due to an inconsistency in the spec, this library does not
        enforce requiring a uri attribute. While the spec's Attributes
        sectin does explicitly describe uri as required, the spec's Examples
        section also includes an example tag with 'protocol="disabled"'
        and no uri attribute.

        Dict keys are as follows. Only "protocol" is required
            - uri (optional): The uri/url of root post comment
            - protocol (required): The protocol in use for interacting with
            the comment root post.
            - account_id (optional): The account id (on the commenting
            platform) of the account that created this root post.
            - account_url (optional): The public url (on the commenting
            platform) of the account that created this root post.
            - priority (optional): When multiple socialInteract tags are
            present, this integer gives order of priority. A lower number
            means higher priority.

        :param: dict or array of dicts as described above
        :param replace: Add or replace old data. (default false)
        :return: List of social_interact tags as dictionaries
        '''
        if (args or kwargs):
            ensures = {
                'allowed': ['uri', 'protocol', 'account_id',
                            'account_url', 'priority'],
                'required': ['protocol'],
                'allowed_values': {'protocol': PC20_SOCIAL_PROTOCOLS}
            }
            self.__pc20_social_interact = \
                self.simple_multi_helper(ensures, True, args, kwargs)
        return self.__pc20_social_interact

    def simple_single_helper(self, ensures, l_args, kw_args):
        import inspect
        tag_name = inspect.stack()[1].function
        tag_name_camel = to_lower_camel_case(tag_name)
        attr_name = f"__pc20_{tag_name}"

        if (l_args and (kw_args or len(l_args) > 1)):
            raise ValueError(f"Too Many Args!\nl: {l_args}\nkw: {kw_args}\n")
        new_vals = l_args[0] if l_args else kw_args

        new_vals = ensure_format(
            new_vals,
            set(ensures['allowed']),
            set(ensures['required']),
            ensures.get('allowed_values', None),
            ensures.get('defaults', None)
        ).pop()

        node = xml_elem('{%s}%s' % (PC20_NS, tag_name_camel))
        node.text = new_vals.get(tag_name, None)
        for k, v in new_vals.items():
            if k == 'text':
                continue
            node.attrib[to_lower_camel_case(k)] = v

        self._nodes[tag_name] = node
        setattr(self, attr_name, new_vals)
        return getattr(self, attr_name)

    def simple_multi_helper(self, ensures, multi, l_args, kw_args):
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
            set(ensures['allowed']),
            set(ensures['required']),
            ensures.get('allowed_values', None),
            ensures.get('defaults', None)
        )

        if replace or (not getattr(self, attr_name, None)):
            nodes = []
            vals = []
        else:
            nodes = self._nodes[attr_name]
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

        self._nodes[tag_name] = nodes
        setattr(self, attr_name, vals)
        return getattr(self, attr_name)
