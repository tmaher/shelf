FROM python:3.12-alpine3.19

RUN mkdir /app
COPY "Pipfile*" "*.rb" "*.py" "restock_shelf.sh" /app/

WORKDIR /app
RUN apk add ffmpeg ruby build-base libffi libffi-dev
RUN pip install poetry==1.8.2

# ENV PATH=/app/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# ENV PIPENV_VENV_IN_PROJECT=1

# RUN pipenv install
# CMD ["/app/restock_shelf.sh"]
