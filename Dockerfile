FROM python:3.11-alpine3.19

RUN apk add ffmpeg ruby build-base libffi libffi-dev
RUN pip install poetry==1.8.2

RUN mkdir /app
COPY "pyproject.toml" "poetry.*" "*.rb" "*.py" "restock_shelf.sh" /app/
COPY "src/" /app/src/

ENV AUDIBLE_CONFIG_DIR=${AUDIBLE_CONFIG_DIR:-/config} 
RUN mkdir -p ${AUDIBLE_CONFIG_DIR}
WORKDIR /app

RUN poetry install

# CMD ["/app/restock_shelf.sh"]
