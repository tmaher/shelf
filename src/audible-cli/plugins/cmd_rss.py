"""Generate rss feed info for library

This is a proof-of-concept and for testing purposes only.

No error handling.
Need further work. Some options do not work or options are missing.

Needs at least ffmpeg 4.4
"""

import json
import pathlib
import re
import subprocess  # noqa: S404
import typing as t
from enum import Enum
from glob import glob
from shutil import which
from datetime import timedelta
import dateutil
import podgen
from rfc3986 import normalize_uri, is_valid_uri

import click
from click import echo, secho

from audible_cli.decorators import (
    pass_client,
    pass_session,
    bunch_size_option,
    end_date_option,
    start_date_option,
)

from audible_cli.exceptions import AudibleCliException
from audible_cli.models import Library


class ChapterError(AudibleCliException):
    """Base class for all chapter errors."""


class SupportedFiles(Enum):
    M4B = ".m4a"
    MP3 = ".mp3"
    MP4 = ".mp4"

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


async def _get_library_info(session, client):
    bunch_size = session.params.get("bunch_size")
    start_date = session.params.get("start_date")
    end_date = session.params.get("end_date")

    library = await Library.from_api_full_sync(
        client,
        response_groups=",".join([
            "contributors",
            "product_attrs",
            "product_desc",
        ]),
        bunch_size=bunch_size,
        start_date=start_date,
        end_date=end_date
    )
    await library.resolve_podcats(start_date=start_date, end_date=end_date)

    books = {}
    for book in library:
        books[book.asin] = {
            'asin': book.asin,
            'title': book.title,
            'authors':
                ", ".join([i["name"] for i in (book.authors or [])]),
            'narrators':
                ", ".join([i["name"] for i in (book.narrators or [])]),
            'date_added': book.purchase_date,
        }

    return books


class EpisodeCreator:
    def __init__(
        self,
        file: pathlib.Path,
        url_prefix: str,
        overwrite: bool,
        make_public: bool
    ):
        self._source = file
        self._url_prefix = url_prefix
        self._overwrite = overwrite
        self._make_public = make_public
        self._asin = None
        self._do_probe()
        self._create_podgen_episode()

    @property
    def asin(self) -> str:
        if (not self._asin):
            try:
                self._asin = self._tags['episode_id']
            except KeyError:
                file_name = pathlib.Path(self._source).name
                match = re.search(r'\A([A-Z0-9]{10})_', file_name)
                if (not match):
                    raise RuntimeError("Unable to determine ASIN")
                try:
                    self._asin = match(1)
                except IndexError:
                    raise RuntimeError("Unable to determine ASIN")

        return self._asin

    @property
    def title(self) -> str:
        return self._tags['title']

    @property
    def source(self) -> str:
        return self._source

    @property
    def podgen_episode(self) -> podgen.Episode:
        return self._podgen_episode

    @property
    def ctime(self):
        if (not self._ctime):
            stat = pathlib.Path(self._source).stat()
            try:
                self._ctime = stat.st_birthtime
            except AttributeError:
                self._ctime = stat.st_ctime
        return self._ctime

    @property
    def library_info(self):
        return self._library_info

    @library_info.setter
    def library_info(self, var):
        self._library_info = var

    def _do_probe(self):
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
            raise RuntimeError(f"ffprobe failed, corrupt? {str(self._source)}")

        try:
            probe_dict = json.loads(child_result.stdout)
        except json.JSONDecodeError:
            secho("f skip {outfile} json parse error from ffprobe")

        self._probe = probe_dict["format"]
        self._tags = self._probe["tags"]

        return

    def _create_podgen_episode(self) -> None:
        pubdate = dateutil.parser.isoparse(self._tags["creation_time"])
        file_name = pathlib.Path(self._source).name
        self._podgen_episode = podgen.Episode(
            id=self.asin,
            title=self._tags["title"],
            summary=self._tags["comment"],
            publication_date=pubdate,
            authors=[podgen.Person(self._tags["artist"])],
            withhold_from_itunes=(not self._make_public)
        )

        self._podgen_episode.media = podgen.Media(
            url=f"{self._url_prefix}{file_name}",
            size=self._probe["size"],
            duration=timedelta(seconds=float(self._probe["duration"]))
        )

@click.command("rss")  # noqa: E302
@click.argument("files", nargs=-1)
@click.option(
    "--name",
    type=str,
    required=True,
    help="podcast name"
)
@click.option(
    "--desc",
    type=str,
    required=True,
    help="podcast description"
)
@click.option(
    "--website",
    type=str,
    help="podcast homepage - if not specified, defaults to `--url-prefix`"
)
@click.option(
    "--explicit",
    is_flag=True,
    default=True,
    show_default=True,
    help="Listener discretion is advised"
)
@click.option(
    "--make-public",
    is_flag=True,
    type=bool,
    default=False,
    show_default=True,
    help="""
    **DO YOU FEEL LUCKY, PUNK?**

    By default, feed is set to private to avoid showing up in
    public directories ("<itunes:block>" is set to Yes). If you
    are *REALLY, REALLY SURE* that you are comfortable with publicly
    listing *A PODCAST OF YOUR DRM-STRIPPED AUDIBLE BOOKS* and
    aren't worried about DMCA takedowns to your ISP or losing your
    Audible account, go right ahead and pass this flag.

    n.B. - Spotify doesn't honor <itunes:block>, so even if you don't
    use `--make-public` flag, you may still get listed there
    """
)
@click.option(
    "--image",
    type=str,
    required=True,
    help="""
    Podcast artwork image. If you give a URL, it will be used unmodified.
    If you give a bare filename, `--url-prefix` will be used instead
    (plus the filename). E.g. `--url prefix https://example.com/cast/`
    and `--image art.jpg` will result in https://example.com/cast/art.jpg
    """
)
@click.option(
    "--category",
    type=str,
    default="Arts",
    show_default=True,
    help="""
    iTunes top level category, see
    https://podcasters.apple.com/support/1691-apple-podcasts-categories
    """
)
@click.option(
    "--subcategory",
    type=str,
    default="Books",
    show_default=True,
    help="""
    iTunes sub category, see
    https://podcasters.apple.com/support/1691-apple-podcasts-categories
    """
)
@click.option(
    "--url-prefix",
    required=True,
    help="""
    Base URL for media files and other details. If you have
    `--files foo.mp3 --url-prefix https://example.com/cast/`,
    the feed will fetch https://example.com/cast/foo.mp3 .
    May influence `--website`, `--feed-url`, and `--image`

    Note - don't forget to include the trailing "/"
    """
)
@click.option(
    "--outfile",
    "-o",
    type=str,
    default=pathlib.Path.cwd() / "rss",
    help="""
    Output filename for the rss feed
    """,
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
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="""
    Overwrite an existing `--outfile`
    """
)
@click.option(
    "--sort-by-purchase-date",
    is_flag=True,
    default=False,
    help="""
    Order podcast entries by purchase date. Requires reading from library API
    """
)
@click.option(
    "--add-contributors-from-library-api",
    is_flag=True,
    default=False,
    help="""
    Credit writers and narrators per-episode, using library API
    If not used, default is to credit writer only using file metadata
    """
)
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
@bunch_size_option
@start_date_option
@end_date_option
@pass_session
@pass_client
async def cli(
    session,
    client,
    name: str,
    desc: str,
    website: str,
    explicit: bool,
    make_public: bool,
    url_prefix: str,
    image: str,
    category: str,
    subcategory: str,
    feed_url: str,
    files: str,
    outfile: str,
    sort_by_purchase_date: bool,
    add_contributors_from_library_api: bool,
    all_: bool,
    overwrite: bool,
):
    """Generate RSS File"""

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
    print(f"sort by purchase date => {sort_by_purchase_date}")

    cast = podgen.Podcast(
        name=name,
        description=desc,
        website=website,
        explicit=explicit,
        withhold_from_itunes=(not make_public),
        image=image,
        feed_url=feed_url,
        category=podgen.Category(category, subcategory)
    )

    episode_array = []
    for file in _get_input_files(files, recursive=True):
        ep = EpisodeCreator(
            file=file,
            url_prefix=url_prefix,
            overwrite=overwrite,
            make_public=make_public
        )
        echo(f"adding {ep.asin} => {ep.title}")
        episode_array.append(ep)

    if add_contributors_from_library_api or sort_by_purchase_date:
        books = await _get_library_info(
            session,
            client
        )
        for ep in episode_array:
            ep.library_info = books[ep.asin]
            if sort_by_purchase_date:
                ep.podgen_episode.publication_date = \
                    ep.library_info['date_added']
            if add_contributors_from_library_api:
                ep.podgen_episode.authors = [
                    podgen.Person(
                        f"Written by {ep.library_info['authors']}"
                    ),
                    podgen.Person(
                        f"Narrated by {ep.library_info['narrators']}"
                    ),
                ]

    if sort_by_purchase_date:
        episode_array.sort(key=(lambda x: x.library_info['date_added']))
    else:
        episode_array.sort(key=(lambda x: x.ctime))

    for ep in episode_array:
        cast.add_episode(ep.podgen_episode)

    echo("creating feed...")
    cast.rss_file(outfile)
    print(f"feed saved to {outfile}")
