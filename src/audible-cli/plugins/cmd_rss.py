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
import tempfile
import typing as t
from enum import Enum
from functools import reduce
from glob import glob
from shlex import quote
from shutil import which
from podgen import Podcast, Episode, Media
from pprint import pprint

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
        file: pathlib.Path,
        target_dir: pathlib.Path,
        tempdir: pathlib.Path,
        overwrite: bool
    ) -> None:
        self._source = file
        self._target_dir = target_dir
        self._tempdir = tempdir
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
        return 

    def do_xml(self):
        True

    def run(self):
        oname = self._source.with_suffix(".xml").name
        outfile = self._target_dir / oname

        if outfile.exists():
            if self._overwrite:
                secho(f"Overwrite {outfile}: already exists", fg="blue")
            else:
                secho(f"Skip {outfile}: already exists", fg="blue")
                return

        self.do_probe()
        pprint(self._probe, indent=4)
        self.do_xml()

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
    default="",
    help="Description"
)
@click.option(
    "--website",
    type=str,
    default="",
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
    help="URL for the artwork image, e.g. https://example.com/cast.jpg"
)
@click.option(
    "--media-url-prefix",
    required=True,
    help="URL prefix for the media files. If you have file foo.mp3 and it will be fetched as https://example.com/cast/foo.mp3 then set this to https://example.com/cast/"
)
@click.option(
    "--dir",
    "-d",
    "directory",
    type=click.Path(exists=True, dir_okay=True),
    default=pathlib.Path.cwd(),
    help="Folder where the decrypted files should be saved.",
    show_default=True
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing files.")
@click.option(
    "--all",
    "-a",
    "all_",
    is_flag=True,
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
    directory: t.Union[pathlib.Path, str],
    all_: bool,
    overwrite: bool,
):
    """Generate RSS File"""

    if not which("ffprobe"):
        ctx = click.get_current_context()
        ctx.fail("ffprobe not found")

    if all_:
        if files:
            raise click.BadOptionUsage("all",
                "If using `--all`, no FILES arguments can be used."
            )
        files = [f"*{suffix}" for suffix in SupportedFiles.get_supported_list()]

    cast = Podcast(
        name=name,
        description=desc,
        website=website,
        explicit=explicit,
    )

    files = _get_input_files(files, recursive=True)
    with tempfile.TemporaryDirectory() as tempdir:
        for file in files:
            episode_creator = EpisodeCreator(
                file=file,
                target_dir=pathlib.Path(directory).resolve(),
                tempdir=pathlib.Path(tempdir).resolve(),
                overwrite=overwrite
            )
            episode_creator.run()
    True