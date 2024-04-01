#!/bin/sh

target_dir=${target_dir:-/shelf}
export target_dir
mkdir -p ${target_dir}/dl ${target_dir}/pt
cd ${target_dir}/dl

audible download --aaxc --pdf --cover --cover-size 500 --chapter \
    --annotation -j 4 --ignore-podcasts --all
#    --start-date 2024-01-01 --end-date 2024-03-01

audible decrypt --all --dir ${target_dir}/pt \
    --rebuild-chapters --force-rebuild-chapters

# cd "${target_dir}"
# /app/generate_personal_podcast.rb
