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
                if book['_STATE']:
                    printf(f"** SKIPPING {asin} - state exists")
                    continue

                license = client.post(
                    f"1.0/content/{asin}/licenserequest",
                    {"consumption_type": "Download",
                        "supported_drm_types": ["Mpeg", "Adrm"],
                        "quality": "Extreme"
                    }
                )
                decrypted_voucher = audible.aescipher.decrypt_voucher_from_licenserequest(account, license)
                asset_url = license['content_license']['content_metadata']['content_url']['offline_url']

                #print(f"** LICENSE REQ => '{license}'")
                print(f"** DECRYPTED   => '{decrypted_voucher}'")
                print(f"** ASIN/Title  => '{asin} / {book['title']}'")
                print(f"** TITLE => '{book['title']}'")
                print(f"** ASSET URL => '{asset_url}'")

                dl_filename = f"{catalog_dir}/{asin}.aax"

                #r = requests.get(asset_url, stream=True)
                #r = requests.get(asset_url)
                #r, _ = client._request(
                #    "GET",
                #    url=asset_url,
                #    allow_redirects=True
                #)
                #print(f"** ** I got headers\n{r.headers}")

                subprocess.run(["curl", "-s", "-D", "-",
                    "-H", "User-agent:your-mom",
                    "-o", dl_filename,
                    asset_url],
                    check=True)

                print(f"DOWNLOADED => {dl_filename}")

                book['_STATE']['_DRM'] = decrypted_voucher
                with open(asin_file, 'w') as f:
                    json.dump(book, f)
                print(f"marked {asin} as done\n\n")
