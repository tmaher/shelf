#!/usr/bin/env python3

import audible
import pprint

pp = pprint.PrettyPrinter(indent=4)
auth = audible.FileAuthenticator(".audible-creds.json")
auth.to_file(".audible-creds.json", encryption=False)
client = audible.AudibleAPI(auth)

books, _ = client.get(
        path="library",
        params={
            "response_groups": "contributors,product_desc,product_attrs",
            "num_results": "5",
            "sort_by": "PurchaseDate"
            }
    )

pp.pprint(books["items"][0])

asin = books["items"][0]['asin']

resp = client.get(f"content/{asin}/metadata",
        params={
            "response_groups": "chapter_info,always-returned,content_reference,content_url",
        }
    )
pp.pprint(resp)
