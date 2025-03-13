import platform
import subprocess
from logging import getLogger
from .discord import send_discord_notification

log = getLogger(__name__)


NOTIFICATION_TITLE = "Moodle Painkillers"


try:
    import shutil
    import pync
    if not shutil.which("terminal-notifier"):
        raise ImportError("terminal-notifier not found. Install using brew!")
    log.debug("pync module loaded successfully for macOS notifications")
except ImportError:
    pync = None
    log.warning("pync module not available, falling back to alternative methods for macOS")


try:
    from win10toast import ToastNotifier
    log.debug("win10toast module loaded successfully for Windows notifications")
except ImportError:
    ToastNotifier = None
    log.warning("win10toast module not available, Windows notifications may not work")


def _send_windows_notification(message: str):
    """Send a notification on Windows systems"""
    assert isinstance(message, str), "Message must be a string"

    if not ToastNotifier:
        return False

    log.debug("Attempting to send Windows notification")
    toaster = ToastNotifier()
    toaster.show_toast(NOTIFICATION_TITLE, message, duration=5)
    log.info("Windows notification sent successfully")
    return True

def _send_macos_notification(message: str):
    """Send a notification on macOS systems"""
    assert isinstance(message, str), "Message must be a string"

    if not pync:
        return False

    log.debug("Attempting to send macOS notification via pync")
    pync.notify(message, title=NOTIFICATION_TITLE)
    log.info("macOS notification sent successfully via pync")
    return True

def _send_linux_notification(message: str):
    """Send a notification on Linux systems"""
    assert isinstance(message, str), "Message must be a string"

    try:
        log.debug("Attempting to send Linux notification")
        cmd = ['notify-send', NOTIFICATION_TITLE, message]
        _ = subprocess.run(cmd, check=True)
        log.info("Linux notification sent successfully")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        log.fatal("Could not send notification on Linux")
        return False

def send_notification(message: str, *, discord_webhook: str | None = None):
    """
    Send a desktop notification with the given message across different operating systems.
    
    Dependencies:
        - Windows: win10toast package (pip install win10toast)
        - macOS: AppleScript or pync package (pip install pync)
        - Linux: notify-send command or PyGObject with libnotify
    
    Args:
        message (str): The message to display in the notification
        
    Returns:
        bool: True if notification was sent successfully, False otherwise
    """
    assert isinstance(message, str), "Message must be a string"
    assert isinstance(discord_webhook, str) or discord_webhook is None, "Discord webhook must be a string or None"
    system = platform.system()

    log.info(f"Sending notification: {message}")

    if discord_webhook:
        send_discord_notification(message, discord_webhook=discord_webhook)

    log.debug(f"Sending notification on {system} platform")
    
    try:
        if system == "Windows":
            return _send_windows_notification(message)
        elif system == "Darwin":  # macOS
            return _send_macos_notification(message)
        elif system == "Linux":
            return _send_linux_notification(message)
        else:
            log.warning(f"Notifications not supported on {system}")
            return False
            
    except Exception as e:
        log.exception(f"Failed to send notification: {e}")
        return False
