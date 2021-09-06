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

pp = pprint.PrettyPrinter(indent=4)

def assert_env_vars():
    for var in ['PATH']:
        if not(os.getenv(var)):
            raise RuntimeError(f"must set shell env var {var}")

if __name__ == "__main__":

    assert_env_vars()
    my_locale = os.getenv('audible_locale') or 'us'

    os.makedirs('creds', 0o0700, exist_ok=True)

    #auth = audible.Authenticator.from_login(
    #    os.getenv('audible_username'),
    #    os.getenv('audible_password'),
    #    locale=my_locale,
    #    with_username=False,
    #    register=True)

    auth = audible.Authenticator.from_login_external(
        locale=my_locale,
        register=True
    )
    ab = auth.get_activation_bytes()
    print(f'activation bytes: {ab}')

    auth.to_file(f'creds/{my_locale}.json', encryption=False)

    #auth = audible.Authenticator.from_file(f'creds/{my_locale}.json')

    with audible.Client(auth=auth) as client:
        library = client.get(
            "1.0/library",
            num_results=1,
            response_groups="product_desc, product_attrs",
            sort_by="-PurchaseDate"
        )
    for book in library["items"]:
        pp.pprint(book)
