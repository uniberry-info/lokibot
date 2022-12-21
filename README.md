# Loki Bot

Gatekeeper bot for the Unimore Informatica unofficial Matrix space

\[ [**Website**](https://loki.steffo.eu) | [PyPI](https://pypi.org/project/lokiunimore/) \]

> TIP: You may be looking for its predecessor, [Thor Bot](https://github.com/Steffo99/thorunimore).

![](lokiunimore/web/static/opengraph.png)

## Functionality

This bot monitors a [pre-configured *public* Matrix space][config-public-space] for join events, sending a [welcome message][welcome-msg] to every new joiner.

The [welcome message][welcome-msg] contains a link, which when clicked starts the user verification process:

1. a page describing the bot is opened, and it allows users to login with a [pre-configured OpenID Connect Identity Provider][config-oidc-idp];
2. the claims of the OIDC IdP are verified, and the user's email address is checked to verify that its domain matches a [pre-configured RegEx][config-email-regex]
 with specific email requirements;
3. if the email address fullfils all the requirements, an invitation to a different, [pre-configured *private* Matrix space][config-private-space] is sent to the user.

Additionally, the bot monitors for leave events from both spaces, deleting user data if no longer needed to protect the user's privacy.

[welcome-msg]: https://github.com/Steffo99/lokiunimore/blob/99f7101abc3f68472844cd2f1bac5119e41c1682/lokiunimore/matrix/templates/messages.py#L3-L23
[config-public-space]: https://github.com/Steffo99/lokiunimore/blob/main/lokiunimore/config/config.py#L50-L60
[config-oidc-idp]: https://github.com/Steffo99/lokiunimore/blob/main/lokiunimore/config/config.py#L147-L202
[config-email-regex]: https://github.com/Steffo99/lokiunimore/blob/main/lokiunimore/config/config.py#L194-L202
[config-private-space]: https://github.com/Steffo99/lokiunimore/blob/99f7101abc3f68472844cd2f1bac5119e41c1682/lokiunimore/config/config.py#L76-L86

## Setting up a development environment

### Dependencies

This project uses [Poetry](https://python-poetry.org/) to manage the dependencies.

To install all dependencies in a venv, run:

```console
$ poetry install
```

> TIP: For easier venv management, you may want to set:
> 
> ```console
> $ poetry config virtualenvs.in-project true
> ```

To activate the venv, run:

```console
$ poetry shell
```

To run something in the venv without activating it, run:

```console
$ poetry run <COMMAND>
```

### Environment

Loki requires a lot of environment variables to be set, therefore it makes use of [cfig](https://cfig.readthedocs.io/en/latest/) to simplify the setup.

To view the current configuration, followed by a description of each variable, run:

```console
$ poetry run python -m lokiunimore.config
```

## Deploying in production

Use the [pre-built Docker image](https://github.com/Steffo99/lokiunimore/pkgs/container/lokiunimore), or build it from the [provided Dockerfile](Dockerfile).

Run the image without any command to view and validate the current configuration.

Run the image with the `gunicorn -b 0.0.0.0:80 lokiunimore.web.app:rp_app` command to launch the production web server on local port 80, expecting to be behind a  reverse proxy.

Run the image with the `lokiunimore.matrix` command to launch the Matrix bot.

### Using Docker Compose

Create a `docker-compose.yml` file which starts three services:
- a [`postgres`](https://registry.hub.docker.com/_/postgres) instance
- a [`ghcr.io/steffo99/lokiunimore`](https://github.com/Steffo99/lokiunimore/pkgs/container/lokiunimore) instance running the webserver via the command `gunicorn -b 0.0.0.0:80 lokiunimore.web.app:rp_app`
- a [`ghcr.io/steffo99/lokiunimore`](https://github.com/Steffo99/lokiunimore/pkgs/container/lokiunimore) instance running the Matrix bot via the command `lokiunimore.matrix`

Ensure you're configuring all the required environment variables, as Loki Bot will not work otherwise.

<details>
<summary>Example docker-compose.yml</summary>

```yaml
version: "3.9"


services:
  # The database Loki uses to store its files
  lokidb:
    image: "postgres:14"
    restart: unless-stopped
    environment:
      PGUSER: "loki"
      PGPASSWORD: "loki"
      PGDATABASE: "loki"
      POSTGRES_USER: "loki"
      POSTGRES_PASSWORD: "loki"
      POSTGRES_DB: "loki"
      POSTGRES_INITDB_ARGS: '--encoding=UTF-8 --lc-collate=C --lc-ctype=C'
      LANG: "C"
      LC_COLLATE: "C"
      LC_CTYPE: "C"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - "./data/lokidb:/var/lib/postgresql/data"

  # The web server that Loki uses for authentication
  lokiweb:
    image: "ghcr.io/steffo99/lokiunimore:latest"
    command: "gunicorn -b 0.0.0.0:80 lokiunimore.web.app:rp_app"
    restart: unless-stopped
    ports:
      - "80:30035"  # Choose your preferred port
    env_file:
      - "./secrets/loki.env"
    depends_on:
      lokidb:
        condition: service_healthy

  # The Matrix bot that Loki uses for user interactions
  lokibot:
    image: "ghcr.io/steffo99/lokiunimore:latest"
    command: "lokiunimore.matrix"
    restart: unless-stopped
    env_file:
      - "./secrets/loki.env"
    depends_on:
      lokidb:
        condition: service_healthy
```

</details>
