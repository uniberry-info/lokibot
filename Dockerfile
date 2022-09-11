FROM python AS metadata
LABEL maintainer="Stefano Pigozzi <me@steffo.eu>"

FROM metadata AS workdir
WORKDIR /usr/src/lokiunimore

FROM workdir AS poetry
RUN pip install "poetry"

FROM poetry AS dependencies
COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock
RUN poetry install --no-root --no-dev

FROM dependencies AS package
COPY . .
RUN poetry install

FROM package AS environment
ENV PYTHONUNBUFFERED=1

FROM environment AS entrypoint
# Remember to change the CMD in Docker Compose!
ENTRYPOINT ["poetry", "run", "python", "-m"]
CMD ["lokiunimore.config"]

