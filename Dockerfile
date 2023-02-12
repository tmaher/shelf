FROM python:3.8-alpine3.17

WORKDIR /app
COPY "Pipfile" "*.rb" "*.py" /app/

RUN pip install pipenv
RUN adduser -S -h /app app
USER app
ENV PATH=/app/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

ENTRYPOINT ["/bin/sh"]
