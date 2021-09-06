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
        ab = account.activation_bytes
        cc = account.locale.country_code
        os.makedirs(f'{target_dir}/catalog', 0o0700, exist_ok=True)
        os.makedirs(f'{target_dir}/catalog/{cc}.{ab}', 0o0700, exist_ok=True)

        with audible.Client(auth=account) as client:
            library = client.get(
                "1.0/library",
                num_results=3,
                response_groups="contributors,product_desc,product_attrs",
                sort_by="-PurchaseDate"
            )
            for book in library["items"]:
                asin = book['asin']

                catalog_file = f"{target_dir}/catalog/{cc}.{ab}/{asin}.json"
                with open(catalog_file, 'w') as f:
                    f.write(json.dumps(book))
