import shutil
from logging import getLogger

import pync  # pyright: ignore[reportMissingImports]

log = getLogger(__name__)


if not shutil.which("terminal-notifier"):
    raise ImportError("terminal-notifier not found. Install using brew!")
log.debug("pync module loaded successfully for macOS notifications")


def send_notification(message: str, title: str) -> None:
    """Send a notification on macOS systems"""
    assert isinstance(message, str), "Message must be a string"
    assert isinstance(title, str), "Title must be a string"

    if not pync:
        raise ImportError("pync package is required for macOS notifications")

    log.debug("Attempting to send macOS notification via pync")
    pync.notify(message, title=title)
    log.info("macOS notification sent successfully via pync")
