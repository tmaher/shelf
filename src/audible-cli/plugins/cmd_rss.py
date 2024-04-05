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

import click
from click import echo, secho

from audible_cli.decorators import pass_session
from audible_cli.exceptions import AudibleCliException


class ChapterError(AudibleCliException):
    """Base class for all chapter errors."""

@click.command("rss")
@pass_session
def cli(
    session
):
    """Generate RSS File"""
    True