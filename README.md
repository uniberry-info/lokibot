# Loki Bot

Gatekeeper bot for the Unimore Informatica unofficial Matrix space, successor to [Thor Bot](https://github.com/Steffo99/thorunimore).

[![Website](https://img.shields.io/website?url=https%3A%2F%2Floki.steffo.eu%2F)](https://loki.steffo.eu/)
 
[![On PyPI](https://img.shields.io/pypi/v/lokiunimore)](https://pypi.org/project/lokiunimore/)
 
[![Chat](https://img.shields.io/matrix/loki-bot:ryg.one?server_fqdn=matrix.ryg.one)](https://matrix.to/#/#loki-bot:ryg.one)

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
