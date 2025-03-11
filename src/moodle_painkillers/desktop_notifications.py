import platform
import subprocess
from logging import getLogger

log = getLogger(__name__)

try:
    import pync
    macos_notification=True
    log.debug("pync module loaded successfully for macOS notifications")
except ImportError:
    macos_notification=False
    log.warning("pync module not available, falling back to alternative methods for macOS")
try:
    from win10toast import ToastNotifier
    windows_notification=True
    log.debug("win10toast module loaded successfully for Windows notifications")
except ImportError:
    windows_notification=False
    log.warning("win10toast module not available, Windows notifications may not work")


def _send_windows_notification(message):
    """Send a notification on Windows systems"""
    try:
        log.debug("Attempting to send Windows notification")
        toaster = ToastNotifier()
        toaster.show_toast("Notification", message, duration=5)
        log.info("Windows notification sent successfully")
        return True
    except ImportError:
        log.error("win10toast package is required for Windows notifications. "
                  "Install it with: pip install win10toast")
        return False

def _send_macos_notification(message):
    """Send a notification on macOS systems"""
    try:
        log.debug("Attempting to send macOS notification via pync")
        pync.notify(message, title="Notification")
        log.info("macOS notification sent successfully via pync")
        return True
    except ImportError:
        log.warning("pync not available, falling back to AppleScript for macOS notification")
        try:
            cmd = ['osascript', '-e', f'display notification "{message}" with title "Notification"']
            subprocess.run(cmd, check=True)
            log.info("macOS notification sent successfully via AppleScript")
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            log.error("Could not send notification on macOS")
            return False

def _send_linux_notification(message):
    """Send a notification on Linux systems"""
    try:
        log.debug("Attempting to send Linux notification")
        cmd = ['notify-send', 'Notification', message]
        subprocess.run(cmd, check=True)
        log.info("Linux notification sent successfully")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        log.fatal("Could not send notification on Linux")
        return False

def send_notification(message):
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
    if not isinstance(message, str):
        message = str(message)
        log.debug(f"Converted non-string message to string: {message}")
    
    system = platform.system()
    log.debug(f"Sending notification on {system} platform")
    
    try:
        if system == "Windows" and windows_notification:
            return _send_windows_notification(message)
        elif system == "Darwin" and macos_notification:  # macOS
            return _send_macos_notification(message)
        elif system == "Linux":
            return _send_linux_notification(message)
        else:
            log.warning(f"Notifications not supported on {system}")
            return False
            
    except Exception as e:
        log.exception(f"Failed to send notification: {e}")
        return False