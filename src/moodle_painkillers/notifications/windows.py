from logging import getLogger

import win10toast  # pyright: ignore[reportMissingImports]

log = getLogger(__name__)


def send_notification(message: str, title: str) -> None:
    """Send a notification on Windows systems"""
    assert isinstance(message, str), "Message must be a string"
    assert isinstance(title, str), "Title must be a string"

    if not win10toast:
        raise ImportError(
            "win10toast package is required for Windows notifications"
        )

    log.debug("Attempting to send Windows notification")
    toaster = win10toast.ToastNotifier()
    toaster.show_toast(title, message, duration=5)
    log.info("Windows notification sent successfully")
