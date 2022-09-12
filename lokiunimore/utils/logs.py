import logging
import coloredlogs

log = logging.getLogger(__name__)


def install_log_handler(logger: logging.Logger = None):
    if logger is None:
        logger = logging.getLogger("lokiunimore")

    coloredlogs.install(
        logger=logger,
        level="DEBUG",
        fmt="{asctime} | {name:<32} | {levelname:>8} | {message}",
        style="{",
        level_styles=dict(
            debug=dict(color="white"),
            info=dict(color="cyan"),
            warning=dict(color="yellow"),
            error=dict(color="red"),
            critical=dict(color="red", bold=True),
        ),
        field_styles=dict(
            asctime=dict(color='magenta'),
            levelname=dict(color='blue', bold=True),
            name=dict(color='blue'),
        ),
        isatty=True,
    )
    log.info("Installed custom log handler!")


__all__ = (
    "install_log_handler",
)