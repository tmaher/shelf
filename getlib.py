#!/usr/bin/env python3

import os
import sys
appdir=os.path.dirname(os.path.abspath(__file__))
os.chdir(appdir)

import pathlib
import shutil
import audible
import requests
import pprint
import subprocess

pp = pprint.PrettyPrinter(indent=4)

def get_auth():
    auth = audible.FileAuthenticator(".audible-creds.json")
    auth.to_file(".audible-creds.json", encryption=False)
    return auth


# get download link(s) for book
def _get_download_link(client, asin, codec="LC_64_22050_stereo"):
    # need at least v0.2.1a4
    try:
        content_url = "https://cde-ta-g7g.amazon.com/FionaCDEServiceEngine/FSDownloadContent"
        params = {
            'type': 'AUDI',
            'currentTransportMethod': 'WIFI',
            'key': asin,
            'codec': codec
        }
        r, _ = client._request(
            "GET",
            url=content_url,
            params=params,
            allow_redirects=False
        )
        link = r.headers['Location']
        tld = client.auth.locale.domain
        new_link = link.replace("cds.audible.com", f"cds.audible.{tld}")
        return new_link
    except Exception as e:
        try:
            link = e.response.headers['Location']

            # prepare link
            # see https://github.com/mkb79/Audible/issues/3#issuecomment-518099852
            tld = client.auth.locale.domain
            new_link = link.replace("cds.audible.com", f"cds.audible.{tld}")
            return new_link

        except Exception as e:
            print(f"Error: {e}")
            return

def get_dl_filename(asin, purchased, codec, disposition):
    attachment = disposition.split("filename=")[1]
    title, ext = os.path.splitext(attachment)

    return pathlib.Path.cwd() / "audiobooks" / f"{purchased}-{title}.{asin}.{codec}{ext}"


def get_clean_filename(dl_filename):
    base_path, _ = os.path.splitext(dl_filename)
    return f"{base_path}.m4a"


def download_file(url, asin, purchased='1970-01-01', codec="LC_64_22050_stereo"):
    r = requests.get(url, stream=True)

    if not("Content-Disposition" in r.headers):
        print(f"no content-disposition for {url}")
        return

    dl_filename = get_dl_filename(asin, purchased, codec,
                                r.headers["Content-Disposition"])

    try:
        s = os.stat(dl_filename)
        if s.st_size == int(r.headers["Content-Length"]):
            print(f"SKIPPING {dl_filename} (already exists and size matches)")
            return
    except OSError as e:
        True

    if os.getenv('dl_dryrun'):
        print(f"SKIPPING DL (just because) => {dl_filename}")
        return

    with open(dl_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    print(f"DOWNLOADED => {dl_filename}")
    return dl_filename

def convert_file(dl_filename):
    clean_filename = get_clean_filename(dl_filename)
    cmd = ["ffmpeg", "-activation_bytes", os.getenv('activation_bytes'),
            "-i", dl_filename, "-c:a", "copy", clean_filename ]
    subprocess.run(cmd, check=True)
    return clean_filename


if __name__ == "__main__":

    auth = get_auth()
    client = audible.AudibleAPI(auth)

    books, _ = client.get(
        path="library",
        params={
            "response_groups": "product_attrs",
            "num_results": "999",
            "sort_by": "PurchaseDate"
            }
    )

    for book in books["items"]:
        asin = book["asin"]
        purchased = book["purchase_date"].split("T")[0]

        print()
        print(f"asin: {asin}, purchased {purchased}")
        print(f"summary {book['merchandising_summary']}")

        dl_link = _get_download_link(client, asin)

        if dl_link:
            print(f"download link now: {dl_link}")
            status = download_file(dl_link, asin, purchased)
            if status:
                convert_file(status)
            else:
                print(f"SKIPPING CONVERSION (no filename) <= {dl_link}")
