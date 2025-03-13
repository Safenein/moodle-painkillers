import requests as rq
from logging import getLogger
import bs4

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


class MoodleAuthenticatedSession(rq.Session):
    """
    A request class that automatically authenticates with a Moodle platform via Shibboleth authentication.
    This class extends the standard Request class from the requests library to provide
    automatic authentication with a Moodle platform using Shibboleth Single Sign-On.
    It's specifically designed for the University of South Brittany (Université de Bretagne Sud)
    Moodle platform but may work with other Shibboleth-enabled Moodle instances.
    The class implements the context manager protocol for proper resource management.
    Parameters:
        username (str): The username for Moodle authentication
        password (str): The password for Moodle authentication
        ...: Additional parameters are passed to the Request class
    Example:
        >>> with MoodleAuthenticatedSession("username", "password") as session:
        ...     response = session.get("https://moodle.univ-ubs.fr/my/")
        ...     # Use the authenticated session for further requests
        Exception: If authentication fails due to incorrect credentials or network issues
    """
    username: str
    password: str

    def __init__(self, username: str, password: str):
        assert isinstance(username, str), "Invalid username"
        assert isinstance(password, str), "Invalid password"

        self.username = username
        self.password = password
        super().__init__()

    def __enter__(self):
        self.authenticate_on_moodle(self.username, self.password)
        return self

    def __exit__(self, *_):
        self.close()

    def authenticate_on_moodle(
        self, username: str, password: str
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
        res = self.get(
            "https://moodle.univ-ubs.fr/auth/shibboleth/login.php",
        )

        if res.status_code != 200:
            log.error(f"Failed to get login page: HTTP {res.status_code}")
            raise Exception(f"{res.status_code} Failed to get login page")

        log.debug("Posting to Shibboleth login page")
        # Post the login form to be redirected on the shibboleth login page
        res = self.post(
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
        res = self.post(
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
        try:
            relaystate_value = get_hidden_input_value(soup, "RelayState")
            samlresponse_value = get_hidden_input_value(soup, "SAMLResponse")
        except ValueError as e:
            log.error("Failed to extract SAML response parameters")
            raise Exception("Failed to extract SAML response parameters. Are the credentials correct?") from e

        log.debug("Posting SAML response to service provider")
        res = self.post(
            "https://moodle.univ-ubs.fr/Shibboleth.sso/SAML2/POST",
            data={
                "RelayState": relaystate_value,
                "SAMLResponse": samlresponse_value,
            },
        )
        
        log.info("Authentication completed successfully")

