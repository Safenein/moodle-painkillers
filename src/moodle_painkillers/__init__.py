import os
import requests as rq
from logging import getLogger
from dataclasses import dataclass
import bs4
import argparse


log = getLogger(__name__)


def get_hidden_input_value(soup: bs4.BeautifulSoup, name: str) -> str:
    """
    Retrieve the value of a hidden input element from a BeautifulSoup object.

    Args:
        soup (bs4.BeautifulSoup): The BeautifulSoup object containing the HTML.
        name (str): The name attribute of the hidden input element to find.

    Returns:
        str: The value of the hidden input element.

    Raises:
        AssertionError: If the soup is not a BeautifulSoup object or name is not a string.
        ValueError: If the hidden input element with the specified name is not found.
    """
    log.debug(f"Getting hidden input value for element named '{name}'")
    assert isinstance(soup, bs4.BeautifulSoup), "Invalid soup"
    assert isinstance(name, str), "Invalid name"

    input_element = soup.find("input", {"type": "hidden", "name": name})

    if not input_element:
        log.error(f"Hidden input element '{name}' not found in the HTML")
        raise ValueError(f"Element {name} introuvable")

    assert isinstance(input_element, bs4.element.Tag)
    value = input_element["value"]

    assert isinstance(value, str), "Invalid value"
    log.debug(f"Found hidden input value for '{name}'")
    return value


def authenticate_on_moodle(
    session: rq.Session, username: str, password: str
) -> None:
    """
    Authenticate a user on the Moodle platform using Shibboleth.

    This function performs a series of HTTP requests to authenticate a user on the Moodle platform
    of the University of South Brittany (Université de Bretagne Sud) using Shibboleth.

    Args:
        session (rq.Session): The requests session object to maintain the session.
        username (str): The username of the user.
        password (str): The password of the user.

    Raises:
        Exception: If any of the HTTP requests fail (status code is not 200).

    Returns:
        None
    """
    log.info("Starting Moodle authentication process")
    log.debug(f"Authenticating user: {username}")
    
    log.debug("Requesting Shibboleth login page")
    res = session.get(
        "https://moodle.univ-ubs.fr/auth/shibboleth/login.php",
    )

    if res.status_code != 200:
        log.error(f"Failed to get login page: HTTP {res.status_code}")
        raise Exception(f"{res.status_code} Failed to get login page")

    log.debug("Posting to Shibboleth login page")
    # Post the login form to be redirected on the shibboleth login page
    res = session.post(
        "https://moodle.univ-ubs.fr/auth/shibboleth/login.php",
        cookies=res.cookies,
        data={"idp": "urn:mace:cru.fr:federation:univ-ubs.fr"},
    )

    if res.status_code != 200:
        log.error(f"Failed to authenticate on login page: HTTP {res.status_code}")
        raise Exception(
            f"{res.status_code} Failed to authenticate on login page"
        )

    log.debug("Parsing login response page")
    soup = bs4.BeautifulSoup(res.text, "html.parser")

    execution_value = get_hidden_input_value(soup, "execution")

    log.debug("Submitting credentials to Shibboleth")
    # Authenticate on shibboleth
    res = session.post(
        res.url.split("?")[0],
        data={
            "username": username,
            "password": password,
            "execution": execution_value,
            "_eventId": "submit",
            "geolocation": "",
        },
    )

    log.debug("Parsing authentication response")
    soup = bs4.BeautifulSoup(res.text, "html.parser")

    log.debug("Extracting SAML response parameters")
    relaystate_value = get_hidden_input_value(soup, "RelayState")
    samlresponse_value = get_hidden_input_value(soup, "SAMLResponse")

    log.debug("Posting SAML response to service provider")
    res = session.post(
        "https://moodle.univ-ubs.fr/Shibboleth.sso/SAML2/POST",
        data={
            "RelayState": relaystate_value,
            "SAMLResponse": samlresponse_value,
        },
    )
    
    log.info("Authentication completed successfully")


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
    discord_webhook: str


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
    parser.add_argument("--username", "-u", help="Moodle username")
    parser.add_argument("--password", "-p", help="Moodle password")
    parser.add_argument("--discord-webhook", "-w", help="Discord webhook URL for notifications")
    args = parser.parse_args()
    
    # Get credentials from environment variables as fallback
    moodle_username = args.username or os.getenv("MOODLE_USERNAME") or ""
    moodle_password = args.password or os.getenv("MOODLE_PASSWORD") or ""
    discord_webhook = args.discord_webhook or os.getenv("DISCORD_WEBHOOK") or ""

    log.debug("Checking if credentials are provided")
    if not moodle_username or not moodle_password:
        log.error("Missing Moodle credentials")
        raise NameError("Missing Moodle credentials. Provide them via command line arguments or environment variables.")
    
    log.debug("Arguments parsed successfully")
    return Args(username=moodle_username, password=moodle_password, discord_webhook=discord_webhook)


def main(args: Args | None = None):
    """
    Main function to authenticate on Moodle and register presence status.

    This function retrieves the Moodle username and password from environment variables,
    opens a session, authenticates on Moodle, registers the presence status, and then
    closes the session.

    Raises:
        NameError: If either MOODLE_USERNAME or MOODLE_PASSWORD environment variables are missing.
    """
    log.info("Starting Moodle presence registration process")

    # Get moodle username and password from environment variables
    args = args or parse_args()
    log.debug("Arguments obtained")

    # Open a session
    log.debug("Creating new HTTP session")
    session = rq.Session()

    # Authenticate on moodle
    authenticate_on_moodle(session, args.username, args.password)

    # Register presence status
    register_presence_status(session)

    log.debug("Closing HTTP session")
    session.close()
    
    log.info("Presence registration process completed successfully")

    return


if __name__ == "__main__":
    main(None)
