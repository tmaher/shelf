#!/bin/sh

target_dir=${target_dir:-/shelf}
export target_dir

cd /app
pipenv run ./getlib.py

cd "${target_dir}"
/app/generate_personal_podcast.rb
