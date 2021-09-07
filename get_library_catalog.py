#!/usr/bin/env python3

import os
from os.path import exists
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
    os.makedirs(f'{target_dir}/catalog', 0o0700, exist_ok=True)

    for account in get_auth_creds():
        cc = account.locale.country_code
        ab = account.activation_bytes

        with audible.Client(auth=account) as client:
            catalog_dir = f'{target_dir}/catalog/{cc}.{ab}'
            os.makedirs(catalog_dir, 0o0700, exist_ok=True)

            library = client.get(
                "1.0/library",
                num_results=1,
                response_groups="contributors,product_desc,product_attrs",
                sort_by="-PurchaseDate"
            )
            for book in library["items"]:
                asin = book['asin']
                print(f"found '{book['title']}' by {book['authors'][0]['name']}")
                book['_STATE'] = {}

                catalog_file = f"{catalog_dir}/{asin}.json"
                if exists(catalog_file):
                    print(f"** SKIPPING {asin}, catalog json already exists")
                    continue

                with open(catalog_file, 'w') as f:
                    f.write(json.dumps(book))
