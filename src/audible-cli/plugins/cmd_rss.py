"""Generate rss feed info for library

This is a proof-of-concept and for testing purposes only.

No error handling.
Need further work. Some options do not work or options are missing.

Needs at least ffmpeg 4.4
"""

import json
# import operator
import pathlib
# import re
import subprocess  # noqa: S404
import typing as t
from enum import Enum
# from functools import reduce
from glob import glob
# from shlex import quote
from shutil import which
import podgen
from datetime import timedelta
import dateutil
from podgen import Podcast, Episode, Media, Person, Category
from rfc3986 import normalize_uri, is_valid_uri
# from pprint import pprint
# import xml.etree.ElementTree as ElementTree
# from xml.dom import minidom

import click
from click import echo, secho

from audible_cli.decorators import pass_session
from audible_cli.exceptions import AudibleCliException


class ChapterError(AudibleCliException):
    """Base class for all chapter errors."""


class SupportedFiles(Enum):
    AAX = ".aax"
    AAXC = ".aaxc"
    M4A = ".m4b"
    M4B = ".m4a"
    MP3 = ".mp3"
    MP4 = ".mp4"
    MOV = ".mov"

    @classmethod
    def get_supported_list(cls):
        return list(set(item.value for item in cls))

    @classmethod
    def is_supported_suffix(cls, value):
        return value in cls.get_supported_list()

    @classmethod
    def is_supported_file(cls, value):
        return pathlib.PurePath(value).suffix in cls.get_supported_list()


def _get_feed_url(
    feed_url,
    url_prefix: str,
    outfile: str
) -> str:
    if feed_url:
        return feed_url
    outfile_base = pathlib.Path(outfile).name
    return f"{url_prefix}{outfile_base}"


def _get_website(
    website,
    url_prefix: str
) -> str:
    website = website if website else url_prefix
    if not is_valid_uri(
            website,
            require_scheme=True,
            require_authority=True,
            require_path=True
            ):
        raise click.BadOptionUsage(
                website,
                f"homepage {website} is invalid - needs to be an URL"
        )
    return website


def _get_image(
    image: str,
    url_prefix: str
) -> str:
    if is_valid_uri(
            image,
            require_scheme=True,
            require_authority=True,
            require_path=True
            ):
        return image

    return f"{url_prefix}{image}"


def _get_url_prefix(
        prefix: str
) -> str:
    if not is_valid_uri(prefix, require_path=True) \
            and is_valid_uri(prefix):
        prefix += "/"

    if not is_valid_uri(
            prefix,
            require_scheme=True,
            require_authority=True,
            require_path=True
            ):
        raise click.BadOptionUsage(
                prefix,
                f"url prefix {prefix} is invalid - needs to be an URL"
        )

    return normalize_uri(prefix)


def _get_input_files(
    files: t.Union[t.Tuple[str], t.List[str]],
    recursive: bool = True
) -> t.List[pathlib.Path]:
    filenames = []
    for filename in files:
        # if the shell does not do filename globbing
        expanded = list(glob(filename, recursive=recursive))

        if (
            len(expanded) == 0
            and '*' not in filename
            and not SupportedFiles.is_supported_file(filename)
        ):
            raise (click.BadParameter(
                "{filename}: file not found or supported."))

        expanded_filter = filter(
            lambda x: SupportedFiles.is_supported_file(x), expanded
        )
        expanded = list(
            map(lambda x: pathlib.Path(x).resolve(), expanded_filter)
        )
        filenames.extend(expanded)

    return filenames


class EpisodeCreator:
    def __init__(
        self,
        cast: podgen.Podcast,
        file: pathlib.Path,
        url_prefix: str,
        overwrite: bool
    ) -> None:
        self._cast = cast
        self._source = file
        self._url_prefix = url_prefix
        self._overwrite = overwrite

    def do_probe(self):
        base_cmd = [
            "ffprobe",
            "-show_format",
            "-output_format",
            "json",
            "-i",
            str(self._source)
        ]
        child_result = subprocess.run(base_cmd, capture_output=True)
        if child_result.returncode != 0:
            secho("f Skip {outfile}: ffprobe failed")
            return

        try:
            probe_dict = json.loads(child_result.stdout)
        except json.JSONDecodeError:
            secho("f skip {outfile} json parse error from ffprobe")

        self._probe = probe_dict["format"]
        self._tags = self._probe["tags"]

        return

    def do_ep(self):
        pubdate = dateutil.parser.isoparse(self._tags["creation_time"])
        file_name = pathlib.Path(self._source).name
        self._episode = Episode(
            title=self._tags["title"],
            summary=self._tags["comment"],
            publication_date=pubdate,
            authors=[Person(self._tags["artist"])],
            withhold_from_itunes=True
        )
        # ep_url = f"{self._url_prefix}{file_name}"
        # print(f"about to media-ify {ep_url}")

        self._episode.media = Media(
            url=f"{self._url_prefix}{file_name}",
            size=self._probe["size"],
            duration=timedelta(seconds=float(self._probe["duration"]))
        )

    def run(self):
        self.do_probe()
        # pprint(self._probe)
        self.do_ep()
        # xmlstr = minidom.parseString(
        #    ElementTree.tostring(self._episode.rss_entry())
        # ).toprettyxml(indent="  ")
        # print(xmlstr)
        echo(f"adding {self._source}")
        self._cast.add_episode(self._episode)

@click.command("rss")  # noqa: E302
@click.argument("files", nargs=-1)
@click.option(
    "--name",
    type=str,
    required=True,
    help="Name of podcast"
)
@click.option(
    "--desc",
    "--description",
    type=str,
    required=True,
    help="Description"
)
@click.option(
    "--website",
    type=str,
    help="podcast homepage - if not specified, defaults to --url-prefix"
)
@click.option(
    "--explicit",
    is_flag=True,
    default=True,
    show_default=True,
    help="Listener discretion is advised"
)
@click.option(
    "--image",
    type=str,
    required=True,
    help="URL for the artwork image, e.g. https://example.com/cast.jpg"
)
@click.option(
    "--category",
    type=str,
    default="Arts",
    show_default=True,
    help="iTunes top level category, see "
    "https://podcasters.apple.com/support/1691-apple-podcasts-categories"
)
@click.option(
    "--subcategory",
    type=str,
    default="Books",
    show_default=True,
    help="iTunes sub category, see "
    "https://podcasters.apple.com/support/1691-apple-podcasts-categories"
)
@click.option(
    "--url-prefix",
    required=True,
    help="""
    URL prefix for the podcast. If you have file foo.mp3 and it will
    be fetched as https://example.com/cast/foo.mp3 then set url-prefix to
    https://example.com/cast/

    Note - don't forget to include the trailing "/"
    """
)
@click.option(
    "--outfile",
    "-o",
    type=str,
    default=pathlib.Path.cwd() / "rss",
    help="Folder where the decrypted files should be saved.",
    show_default=True
)
@click.option(
    "--feed-url",
    type=str,
    help="""
    URL where rss will be served from, i.e. the URL you will add to podcast
    clients. Default is url-prefix plus the outfile, e.g. if your
    url-prefix is https://example.com/cast/ and outfile is rss,
    default feed-url is https://example.com/cast/rss
    """
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing files.")
@click.option(
    "--all",
    "-a",
    "all_",
    is_flag=True,
    default=False,
    help="RSS-ify all eligible media files in current dir ({0})".format(
        ",".join(SupportedFiles.get_supported_list())
    )
)
@pass_session
def cli(
    session,
    name: str,
    desc: str,
    website: str,
    explicit: bool,
    url_prefix: str,
    image: str,
    category: str,
    subcategory: str,
    feed_url: str,
    files: str,
    outfile: str,
    all_: bool,
    overwrite: bool,
):
    """Generate RSS File"""

    # raise RuntimeError("zoinks! add pubdate library support before merging")
    if not which("ffprobe"):
        ctx = click.get_current_context()
        ctx.fail("ffprobe not found")

    if all_:
        if files:
            raise click.BadOptionUsage(
                "all",
                "If using `--all`, no FILES arguments can be used."
            )
        files = [
            f"*{suffix}" for suffix in SupportedFiles.get_supported_list()
        ]

    if pathlib.Path(outfile).exists() and not (overwrite):
        raise click.BadOptionUsage(
            "outfile",
            f"sorry --outfile {outfile} already exists"
        )

    url_prefix = _get_url_prefix(prefix=url_prefix)
    website = _get_website(website=website, url_prefix=url_prefix)
    image = _get_image(image=image, url_prefix=url_prefix)
    feed_url = _get_feed_url(
        feed_url=feed_url,
        url_prefix=url_prefix,
        outfile=outfile
    )

    print(f"creating podcast site {website}...")

    cast = Podcast(
        name=name,
        description=desc,
        website=website,
        explicit=explicit,
        image=image,
        feed_url=feed_url,
        category=Category(category, subcategory),
    )

    files = _get_input_files(files, recursive=True)
    for file in files:
        EpisodeCreator(
            cast=cast,
            file=file,
            url_prefix=url_prefix,
            overwrite=overwrite
        ).run()

    cast.rss_file(outfile)
    print(f"feed saved to {outfile}")
    True
