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
import readline
import glob

pp = pprint.PrettyPrinter(indent=4)

def assert_env_vars():
    for var in ['target_dir']:
        if not(os.getenv(var)):
            raise RuntimeError(f"must set shell env var {var}")

def get_auth_creds():
    return map(audible.Authenticator.from_file, glob.glob('creds/*'))

if __name__ == "__main__":

    assert_env_vars()
    target_dir = os.getenv('target_dir')

    for account in get_auth_creds():
        cc = account.locale.country_code
        ab = account.activation_bytes
        catalog_dir = f"{target_dir}/catalog/{cc}.{ab}"
        print(f"using catalog {catalog_dir}")

        with audible.Client(auth=account) as client:
            for asin_file in glob.glob(f'{catalog_dir}/*.json'):
                book = json.load(open(asin_file))
                asin  = book['asin']

                print(f"** ASIN/Title  => '{asin} / {book['title']}'")

                if '_DRM' not in book['_STATE']:
                    print(f"** SKIPPING {asin} - no DRM keys")
                    continue
                if 'stripped' in book['_STATE']['_DRM']:
                    print(f"** SKIPPING {asin} - catalog json says is already DRM stripped")
                    continue

                aax_file = f"{catalog_dir}/{asin}.aax"
                m4a_file = f"{catalog_dir}/{asin}.m4a"

                subprocess.run(["ffmpeg", "-y",
                    "-audible_key", book['_STATE']['_DRM']['key'],
                    "-audible_iv",  book['_STATE']['_DRM']['iv'],
                    "-i", aax_file,
                    "-c", "copy", m4a_file],
                check=True)
                print("ffmpeg done...")

                book['_STATE']['_DRM']['stripped'] = True
                with open(asin_file, 'w') as f:
                    json.dump(book, f)

                print(f"DRM STRIPPED => {m4a_file}\n\n")
