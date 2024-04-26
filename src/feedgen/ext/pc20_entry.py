# import feedgen
# import feedgen.ext
# import pkgutil
import sys  # noqa: F401
from .pc20 import Pc20BaseExtension

# FIXME: feedgen is not a namespaced package, hence the path manipulation
# Remove before submitting PR to upstream
# feedgen.__path__ = \
#    pkgutil.extend_path(feedgen.__path__, feedgen.__name__)
# feedgen.ext.__path__ = \
#    pkgutil.extend_path(feedgen.ext.__path__, feedgen.ext.__name__)
# from feedgen.ext.pc20 import Pc20BaseExtension, PC20_NS  # type: ignore # noqa: E402 E501
# from feedgen.util import xml_elem, ensure_format


class Pc20EntryExtension(Pc20BaseExtension):
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
