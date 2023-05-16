FROM python:3-alpine AS build
RUN apk add --update \
    "build-base" \
    "python3-dev" \
    "py3-pip" \
    "musl-dev" \
    "libffi-dev" \
    "openssl-dev" \
    "postgresql-dev" \
    "gcc" \
    "git" \
    "rust" \
    "cargo" \
    "pkgconfig"
RUN pip install "poetry"

WORKDIR /usr/src/lokiunimore
COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock

RUN pip install --upgrade "pip"
RUN poetry install --no-root --no-dev

COPY . .
RUN poetry install

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["poetry", "run", "python", "-m"]
# Remember to change the CMD in Docker Compose!
CMD ["lokiunimore.config"]

LABEL org.opencontainers.image.title="Lokiunimore"
LABEL org.opencontainers.image.description="Matrix room gatekeeper bot for the unofficial Unimore space"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"
LABEL org.opencontainers.image.url="https://github.com/Steffo99/lokiunimore"
LABEL org.opencontainers.image.authors="Stefano Pigozzi <me@steffo.eu>"

FROM build AS final
