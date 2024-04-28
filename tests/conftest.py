import pytest
import feedgen
import feedgen.ext
import pkgutil
from lxml import etree

# FIXME: feedgen is not a namespaced package, hence the path manipulation
# Remove before submitting PR to upstream
feedgen.__path__ = \
    pkgutil.extend_path(feedgen.__path__, feedgen.__name__)
feedgen.ext.__path__ = \
    pkgutil.extend_path(feedgen.ext.__path__, feedgen.ext.__name__)
from feedgen.ext.pc20 import (  # type: ignore # noqa: E402
    PC20_NS, pc20_extend_ns, to_lower_camel_case
 )


class Helpers:
    @staticmethod
    def simple_single(fg, tag_func, tag_name, cases, parent="channel"):
        tag_name_camel = to_lower_camel_case(tag_name)
        open_dtag = f"<data xmlns:podcast=\"{PC20_NS}\">"
        close_dtag = "</data>"

        for case in cases:
            spec_xml = open_dtag + case['spec'] + close_dtag
            spec_root = etree.fromstring(spec_xml)

            tag_func(case['test'])
            assert tag_func() == case['test']

            test_xml = fg.rss_str().decode('UTF-8')
            test_root = etree.XML(test_xml.encode('UTF-8'))

            for attr in case['test'].keys():
                attr_camel = to_lower_camel_case(attr)
                xp_frag = "text()" if attr == tag_name else f"@{attr_camel}"

                test_attr = test_root.xpath(
                    f"/rss/{parent}/podcast:{tag_name_camel}/{xp_frag}",
                    namespaces=pc20_extend_ns()
                )
                spec_attr = spec_root.xpath(
                    f"/data/podcast:{tag_name_camel}/{xp_frag}",
                    namespaces=pc20_extend_ns()
                )
                assert spec_attr == test_attr

            test_kid = etree.XML(fg.rss_str())\
                .xpath(
                    f"//podcast:{tag_name_camel}",
                    namespaces=pc20_extend_ns()
                )[0]
            test_dtag = etree.fromstring(open_dtag + close_dtag)
            test_dtag.append(test_kid)
            test_xml = etree.tostring(test_dtag).decode('UTF-8')

            spec_xml_canon = etree.canonicalize(spec_xml)
            test_xml_canon = etree.canonicalize(test_xml)
            assert spec_xml_canon == test_xml_canon

    @staticmethod
    def simple_multi(fg, tag_func, tag_name, cases):
        tag_name_camel = to_lower_camel_case(tag_name)
        open_dtag = f"<data xmlns:podcast=\"{PC20_NS}\">"
        close_dtag = "</data>"

        spec_xml = open_dtag + \
            "".join(map(lambda x: x['spec'], cases)) + close_dtag

        test_cases = list(map(lambda x: x['test'], cases))

        tag_func(**test_cases[0], replace=True)
        assert tag_func() == [test_cases[0]]
        for test_case in test_cases[1:]:
            tag_func(**test_case, replace=False)
        assert tag_func() == test_cases

        tag_func(**test_cases[0], replace=True)
        assert tag_func() == [test_cases[0]]
        for test_case in test_cases[1:]:
            tag_func(**test_case)
        assert tag_func() == test_cases

        tag_func(test_cases, replace=True)
        assert tag_func() == test_cases
        test_kids = etree.XML(fg.rss_str())\
            .xpath(
                f"//podcast:{tag_name_camel}",
                namespaces=pc20_extend_ns()
            )
        test_dtag = etree.fromstring(open_dtag + close_dtag)
        for kid in test_kids:
            test_dtag.append(kid)
        test_xml = etree.tostring(test_dtag).decode('UTF-8')

        spec_xml_canon = etree.canonicalize(spec_xml)
        test_xml_canon = etree.canonicalize(test_xml)
        assert spec_xml_canon == test_xml_canon


@pytest.fixture
def helper():
    return Helpers
