FROM python:3-alpine AS system
RUN apk add --update build-base python3-dev py-pip musl-dev libffi-dev openssl-dev postgresql-dev gcc rust cargo
RUN pip install "poetry"

FROM system AS workdir
WORKDIR /usr/src/lokiunimore

FROM workdir AS dependencies
COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock
RUN poetry install --no-root --no-dev

FROM dependencies AS package
COPY . .
RUN poetry install

FROM package AS entrypoint
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["poetry", "run", "python", "-m"]
# Remember to change the CMD in Docker Compose!
CMD ["lokiunimore.config"]

FROM entrypoint AS labels
LABEL org.opencontainers.image.title="Lokiunimore"
LABEL org.opencontainers.image.description="Matrix room gatekeeper bot for the unofficial Unimore space"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"
LABEL org.opencontainers.image.url="https://github.com/Steffo99/lokiunimore"
LABEL org.opencontainers.image.authors="Stefano Pigozzi <me@steffo.eu>"

FROM labels AS final
