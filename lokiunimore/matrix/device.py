import socket


def generate_device_id(name: str) -> str:
    return f"{name}@{socket.gethostname()}"


def generate_device_name(name: str) -> str:
    return f"Loki [{name}] @ {socket.gethostname()}"


__all__ = (
    "generate_device_id",
    "generate_device_name",
)
