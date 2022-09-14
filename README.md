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

TODO

## Deploying in production

TODO