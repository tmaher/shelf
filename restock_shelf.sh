#!/bin/sh

target_dir=${target_dir:-/shelf} export target_dir

: "${SHELF_DESC:=description goes here}" ; export SHELF_DESC
: "${SHELF_TITLE:=title goes here}" ; export SHELF_TITLE
: "${SHELF_IMAGE:=image-goes-here.jpg}" ; export SHELF_IMAGE
: "${SHELF_URL_PREFIX:=https://invalid.invalid/}" ; export SHELF_URL_PREFIX

mkdir -p "${target_dir}/dl" "${target_dir}/pt"
cd "${target_dir}/dl" || exit 1

audible library export --resolve-podcasts --format json

audible download --aaxc --pdf --cover --cover-size 500 --chapter \
    --annotation -j 4 --quality best \
    --filename-mode asin_ascii \
    --resolve-podcasts \
    --all \
    --start-date 2024-01-01 --end-date 2099-12-31

audible decrypt --all --dir "${target_dir}/pt" \
    --copy-asin-to-metadata \
    --rebuild-chapters

## injecting arbitrary metadata keys...
## ffmpeg -i blah.m4a \
##   -c copy -metadata:g somekey=someval -movflags +use_metadata_tags out.m4a

cp library.json "${target_dir}/pt"
cd "${target_dir}/pt" || exit 1

audible rss \
    --all \
    --overwrite \
    --name "${SHELF_TITLE}" \
    --desc "${SHELF_DESC}" \
    --image "${SHELF_IMAGE}" \
    --url-prefix "${SHELF_URL_PREFIX}" \
