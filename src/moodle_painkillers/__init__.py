import os
import requests as rq
import logging
from dataclasses import dataclass
import bs4
import argparse
from typing import Any, Callable

from .desktop_notifications import send_notification
from .moodle_authenticate import MoodleAuthenticatedSession


log = logging.getLogger(__name__)


try:
    from rich.traceback import install as install_rich_traceback
    from rich.logging import RichHandler
    
    # Install rich traceback for better exception visualization
    _ = install_rich_traceback(show_locals=True)
    
    # Set up rich logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    logger = logging.getLogger("moodle_painkillers")
    logger.info("Rich logger and traceback installed")
except ImportError:
    # Rich is not available, use standard logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("moodle_painkillers")
    logger.info("Standard logging initialized (Rich not available)")



def register_presence_status(session: rq.Session) -> None:
    """
    Registers the presence status for a session on Moodle.

    This function sends a GET request to the Moodle attendance page and parses
    the HTML to find the link for sending the presence status. It then sends
    another GET request to that link to register the presence status.

    Args:
        session (rq.Session): The requests session object used to make HTTP requests.

    Raises:
        Exception: If the link to send the presence status cannot be found.
        Exception: If the presence status registration fails.
    """
    log.info("Starting presence status registration process")
    
    log.debug("Requesting attendance page")
    res = session.get(
        "https://moodle.univ-ubs.fr/mod/attendance/view.php?id=433340"
    )

    log.debug("Parsing attendance page")
    soup = bs4.BeautifulSoup(res.text, "html.parser")

    log.debug("Looking for presence status link")
    a_element = soup.find("a", string="Envoyer le statut de présence")
    if not a_element:
        log.error("Could not find the presence status link on the page")
        raise Exception("Could not find the send status cell. Did you already checked in?")
    assert isinstance(a_element, bs4.element.Tag)

    link_status_href = a_element["href"]
    assert isinstance(link_status_href, str)
    log.debug(f"Found presence status link: {link_status_href}")

    log.debug("Sending presence status request")
    res = session.get(link_status_href)
    if "Votre présence à cette session a été enregistrée." not in res.text:
        log.error("Failed to register presence status")
        raise Exception("Failed to register presence status.")

    log.info("Successfully registered presence status")


@dataclass
class Args:
    """
    A class that stores authentication credentials for Moodle.

    Attributes:
        username (str): The username for Moodle authentication.
        password (str): The password for Moodle authentication.
        discord_webhook (str): The Discord webhook URL for notifications.

    """
    username: str
    password: str
    discord_webhook: str | None


def parse_args():
    """
    Parse command line arguments for Moodle credentials.
    The function checks for username and password in the following order:
    1. Command line arguments
    2. Environment variables (MOODLE_USERNAME, MOODLE_PASSWORD)
    Returns:
        Args: An object containing the Moodle username and password.
    Raises:
        NameError: If either username or password is missing from both
                   command line arguments and environment variables.
    """
    log.debug("Parsing command line arguments")
    parser = argparse.ArgumentParser(description="Moodle presence registration tool")
    _ = parser.add_argument("--username", "-u", help="Moodle username", type=str)
    _ = parser.add_argument("--password", "-p", help="Moodle password", type=str)
    _ = parser.add_argument("--discord-webhook", "-w", help="Discord webhook URL for notifications", type=str)
    args = parser.parse_args()

    # Get credentials from environment variables as fallback
    moodle_username = args.username or os.getenv("MOODLE_USERNAME") or ""
    moodle_password = args.password or os.getenv("MOODLE_PASSWORD") or ""
    discord_webhook = args.discord_webhook or os.getenv("DISCORD_WEBHOOK")

    log.debug("Checking if credentials are provided")
    if not moodle_username or not moodle_password:
        log.error("Missing Moodle credentials")
        raise NameError("Missing Moodle credentials. Provide them via command line arguments or environment variables.")
    
    log.debug("Arguments parsed successfully")
    return Args(username=moodle_username, password=moodle_password, discord_webhook=discord_webhook)


def notify_on_fail(func: Callable[[Any], Any]):
    """
    Decorator to send a notification in case of failure.

    Args:
        func (callable): The function to decorate.

    Returns:
        callable: The decorated function.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"An error occurred: {str(e)}")
            _ = send_notification(str(e))
            raise e
    return wrapper


@notify_on_fail
def main() -> None:
    """
    Execute the Moodle presence registration workflow.
    This function orchestrates the entire process of registering a presence status on Moodle:
    1. Retrieves credentials and arguments from command line or environment variables
    2. Creates an HTTP session
    3. Authenticates to the Moodle platform
    4. Registers the user's presence status
    5. Sends a notification upon successful completion
    Returns:
        None
    Side Effects:
        - Creates and closes an HTTP session
        - Authenticates to Moodle
        - Registers presence on Moodle
        - Logs information about the process
        - Sends a notification when complete
    """
    log.info("Starting Moodle presence registration process")

    # Get moodle username and password from environment variables
    args = parse_args()

    log.debug("Arguments obtained")

    # Open a session
    log.debug("Creating new HTTP session")
    # Authenticate on moodle
    with MoodleAuthenticatedSession(args.username, args.password) as session:
        log.debug("Authenticated on Moodle")

        # Register presence status
        register_presence_status(session)
    
    log.info("Presence registration process completed successfully")
    _ = send_notification("Sent presence status!", discord_webhook=args.discord_webhook)

    return


if __name__ == "__main__":
    main()
