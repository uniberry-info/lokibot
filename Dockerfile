FROM python:3-buster AS system
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y rustc cargo

FROM system AS workdir
WORKDIR /usr/src/lokiunimore

FROM system AS dependencies
COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock
RUN pip install "poetry"
RUN poetry install --no-root --no-dev

FROM dependencies AS package
COPY . .
RUN poetry install

FROM package AS entrypoint
# Remember to change the CMD in Docker Compose!
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["poetry", "run", "python", "-m"]
CMD ["lokiunimore.config"]

FROM entrypoint AS labels
LABEL org.opencontainers.image.title="Lokiunimore"
LABEL org.opencontainers.image.description="Matrix room gatekeeper bot for the unofficial Unimore space"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"
LABEL org.opencontainers.image.url="https://github.com/Steffo99/lokiunimore"
LABEL org.opencontainers.image.authors="Stefano Pigozzi <me@steffo.eu>"

FROM labels AS final
