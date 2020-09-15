FROM alpine:3.12 AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
RUN mkdir -p /app/run && \
    adduser  --no-create-home --gecos "Skylla daemon" --disabled-password \
             --home /app/run --uid 35003 skylla

RUN apk --no-cache upgrade && \
    apk --no-cache add py3-pip py3-cryptography

FROM base AS skylla-build
RUN pip3 install ipython
RUN apk update && \
    apk add py3-pyrsistent py3-attrs py3-jsonschema py3-multidict \
            py3-pexpect py3-ptyprocess py3-pyrsistent py3-requests-toolbelt \
            python3-dev libffi-dev libressl-dev musl-dev make gcc && \
    pip3 install -U pip poetry
WORKDIR /app/src
RUN python3 -m venv /app/env
ENV VIRTUAL_ENV=/app/env \
    PATH=/app/env/bin:$PATH
COPY pyproject.toml poetry.lock /app/src/
RUN poetry install --no-dev --no-root
COPY . /app/src/
RUN poetry build -f wheel && \
    /app/env/bin/pip3 install dist/*.whl


FROM skylla-build AS skylla-test

RUN poetry install
