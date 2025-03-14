import subprocess
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
    except Exception as e:
        try:
            cmd = ["termux-notification", "-t", title, "-c", message]
            _ = subprocess.run(cmd, check=True)
            log.info("Linux notification sent successfully")
        except Exception as e:
            log.fatal(f"Could not send notification on Linux: {e}")
