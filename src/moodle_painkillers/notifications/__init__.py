import platform
from logging import getLogger

from .discord import send_notification as send_discord_notification

log = getLogger(__name__)


match (platform.system()):
    case "Windows":
        from .windows import send_notification as _send_notification

        send_sys_notification = _send_notification
    case "Darwin":  # macOS
        from .macos import send_notification as _send_notification

        send_sys_notification = _send_notification
    case "Linux":
        from .linux import send_notification as _send_notification

        send_sys_notification = _send_notification
    case _ as system:
        log.warning(f"Desktop notifications not supported on {system}")

        def send_sys_notification(message: str, title: str) -> None:
            _ = message, title
            raise ImportError(
                f"Desktop notifications not supported on {system}"
            )


def send_notification(
    message: str, *, title: str, discord_webhook: str | None = None
) -> None:
    """
    Send a desktop notification with the given message across different operating systems.

    Dependencies:
        - Windows: win10toast package (pip install win10toast)
        - macOS: AppleScript or pync package (pip install pync)
        - Linux: notify-send command

    Args:
        message (str): The message to display in the notification

    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    assert isinstance(message, str), "Message must be a string"
    assert (
        isinstance(discord_webhook, str) or discord_webhook is None
    ), "Discord webhook must be a string or None"
    system = platform.system()

    log.info(f"Sending notification: {message}")

    if discord_webhook:
        send_discord_notification(message, discord_webhook=discord_webhook)

    log.debug(f"Sending notification on {system} platform")

    try:
        send_sys_notification(message, title)
    except ImportError as e:
        log.exception(f"Failed to setup notification: {e}")
        raise
    except Exception as e:
        log.exception(f"Failed to send notification: {e}")
        raise
