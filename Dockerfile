FROM python:3.11-alpine3.19

RUN apk add build-base \
            ffmpeg \
            jq \
            libffi libffi-dev \
            ruby
RUN pip install poetry==1.8.2

RUN mkdir /app
COPY "pyproject.toml" "poetry.*" /app/

ENV AUDIBLE_CONFIG_DIR=${AUDIBLE_CONFIG_DIR:-/config}
ENV AUDIBLE_PLUGIN_DIR=${AUDIBLE_PLUGIN_DIR:-/app/src/audible-cli/plugins}
RUN mkdir -p ${AUDIBLE_CONFIG_DIR}
WORKDIR /app

RUN poetry install

COPY "*.rb" "*.py" "restock_shelf.sh" /app/
COPY "src/" /app/src/
ENV PATH=/app/.venv/bin:${PATH}

CMD ["/app/restock_shelf.sh"]
