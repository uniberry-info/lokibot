"""
Executable that displays the current configuration.
"""

from .config import config


def main():
    config.cli()


if __name__ == "__main__":
    main()
