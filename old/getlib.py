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
import json

pp = pprint.PrettyPrinter(indent=4)

def assert_env_vars():
    for var in ['activation_bytes', 'target_dir']:
        if not(os.getenv(var)):
            raise RuntimeError(f"must set shell env var {var}")

def get_auth():
    auth = audible.FileAuthenticator("/creds/audible.json")
    auth.to_file("/creds/audible.json", encryption=False)
    return auth

# get download link(s) for book
def _get_download_link(client, book):
    asin = book['asin']
    codec = get_codec(book)
    book['codec'] = codec
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

def get_dl_filename(book, disposition):
    attachment = disposition.split("filename=")[1]
    title, ext = os.path.splitext(attachment)
    dl_filename = f"{os.getenv('target_dir')}/{book['purchased']}-{title}.{book['asin']}.{book['codec']}{ext}"

    return dl_filename

def get_clean_filename(dl_filename):
    base_path, _ = os.path.splitext(dl_filename)
    return base_path


def download_file(url, book):

    #asin, purchased='1970-01-01', codec="LC_64_22050_stereo"):
    r = requests.get(url, stream=True)

    if not("Content-Disposition" in r.headers):
        print(f"no content-disposition for {url}")
        return

    dl_filename = get_dl_filename(book, r.headers["Content-Disposition"])
    clean_filename = get_clean_filename(dl_filename)
    apidata_filename = f"{clean_filename}.json"
    with open(apidata_filename, 'w') as f:
        f.write(json.dumps(book))

    try:
        s = os.stat(dl_filename)
        if s.st_size == int(r.headers["Content-Length"]):
            print(f"SKIPPING {dl_filename} (already exists and size matches)")
            return dl_filename
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
    m4a_file = f"{clean_filename}.m4a"

    if (os.access(m4a_file, os.R_OK) and
        (os.path.getmtime(m4a_file) > os.path.getmtime(dl_filename))):
        print(f"SKIPPING CONVERT (m4a newer than aax) {dl_filename}")
        return clean_filename

    subprocess.run(["ffmpeg", "-y",
                    "-activation_bytes", os.getenv('activation_bytes'),
                    "-i", dl_filename,
                    "-c", "copy", m4a_file],
                check=True)
    subprocess.run(["ffmpeg", "-y",
                    "-activation_bytes", os.getenv('activation_bytes'),
                    "-i", dl_filename,
                    "-update", "1", "-frames:v", "1",
                    "-an", "-vf", "scale=2000:-1", f"{clean_filename}.png"],
                check=True)

    return m4a_file

def get_codec(book):
    preferred_codecs = [
        "LC_128_44100_stereo",
        "LC_64_44100_stereo",
        "LC_64_22050_stereo",
        "LC_32_22050_stereo"
    ]
    avail_codecs = {}
    try:
        for c in book['available_codecs']:
            avail_codecs[c['enhanced_codec']] = True
        for pc in preferred_codecs:
            if pc in avail_codecs:
                return pc
    except TypeError:
        True
    raise RuntimeError(f"no acceptable codecs for {book['title']} ({book['asin']})")        

if __name__ == "__main__":

    assert_env_vars()
    auth = get_auth()
    client = audible.AudibleAPI(auth)

    books, _ = client.get(
        path="library",
        params={
            "response_groups": "contributors,product_desc,product_attrs",
            "num_results": "1000",
            "sort_by": "PurchaseDate"
            }
    )

    for book in books["items"]:
        purchased = book["purchase_date"].split("T")[0]
        book['purchased'] = purchased

        print()
        print(f"{book['purchased']}: {book['title']} ({book['asin']})")
        print(book['merchandising_summary'])

        dl_link = _get_download_link(client, book)

        if dl_link:
            print(f"download link now: {dl_link}")
            status = download_file(dl_link, book)
            if status:
                convert_file(status)
            else:
                print(f"SKIPPING CONVERSION (no filename) <= {dl_link}")
