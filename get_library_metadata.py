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
    for var in ['PATH']:
        if not(os.getenv(var)):
            raise RuntimeError(f"must set shell env var {var}")

def get_auth_creds():
    return map(audible.Authenticator.from_file, glob.glob('creds/*'))

if __name__ == "__main__":
    all_books = []

    for account in get_auth_creds():
        #pp.pprint(account)
        with audible.Client(auth=account) as client:
            library = client.get(
                "1.0/library",
                num_results=3,
                response_groups="contributors,product_desc,product_attrs",
                sort_by="-PurchaseDate"
            )
            for book in library["items"]:
                all_books.append(book)
                asin = book['asin']
                print(f'got asin {asin}')
                license = client.post(
                    f"1.0/content/{asin}/licenserequest",
                    {"consumption_type": "Download",
                        "supported_drm_types": ["Mpeg", "Adrm"],
                        "quality": "Extreme"
                    }
                )
                pp.pprint(license)
                decrypted_voucher = audible.aescipher.decrypt_voucher_from_licenserequest(account, license)
                print(f"decrypted => '{decrypted_voucher}'")

    #for book in all_books:
    #    pp.pprint(book)
