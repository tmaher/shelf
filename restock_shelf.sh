#!/bin/sh

cd /app
pipenv run ./getlib.py

cd /shelf
/app/generate_personal_podcast.rb
