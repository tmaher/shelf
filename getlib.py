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

def download_file(url, asin):
    r = requests.get(url, stream=True)

    if not("Content-Disposition" in r.headers):
        print(f"no content-disposition for {url}")
        return ""

    attachment = r.headers["Content-Disposition"].split("filename=")[1]
    title, ext = os.path.splitext(attachment)
    filename = pathlib.Path.cwd() / "audiobooks" / f"{title}.{asin}{ext}"

    try:
        s = os.stat(filename)
        if s.st_size == int(r.headers["Content-Length"]):
            print(f"SKIPPING {filename} (already exists and size matches)")
            return filename
    except OSError as e:
        True

    with open(filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return filename


if __name__ == "__main__":

    auth = get_auth()
    client = audible.AudibleAPI(auth)

    books, _ = client.get(
        path="library",
        params={
            "response_groups": "product_attrs",
            "num_results": "999"
            }
    )

    for book in books["items"]:
        asin = book["asin"]
        pp.pprint(book)
        dl_link = _get_download_link(client, asin)

        if dl_link:
            print(f"download link now: {dl_link}")
            status = download_file(dl_link, asin)
            print(f"downloaded file: {status}")
