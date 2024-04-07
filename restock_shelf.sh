#!/bin/sh

target_dir=${target_dir:-/shelf} export target_dir

: "${SHELF_DESC:=description goes here}" ; export SHELF_DESC
: "${SHELF_TITLE:=title goes here}" ; export SHELF_TITLE
: "${SHELF_IMAGE:=image-goes-here.jpg}" ; export SHELF_IMAGE
: "${SHELF_URL_PREFIX:=https://invalid.invalid/}" ; export SHELF_URL_PREFIX

mkdir -p "${target_dir}/dl" "${target_dir}/pt"
cd "${target_dir}/dl" || exit 1

audible library export \
    --resolve-podcasts \
    --format json

audible download \
    --aaxc \
    --pdf \
    --cover \
    --cover-size 500 \
    --chapter \
    --annotation \
    --jobs 4 \
    --quality best \
    --filename-mode asin_ascii \
    --resolve-podcasts \
    --all \
    --start-date 2023-06-01

audible decrypt \
    --all \
    --dir "${target_dir}/pt" \
    --rebuild-chapters \
    --force-rebuild-chapters \
    --copy-asin-to-metadata

cp library.json "${target_dir}/pt"
cd "${target_dir}/pt" || exit 1

audible rss \
    --all \
    --overwrite \
    --start-date 2023-06-01 \
    --name "${SHELF_TITLE}" \
    --desc "${SHELF_DESC}" \
    --image "${SHELF_IMAGE}" \
    --url-prefix "${SHELF_URL_PREFIX}" \
