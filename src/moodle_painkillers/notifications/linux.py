import subprocess
import shutil
from logging import getLogger

log = getLogger(__name__)


def send_notification(message: str, title: str) -> None:
    """Send a notification on Linux systems"""
    assert isinstance(message, str), "Message must be a string"
    assert isinstance(title, str), "Title must be a string"

    try:
        log.debug("Attempting to send Linux notification")
        cmd = ["notify-send", title, message]
        _ = subprocess.run(cmd, check=True)
        log.info("Linux notification sent successfully")
    except subprocess.SubprocessError as e:
        log.fatal(f"Could not send notification on Linux: {e}")
        raise
    except FileNotFoundError as e:
        log.fatal(f"Could not send notification on Linux: {e}")
        raise ImportError(
            "notify-send command not found. Please install libnotify package"
        )
