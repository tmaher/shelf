FROM python:3.8-alpine3.17

RUN mkdir /app
COPY "Pipfile*" "*.rb" "*.py" "restock_shelf.sh" /app/

RUN pip install pipenv \
    && apk add ffmpeg

ENV PATH=/app/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PIPENV_VENV_IN_PROJECT=1

RUN cd /app \
    && pipenv install

CMD ["/app/restock_shelf.sh"]
