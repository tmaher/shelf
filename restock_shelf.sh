#!/bin/sh

: "${SHELF_TARGET_DIR:=/shelf}"; export SHELF_TARGET_DIR
: "${SHELF_DESC:=description goes here}" ; export SHELF_DESC
: "${SHELF_TITLE:=title goes here}" ; export SHELF_TITLE
: "${SHELF_IMAGE:=image-goes-here.jpg}" ; export SHELF_IMAGE
: "${SHELF_URL_PREFIX:=https://invalid.invalid/}" ; export SHELF_URL_PREFIX
: "${SHELF_START_DATE:=1901-12-12}" ; export SHELF_START_DATE
: "${SHELF_END_DATE:=3000-01-01}" ; export SHELF_END_DATE
: "${SHELF_IMG_DL_SIZE:=1215}" ; export SHELF_IMG_DL_SIZE

cd "${SHELF_TARGET_DIR}" || exit 1
mkdir -p "assets" "dl"
cd "dl" || exit 1

# audible library export \
#    --format json

audible download \
    --aaxc \
    --pdf \
    --cover \
    --cover-size "${SHELF_IMG_DL_SIZE}" \
    --chapter \
    --annotation \
    --jobs 4 \
    --quality best \
    --filename-mode asin_ascii \
    --ignore-podcasts \
    --all \
    --start-date "${SHELF_START_DATE}" \
    --end-date "${SHELF_END_DATE}"

audible decrypt \
    --all \
    --dir "${SHELF_TARGET_DIR}/assets" \
    --rebuild-chapters \
    --force-rebuild-chapters \
    --copy-asin-to-metadata

for book in *.aaxc; do
    img_target="${SHELF_TARGET_DIR}/assets/$(basename "${book}" .aaxc).jpg"
    if [ ! -r "${img_target}" ]; then
        img_regex="s/-AAX_[0-9_]+.aaxc/_(${SHELF_IMG_DL_SIZE})/"
        img_src="$(echo "${book}" | sed -E "${img_regex}").jpg"
        : "${img_src:="${book}"}"

        ffmpeg \
            -i "${img_src}" \
            -vf "scale=3000:3000:force_original_aspect_ratio=decrease,pad=3000:3000:(ow-iw)/2:(oh-ih)/2" \
            -frames:v 1 \
            -update 1 \
            "${img_target}"
    fi
done

cd "${SHELF_TARGET_DIR}/assets" || exit 1

audible rss \
    --all \
    --overwrite \
    --sort-by-purchase-date \
    --use-library-api \
    --start-date "${SHELF_START_DATE}" \
    --end-date "${SHELF_END_DATE}" \
    --name "${SHELF_TITLE}" \
    --desc "${SHELF_DESC}" \
    --image "${SHELF_IMAGE}" \
    --url-prefix "${SHELF_URL_PREFIX}"
