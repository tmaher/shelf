FROM python:3.11-alpine3.19 as buildbase

RUN apk add build-base \
            ffmpeg \
            libffi libffi-dev
RUN pip install poetry==1.8.2

RUN mkdir /app
COPY "pyproject.toml" "poetry.*" /app/

ENV AUDIBLE_CONFIG_DIR=${AUDIBLE_CONFIG_DIR:-/config}
ENV AUDIBLE_PLUGIN_DIR=${AUDIBLE_PLUGIN_DIR:-/app/src/audible-cli/plugins}
RUN mkdir -p ${AUDIBLE_CONFIG_DIR}
WORKDIR /app

RUN poetry install

COPY "restock_shelf.sh" /app/
COPY "src/" /app/src/

RUN apk del build-base
FROM scratch

COPY --from=buildbase / /
ENV PATH=/app/.venv/bin:${PATH} \
    AUDIBLE_CONFIG_DIR=${AUDIBLE_CONFIG_DIR:-/config} \
    AUDIBLE_PLUGIN_DIR=${AUDIBLE_PLUGIN_DIR:-/app/src/audible-cli/plugins}

CMD ["/app/restock_shelf.sh"]
