import socket


def generate_device_name(name: str) -> str:
    """
    Generate a human-readable device name from the machine's hostname and a given name to use as `display name for Matrix clients <https://spec.matrix.org/latest/#devices>`_.
    """
    return f"Loki [{name}] @ {socket.gethostname()}"


__all__ = (
    "generate_device_name",
)
