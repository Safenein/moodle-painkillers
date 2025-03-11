import platform
import subprocess
from logging import getLogger

log = getLogger(__name__)

try:
    import pync
    macos_notification=True
except ImportError:
    macos_notification=False
try:
    from win10toast import ToastNotifier
    windows_notification=True
except ImportError:
    windows_notification=False


def _send_windows_notification(message):
    """Send a notification on Windows systems"""
    try:
        toaster = ToastNotifier()
        toaster.show_toast("Notification", message, duration=5)
        return True
    except ImportError:
        print("win10toast package is required for Windows notifications. "
              "Install it with: pip install win10toast")
        return False

def _send_macos_notification(message):
    """Send a notification on macOS systems"""
    try:
        pync.notify(message, title="Notification")
        return True
    except ImportError:
        try:
            cmd = ['osascript', '-e', f'display notification "{message}" with title "Notification"']
            subprocess.run(cmd, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Could not send notification on macOS")
            return False

def _send_linux_notification(message):
    """Send a notification on Linux systems"""
    try:
        cmd = ['notify-send', 'Notification', message]
        subprocess.run(cmd, check=True)
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
    
    system = platform.system()
    
    try:
        if system == "Windows" and windows_notification:
            return _send_windows_notification(message)
        elif system == "Darwin" and macos_notification:  # macOS
            return _send_macos_notification(message)
        elif system == "Linux":
            return _send_linux_notification(message)
        else:
            print(f"Notifications not supported on {system}")
            return False
            
    except Exception as e:
        print(f"Failed to send notification: {e}")
        return False