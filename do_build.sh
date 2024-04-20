#!/bin/sh -x

export APPNAME="${0}"
_log () {
  echo "$(date -Iseconds) ${APPNAME}: ${1}"
}
_error () {
  printf "%d %s ERROR\n\n%s\n" "$(date -Iseconds)" "${APPNAME}" "${1}" >&2
  exit 1
}
APPDIR="$(cd "$(dirname "$0")" && echo "$PWD")" ; export APPDIR
cd "${APPDIR}" || _error "Unable to cd to '${APPDIR}'"

docker image build -t shelf:dev . && docker run -it \
    -v ./tmp:/shelf \
    -v ./config:/config \
    --env-file ./secrets.env \
    shelf:dev "$@"