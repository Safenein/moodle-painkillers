import pytest
import bs4
import requests as rq
from unittest.mock import Mock, patch
from moodle_painkillers import (
    authenticate_on_moodle,
    register_presence_status,
    get_hidden_input_value,
    main,
    parse_args,
)


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

        with pytest.raises(ValueError, match="Element nonexistent introuvable"):
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


class TestAuthenticateOnMoodle:

    def test_authenticate_successful(self):
        # Mock session and responses
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.cookies = {"cookie": "value"}

        # Mock the first POST response
        mock_post_response1 = Mock()
        mock_post_response1.status_code = 200
        mock_post_response1.text = """
            <html><form>
                <input type="hidden" name="execution" value="execution_value">
            </form></html>
        """
        mock_post_response1.url = "https://example.com/login?param=1"

        # Mock the second POST response (authentication)
        mock_post_response2 = Mock()
        mock_post_response2.status_code = 200
        mock_post_response2.text = """
            <html><form>
                <input type="hidden" name="RelayState" value="relay_state_value">
                <input type="hidden" name="SAMLResponse" value="saml_response_value">
            </form></html>
        """

        # Mock the final POST response
        mock_post_response3 = Mock()
        mock_post_response3.status_code = 200

        # Set up the session mock to return our mocked responses
        mock_session.get.return_value = mock_get_response
        mock_session.post.side_effect = [
            mock_post_response1,
            mock_post_response2,
            mock_post_response3,
        ]

        # Call the function
        authenticate_on_moodle(mock_session, "test_username", "test_password")

        # Verify correct calls were made
        mock_session.get.assert_called_once_with(
            "https://moodle.univ-ubs.fr/auth/shibboleth/login.php",
        )

        assert mock_session.post.call_count == 3

        # Verify first POST call
        mock_session.post.assert_any_call(
            "https://moodle.univ-ubs.fr/auth/shibboleth/login.php",
            cookies=mock_get_response.cookies,
            data={"idp": "urn:mace:cru.fr:federation:univ-ubs.fr"},
        )

        # Verify second POST call (authentication)
        mock_session.post.assert_any_call(
            "https://example.com/login",  # URL without parameters
            data={
                "username": "test_username",
                "password": "test_password",
                "execution": "execution_value",
                "_eventId": "submit",
                "geolocation": "",
            },
        )

        # Verify third POST call
        mock_session.post.assert_any_call(
            "https://moodle.univ-ubs.fr/Shibboleth.sso/SAML2/POST",
            data={
                "RelayState": "relay_state_value",
                "SAMLResponse": "saml_response_value",
            },
        )

    def test_get_login_page_failure(self):
        # Test failure when getting the login page fails
        mock_session = Mock(spec=rq.Session)

        # Mock a failed GET response
        mock_get_response = Mock()
        mock_get_response.status_code = 404
        mock_session.get.return_value = mock_get_response

        # Verify exception is raised
        with pytest.raises(Exception, match="404 Failed to get login page"):
            authenticate_on_moodle(
                mock_session, "test_username", "test_password"
            )

    def test_post_login_failure(self):
        # Test failure when posting to the login page fails
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response (success)
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.cookies = {"cookie": "value"}

        # Mock the first POST response (failure)
        mock_post_response = Mock()
        mock_post_response.status_code = 500

        # Set up the session mock
        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response

        # Verify exception is raised
        with pytest.raises(
            Exception, match="500 Failed to authenticate on login page"
        ):
            authenticate_on_moodle(
                mock_session, "test_username", "test_password"
            )

    def test_missing_execution_value(self):
        # Test when execution value is missing in response
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.cookies = {"cookie": "value"}

        # Mock the first POST response with missing execution field
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.text = (
            "<html><form></form></html>"  # No execution input
        )

        # Set up the session mock
        mock_session.get.return_value = mock_get_response
        mock_session.post.return_value = mock_post_response

        # Verify exception is raised when the execution value is not found
        with pytest.raises(ValueError, match="Element execution introuvable"):
            authenticate_on_moodle(
                mock_session, "test_username", "test_password"
            )

    def test_missing_relay_state_value(self):
        # Test when RelayState value is missing in response
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.cookies = {"cookie": "value"}

        # Mock the first POST response
        mock_post_response1 = Mock()
        mock_post_response1.status_code = 200
        mock_post_response1.text = """
            <html><form>
                <input type="hidden" name="execution" value="execution_value">
            </form></html>
        """
        mock_post_response1.url = "https://example.com/login"

        # Mock the second POST response with missing RelayState
        mock_post_response2 = Mock()
        mock_post_response2.status_code = 200
        mock_post_response2.text = """
            <html><form>
                <input type="hidden" name="SAMLResponse" value="saml_response_value">
            </form></html>
        """

        # Set up the session mock
        mock_session.get.return_value = mock_get_response
        mock_session.post.side_effect = [
            mock_post_response1,
            mock_post_response2,
        ]

        # Verify exception is raised when RelayState is not found
        with pytest.raises(ValueError, match="Element RelayState introuvable"):
            authenticate_on_moodle(
                mock_session, "test_username", "test_password"
            )


class TestRegisterPresenceStatus:
    @patch("moodle_painkillers.bs4.BeautifulSoup")
    def test_register_presence_success(self, mock_bs):

        # Mock session
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response (attendance page)
        mock_attendance_response = Mock()
        mock_attendance_response.text = "HTML content"

        # Mock the second GET response (status registration)
        mock_status_response = Mock()
        mock_status_response.text = (
            "Votre présence à cette session a été enregistrée."
        )

        # Configure session.get to return our mocked responses
        mock_session.get.side_effect = [
            mock_attendance_response,
            mock_status_response,
        ]

        # Configure BeautifulSoup and element mocks
        mock_soup = Mock()
        mock_bs.return_value = mock_soup

        mock_a_element = Mock(spec=bs4.element.Tag)
        mock_a_element.get.return_value = "https://example.com/status/link"
        mock_a_element.__getitem__ = lambda x,y: mock_a_element.get.return_value
        mock_soup.find.return_value = mock_a_element

        # Call the function
        register_presence_status(mock_session)

        # Verify the requests were made correctly
        mock_session.get.assert_any_call(
            "https://moodle.univ-ubs.fr/mod/attendance/view.php?id=433340"
        )
        mock_session.get.assert_any_call("https://example.com/status/link")

        # Verify BeautifulSoup was called with the response text
        mock_bs.assert_called_once_with(
            mock_attendance_response.text, "html.parser"
        )

        # Verify soup.find was called with correct parameters
        mock_soup.find.assert_called_once_with(
            "a", string="Envoyer le statut de présence"
        )

    def test_link_not_found(self):

        # Mock session
        mock_session = Mock(spec=rq.Session)

        # Mock GET response
        mock_response = Mock()
        mock_response.text = "<html><body>No link here</body></html>"
        mock_session.get.return_value = mock_response

        # Call the function and verify it raises the expected exception
        with pytest.raises(
            Exception, match="Could not find the send status cell."
        ):
            register_presence_status(mock_session)

    def test_registration_failed(self):

        # Mock session
        mock_session = Mock(spec=rq.Session)

        # Mock the first GET response
        mock_attendance_response = Mock()
        mock_attendance_response.text = "<html><body><a href='link'>Envoyer le statut de présence</a></body></html>"

        # Mock the second GET response (without success message)
        mock_status_response = Mock()
        mock_status_response.text = "Some error occurred"

        # Configure session.get to return our mocked responses
        mock_session.get.side_effect = [
            mock_attendance_response,
            mock_status_response,
        ]

        # Call the function and verify it raises the expected exception
        with pytest.raises(
            Exception, match="Failed to register presence status."
        ):
            register_presence_status(mock_session)


class TestMain:
    @patch("moodle_painkillers.os.getenv")
    @patch("moodle_painkillers.rq.Session")
    @patch("moodle_painkillers.authenticate_on_moodle")
    @patch("moodle_painkillers.register_presence_status")
    def test_main_successful(
        self, mock_register, mock_auth, mock_session, mock_getenv
    ):
        # Mock environment variables
        mock_getenv.side_effect = lambda x: (
            "test_value"
            if x in ("MOODLE_USERNAME", "MOODLE_PASSWORD")
            else None
        )

        # Mock session
        mock_session_instance = mock_session.return_value

        # Call the main function
        main()

        # Verify all steps were called
        mock_auth.assert_called_once_with(
            mock_session_instance, "test_value", "test_value"
        )
        mock_register.assert_called_once_with(mock_session_instance)
        mock_session_instance.close.assert_called_once()

    @patch("moodle_painkillers.os.getenv")
    def test_main_missing_username(self, mock_getenv):
        # Mock missing username
        mock_getenv.side_effect = lambda x: (
            "test_value" if x == "MOODLE_PASSWORD" else ""
        )

        # Call the main function and verify it raises NameError
        with pytest.raises(
            NameError, match="Missing Moodle credentials. Provide them via command line arguments or environment variables."
        ):
            main()

    @patch("moodle_painkillers.os.getenv")
    def test_main_missing_password(self, mock_getenv):
        # Mock missing password
        mock_getenv.side_effect = lambda x: (
            "test_value" if x == "MOODLE_USERNAME" else ""
        )

        # Call the main function and verify it raises NameError
        with pytest.raises(
            NameError, match="Missing Moodle credentials. Provide them via command line arguments or environment variables."
        ):
            main()

    @patch("moodle_painkillers.os.getenv")
    @patch("moodle_painkillers.rq.Session")
    @patch("moodle_painkillers.authenticate_on_moodle")
    def test_main_authentication_failure(
        self, mock_auth, mock_session, mock_getenv
    ):
        # Mock environment variables
        mock_getenv.side_effect = lambda x: (
            "test_value"
            if x in ("MOODLE_USERNAME", "MOODLE_PASSWORD")
            else None
        )

        # Mock authentication failure
        mock_auth.side_effect = Exception("Authentication failed")

        # Call the main function and verify it propagates the exception
        with pytest.raises(Exception, match="Authentication failed"):
            main()

    @patch("moodle_painkillers.os.getenv")
    @patch("moodle_painkillers.rq.Session")
    @patch("moodle_painkillers.authenticate_on_moodle")
    @patch("moodle_painkillers.register_presence_status")
    def test_main_registration_failure(
        self, mock_register, mock_auth, mock_session, mock_getenv
    ):
        # Mock environment variables
        mock_getenv.side_effect = lambda x: (
            "test_value"
            if x in ("MOODLE_USERNAME", "MOODLE_PASSWORD")
            else None
        )

        # Mock registration failure
        mock_register.side_effect = Exception("Registration failed")

        # Call the main function and verify it propagates the exception
        with pytest.raises(Exception, match="Registration failed"):
            main()
            class TestParseArgs:
                @patch("moodle_painkillers.argparse.ArgumentParser")
                @patch("moodle_painkillers.os.getenv")
                def test_parse_args_command_line(self, mock_getenv, mock_argparser):
                    # Setup mock for command line args
                    mock_args = Mock()
                    mock_args.username = "cli_user"
                    mock_args.password = "cli_pass"
                    mock_parser = Mock()
                    mock_parser.parse_args.return_value = mock_args
                    mock_argparser.return_value = mock_parser
                    
                    # Ensure environment vars aren't used
                    mock_getenv.return_value = None
                    
                    # Call function
                    result = parse_args()
                    
                    # Verify results
                    assert result.username == "cli_user"
                    assert result.password == "cli_pass"
                    mock_getenv.assert_not_called()  # Environment vars shouldn't be checked
                
                @patch("moodle_painkillers.argparse.ArgumentParser")
                @patch("moodle_painkillers.os.getenv")
                def test_parse_args_environment_vars(self, mock_getenv, mock_argparser):
                    # Setup mock for command line args (none provided)
                    mock_args = Mock()
                    mock_args.username = None
                    mock_args.password = None
                    mock_parser = Mock()
                    mock_parser.parse_args.return_value = mock_args
                    mock_argparser.return_value = mock_parser
                    
                    # Setup environment vars
                    mock_getenv.side_effect = lambda key: {
                        "MOODLE_USERNAME": "env_user",
                        "MOODLE_PASSWORD": "env_pass"
                    }.get(key)
                    
                    # Call function
                    result = parse_args()
                    
                    # Verify results
                    assert result.username == "env_user"
                    assert result.password == "env_pass"
                    mock_getenv.assert_any_call("MOODLE_USERNAME")
                    mock_getenv.assert_any_call("MOODLE_PASSWORD")
                
                @patch("moodle_painkillers.argparse.ArgumentParser")
                @patch("moodle_painkillers.os.getenv")
                def test_parse_args_precedence(self, mock_getenv, mock_argparser):
                    # Setup mock for command line args (username only)
                    mock_args = Mock()
                    mock_args.username = "cli_user"
                    mock_args.password = None
                    mock_parser = Mock()
                    mock_parser.parse_args.return_value = mock_args
                    mock_argparser.return_value = mock_parser
                    
                    # Setup environment vars (both username and password)
                    mock_getenv.side_effect = lambda key: {
                        "MOODLE_USERNAME": "env_user",
                        "MOODLE_PASSWORD": "env_pass"
                    }.get(key)
                    
                    # Call function
                    result = parse_args()
                    
                    # Verify results - CLI username should take precedence
                    assert result.username == "cli_user"
                    assert result.password == "env_pass"
                
                @patch("moodle_painkillers.argparse.ArgumentParser")
                @patch("moodle_painkillers.os.getenv")
                def test_parse_args_missing_username(self, mock_getenv, mock_argparser):
                    # Setup mock for command line args (none provided)
                    mock_args = Mock()
                    mock_args.username = None
                    mock_args.password = "cli_pass"
                    mock_parser = Mock()
                    mock_parser.parse_args.return_value = mock_args
                    mock_argparser.return_value = mock_parser
                    
                    # Setup environment vars (no username)
                    mock_getenv.side_effect = lambda key: {
                        "MOODLE_USERNAME": None,
                        "MOODLE_PASSWORD": "env_pass"
                    }.get(key)
                    
                    # Call function and expect error
                    with pytest.raises(NameError, match="Missing Moodle credentials"):
                        parse_args()
                
                @patch("moodle_painkillers.argparse.ArgumentParser")
                @patch("moodle_painkillers.os.getenv")
                def test_parse_args_missing_password(self, mock_getenv, mock_argparser):
                    # Setup mock for command line args (none provided)
                    mock_args = Mock()
                    mock_args.username = "cli_user"
                    mock_args.password = None
                    mock_parser = Mock()
                    mock_parser.parse_args.return_value = mock_args
                    mock_argparser.return_value = mock_parser
                    
                    # Setup environment vars (no password)
                    mock_getenv.side_effect = lambda key: {
                        "MOODLE_USERNAME": "env_user",
                        "MOODLE_PASSWORD": None
                    }.get(key)
                    
                    # Call function and expect error
                    with pytest.raises(NameError, match="Missing Moodle credentials"):
                        parse_args()

