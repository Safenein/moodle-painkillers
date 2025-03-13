import bs4
import pytest
import requests

from moodle_painkillers.moodle_authenticate import (MoodleAuthenticatedSession,
                                                    get_hidden_input_value)


class TestGetHiddenInputValue:
    def test_get_hidden_input_value_valid(self):
        # Create a valid BeautifulSoup object with a hidden input
        html = '<html><form><input type="hidden" name="test_name" value="test_value"></form></html>'
        soup = bs4.BeautifulSoup(html, "html.parser")

        # Test valid retrieval
        assert get_hidden_input_value(soup, "test_name") == "test_value"

    def test_get_hidden_input_value_invalid_soup(self):
        # Test with invalid soup (not BeautifulSoup)
        with pytest.raises(AssertionError, match="Invalid soup"):
            get_hidden_input_value("not a soup", "test_name")

    def test_get_hidden_input_value_invalid_name(self):
        # Test with invalid name (not string)
        html = '<html><form><input type="hidden" name="test_name" value="test_value"></form></html>'
        soup = bs4.BeautifulSoup(html, "html.parser")

        with pytest.raises(AssertionError, match="Invalid name"):
            get_hidden_input_value(soup, 123)

    def test_get_hidden_input_value_element_not_found(self):
        # Test when element is not found
        html = '<html><form><input type="hidden" name="test_name" value="test_value"></form></html>'
        soup = bs4.BeautifulSoup(html, "html.parser")

        with pytest.raises(
            ValueError, match="Element nonexistent introuvable"
        ):
            get_hidden_input_value(soup, "nonexistent")

    def test_get_hidden_input_value_complex_html(self):
        # Test with more complex HTML
        html = """
        <html>
            <body>
                <form>
                    <div>
                        <input type="text" name="visible" value="visible_value">
                        <input type="hidden" name="hidden1" value="hidden1_value">
                        <input type="hidden" name="hidden2" value="hidden2_value">
                    </div>
                </form>
            </body>
        </html>
        """
        soup = bs4.BeautifulSoup(html, "html.parser")

        assert get_hidden_input_value(soup, "hidden1") == "hidden1_value"
        assert get_hidden_input_value(soup, "hidden2") == "hidden2_value"


class TestMoodleAuthenticatedSession:
    # __init__
    def test_init_valid_credentials(self):
        # Test initialization with valid credentials
        session = MoodleAuthenticatedSession("test_user", "test_pass")
        assert session.username == "test_user"
        assert session.password == "test_pass"

    def test_init_invalid_username(self):
        # Test with invalid username (not string)
        with pytest.raises(AssertionError, match="Invalid username"):
            MoodleAuthenticatedSession(123, "test_pass")

    def test_init_invalid_password(self):
        # Test with invalid password (not string)
        with pytest.raises(AssertionError, match="Invalid password"):
            MoodleAuthenticatedSession("test_user", 123)

    # __enter__
    def test_enter_method_exists(self):
        # Test that the __enter__ method exists and is callable
        session = MoodleAuthenticatedSession("test_user", "test_pass")
        assert hasattr(session, "__enter__")
        assert callable(session.__enter__)

    def test_enter_calls_authenticate(self, monkeypatch):
        # Test that __enter__ calls authenticate_on_moodle with correct credentials
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        # Track if authenticate_on_moodle is called with correct arguments
        auth_called = False

        def mock_authenticate(username, password):
            nonlocal auth_called
            if username == "test_user" and password == "test_pass":
                auth_called = True

        # Replace authenticate_on_moodle with our mock
        monkeypatch.setattr(
            session, "authenticate_on_moodle", mock_authenticate
        )

        # Call __enter__
        session.__enter__()  # these params should be ignored

        # Verify authenticate was called with credentials from __init__
        assert (
            auth_called
        ), "authenticate_on_moodle was not called with correct credentials"

    def test_enter_returns_self(self, monkeypatch):
        # Test that __enter__ returns the session object itself
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        # Mock authenticate_on_moodle to prevent actual authentication
        def mock_authenticate(username, password):
            pass

        monkeypatch.setattr(
            session, "authenticate_on_moodle", mock_authenticate
        )

        # Call __enter__
        result = session.__enter__()

        # Verify it returns self
        assert (
            result is session
        ), "__enter__ should return the session object itself"

    # __exit__
    def test_exit_method_exists(self):
        # Test that the __exit__ method exists and is callable
        session = MoodleAuthenticatedSession("test_user", "test_pass")
        assert hasattr(session, "__exit__")
        assert callable(session.__exit__)

    def test_exit_calls_close(self, monkeypatch):
        # Test that __exit__ calls the close method
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        # Track if close is called
        close_called = False

        def mock_close():
            nonlocal close_called
            close_called = True

        # Replace close method with our mock
        monkeypatch.setattr(session, "close", mock_close)

        # Call __exit__
        session.__exit__(None, None, None)

        # Verify close was called
        assert close_called, "Session close method was not called by __exit__"

    # authenticate_on_moodle
    def test_authenticate_on_moodle_success(self, monkeypatch):
        """Test successful authentication flow"""
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        # Mock all requests in the authentication flow
        def mock_get(*args, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = (
                b"<html><body>Mock login page</body></html>"
            )
            return mock_response

        def mock_post(url, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200

            if "login.php" in url:
                # First POST response (to login page)
                mock_response.url = "mock_url?param=value"
                mock_response._content = b'<html><body><input type="hidden" name="execution" value="mock_execution"></body></html>'
            elif url.endswith("SAML2/POST"):
                # Final POST response
                pass
            else:
                # Second POST response (after submitting credentials)
                mock_response.url = "mock_url?param=value"
                mock_response._content = b'<html><body><input type="hidden" name="RelayState" value="mock_relay"><input type="hidden" name="SAMLResponse" value="mock_saml"></body></html>'

            return mock_response

        # Apply mocks
        monkeypatch.setattr(session, "get", mock_get)
        monkeypatch.setattr(session, "post", mock_post)

        # Call method - should not raise exceptions
        session.authenticate_on_moodle("test_user", "test_pass")

    def test_authenticate_fail_initial_get(self, monkeypatch):
        """Test failure on initial GET request"""
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        def mock_get(*args, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 404  # Failure status
            return mock_response

        monkeypatch.setattr(session, "get", mock_get)

        with pytest.raises(Exception, match="404 Failed to get login page"):
            session.authenticate_on_moodle("test_user", "test_pass")

    def test_authenticate_fail_login_post(self, monkeypatch):
        """Test failure on login page POST request"""
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        def mock_get(*args, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200
            return mock_response

        def mock_post(url, **kwargs):
            mock_response = requests.Response()
            if "login.php" in url:
                mock_response.status_code = 500  # Failure status
            return mock_response

        monkeypatch.setattr(session, "get", mock_get)
        monkeypatch.setattr(session, "post", mock_post)

        with pytest.raises(
            Exception, match="500 Failed to authenticate on login page"
        ):
            session.authenticate_on_moodle("test_user", "test_pass")

    def test_authenticate_fail_saml_extraction(self, monkeypatch):
        """Test failure when extracting SAML parameters (incorrect credentials)"""
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        def mock_get(*args, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = (
                b"<html><body>Mock login page</body></html>"
            )
            return mock_response

        def mock_post(url, **kwargs):
            mock_response = requests.Response()
            mock_response.status_code = 200

            if "login.php" in url:
                # First POST response (to login page)
                mock_response.url = "mock_url?param=value"
                mock_response._content = b'<html><body><input type="hidden" name="execution" value="mock_execution"></body></html>'
            else:
                # Second POST response - missing SAML parameters
                mock_response.url = "mock_url?param=value"
                mock_response._content = (
                    b"<html><body>Invalid credentials</body></html>"
                )

            return mock_response

        monkeypatch.setattr(session, "get", mock_get)
        monkeypatch.setattr(session, "post", mock_post)

        with pytest.raises(
            Exception,
            match="Failed to extract SAML response parameters. Are the credentials correct?",
        ):
            session.authenticate_on_moodle("test_user", "test_pass")

    def test_authenticate_sends_correct_parameters(self, monkeypatch):
        """Test that correct parameters are sent in authentication requests"""
        session = MoodleAuthenticatedSession("test_user", "test_pass")

        # Track request parameters
        get_url = None
        post_urls = []
        post_data = []

        def mock_get(url, **kwargs):
            nonlocal get_url
            get_url = url

            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = (
                b"<html><body>Mock login page</body></html>"
            )
            return mock_response

        def mock_post(url, **kwargs):
            post_urls.append(url)
            post_data.append(kwargs.get("data", {}))

            mock_response = requests.Response()
            mock_response.status_code = 200

            if len(post_urls) == 1:
                # First POST response
                mock_response.url = "mock_url?param=value"
                mock_response._content = b'<html><body><input type="hidden" name="execution" value="mock_execution"></body></html>'
            elif len(post_urls) == 2:
                # Second POST response
                mock_response.url = "mock_url?param=value"
                mock_response._content = b'<html><body><input type="hidden" name="RelayState" value="mock_relay"><input type="hidden" name="SAMLResponse" value="mock_saml"></body></html>'

            return mock_response

        # Apply mocks
        monkeypatch.setattr(session, "get", mock_get)
        monkeypatch.setattr(session, "post", mock_post)

        # Call method
        session.authenticate_on_moodle("test_user", "test_pass")

        # Verify correct URLs and parameters
        assert (
            get_url == "https://moodle.univ-ubs.fr/auth/shibboleth/login.php"
        )
        assert (
            post_urls[0]
            == "https://moodle.univ-ubs.fr/auth/shibboleth/login.php"
        )
        assert post_data[0] == {
            "idp": "urn:mace:cru.fr:federation:univ-ubs.fr"
        }
        assert post_data[1] == {
            "username": "test_user",
            "password": "test_pass",
            "execution": "mock_execution",
            "_eventId": "submit",
            "geolocation": "",
        }
        assert post_data[2] == {
            "RelayState": "mock_relay",
            "SAMLResponse": "mock_saml",
        }
