"""Generate rss feed info for library

This is a proof-of-concept and for testing purposes only.

No error handling.
Need further work. Some options do not work or options are missing.

Needs at least ffmpeg 4.4
"""

import json
import operator
import pathlib
import re
import subprocess  # noqa: S404
import typing as t
from enum import Enum
from functools import reduce
from glob import glob
from shlex import quote
from shutil import which
import podgen
from datetime import date, timedelta
import dateutil
from podgen import Podcast, Episode, Media, Person
from pprint import pprint
import xml.etree.ElementTree as ElementTree
from xml.dom import minidom

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
            raise(click.BadParameter("{filename}: file not found or supported."))

        expanded_filter = filter(
            lambda x: SupportedFiles.is_supported_file(x), expanded
        )
        expanded = list(map(lambda x: pathlib.Path(x).resolve(), expanded_filter))
        filenames.extend(expanded)

    return filenames

class EpisodeCreator:
    def __init__(
        self,
        cast: podgen.Podcast,
        file: pathlib.Path,
        media_url_prefix: str,
        overwrite: bool
    ) -> None:
        self._cast = cast
        self._source = file
        self._media_url_prefix = media_url_prefix
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
        file_name = pathlib.Path(self._source.name)
        self._episode = Episode(
            title=self._tags["title"],
            summary=self._tags["comment"],
            publication_date=pubdate,
            authors=[Person(self._tags["artist"])],
            withhold_from_itunes=True
        )
        self._episode.media = Media(
            url=f"{self._media_url_prefix}{file_name}",
            size=self._probe["size"],
            duration=timedelta(seconds=float(self._probe["duration"]))
        )

    def run(self):
        self.do_probe()
        #pprint(self._probe)
        self.do_ep()
        #xmlstr = minidom.parseString(
        #    ElementTree.tostring(self._episode.rss_entry())
        #).toprettyxml(indent="  ")
        #print(xmlstr)
        echo(f"adding {self._source}")
        self._cast.add_episode(self._episode)

@click.command("rss")
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
    required=True,
    help="podcast homepage"
)
@click.option(
    "--explicit",
    is_flag=True,
    default=False,
    help="Listener discretion is advised"
)
@click.option(
    "--image",
    type=str,
    default="",
    help="URL for the artwork image, e.g. https://example.com/cast.jpg"
)
@click.option(
    "--media-url-prefix",
    required=True,
    help="URL prefix for the media files. If you have file foo.mp3 and it will be fetched as https://example.com/cast/foo.mp3 then set this to https://example.com/cast/"
)
@click.option(
    "--outfile",
    "-o",
    type=str,
    default=pathlib.Path.cwd() / "rss",
    help="Folder where the decrypted files should be saved.",
    show_default=True
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing files.")
@click.option(
    "--all",
    "-a",
    "all_",
    is_flag=True,
    default=False,
    help="RSS-ify all eligible media files in current dir ({0})".format(",".join(SupportedFiles.get_supported_list()))
)
@pass_session
def cli(
    session,
    name: str,
    desc: str,
    website: str,
    explicit: bool,
    media_url_prefix: str,
    image: str,
    files: str,
    outfile: str,
    all_: bool,
    overwrite: bool,
):
    """Generate RSS File"""

    raise RuntimeError("zoinks! add pubdate library support before merging")
    if not which("ffprobe"):
        ctx = click.get_current_context()
        ctx.fail("ffprobe not found")

    if all_:
        if files:
            raise click.BadOptionUsage("all",
                "If using `--all`, no FILES arguments can be used."
            )
        files = [f"*{suffix}" for suffix in SupportedFiles.get_supported_list()]

    if pathlib.Path(outfile).exists() and not(overwrite):
        raise click.BadOptionUsage(
            "outfile",
            f"sorry --outfile {outfile} already exists"
        )

    cast = Podcast(
        name=name,
        description=desc,
        website=website,
        explicit=explicit,
        image=image
    )

    files = _get_input_files(files, recursive=True)
    for file in files:
        EpisodeCreator(
            cast=cast,
            file=file,
            media_url_prefix=media_url_prefix,
            overwrite=overwrite
        ).run()

    cast.rss_file(outfile)
    raise 
    True