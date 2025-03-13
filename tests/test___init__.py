import os
from unittest.mock import Mock, patch

import bs4
import pytest
import requests as rq

from moodle_painkillers import (
    main,
    notify_on_fail,
    parse_args,
    register_presence_status,
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
        mock_a_element.__getitem__ = (
            lambda x, y: mock_a_element.get.return_value
        )
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


class TestParseArgs:
    @patch("moodle_painkillers.argparse.ArgumentParser.parse_args")
    @patch.dict(os.environ, {}, clear=True)
    def test_parse_args_command_line(self, mock_parse_args):
        # Test parsing arguments from command line only
        mock_args = Mock()
        mock_args.username = "cmd_username"
        mock_args.password = "cmd_password"
        mock_args.discord_webhook = "cmd_webhook"
        mock_parse_args.return_value = mock_args

        result = parse_args()

        assert result.username == "cmd_username"
        assert result.password == "cmd_password"
        assert result.discord_webhook == "cmd_webhook"
        mock_parse_args.assert_called_once()

    @patch("moodle_painkillers.argparse.ArgumentParser.parse_args")
    @patch.dict(
        os.environ,
        {
            "MOODLE_USERNAME": "env_username",
            "MOODLE_PASSWORD": "env_password",
            "DISCORD_WEBHOOK": "env_webhook",
        },
    )
    def test_parse_args_environment(self, mock_parse_args):
        # Test parsing arguments from environment variables
        mock_args = Mock()
        mock_args.username = None
        mock_args.password = None
        mock_args.discord_webhook = None
        mock_parse_args.return_value = mock_args

        result = parse_args()

        assert result.username == "env_username"
        assert result.password == "env_password"
        assert result.discord_webhook == "env_webhook"
        mock_parse_args.assert_called_once()

    @patch("moodle_painkillers.argparse.ArgumentParser.parse_args")
    @patch.dict(
        os.environ,
        {
            "MOODLE_USERNAME": "env_username",
            "MOODLE_PASSWORD": "env_password",
            "DISCORD_WEBHOOK": "env_webhook",
        },
    )
    def test_parse_args_precedence(self, mock_parse_args):
        # Test that command line args take precedence over environment variables
        mock_args = Mock()
        mock_args.username = "cmd_username"
        mock_args.password = None  # Use env for password
        mock_args.discord_webhook = "cmd_webhook"
        mock_parse_args.return_value = mock_args

        result = parse_args()

        assert result.username == "cmd_username"  # From command line
        assert result.password == "env_password"  # From environment
        assert result.discord_webhook == "cmd_webhook"  # From command line
        mock_parse_args.assert_called_once()

    @patch("moodle_painkillers.argparse.ArgumentParser.parse_args")
    @patch.dict(os.environ, {}, clear=True)
    def test_parse_args_missing_credentials(self, mock_parse_args):
        # Test error when credentials are missing
        mock_args = Mock()
        mock_args.username = None
        mock_args.password = None
        mock_args.discord_webhook = None
        mock_parse_args.return_value = mock_args

        with pytest.raises(NameError, match="Missing Moodle credentials"):
            parse_args()

        mock_parse_args.assert_called_once()

    @patch("moodle_painkillers.argparse.ArgumentParser.parse_args")
    @patch.dict(
        os.environ,
        {"MOODLE_USERNAME": "env_username", "MOODLE_PASSWORD": "env_password"},
    )
    def test_parse_args_missing_webhook(self, mock_parse_args):
        # Test that missing webhook doesn't cause error
        mock_args = Mock()
        mock_args.username = None
        mock_args.password = None
        mock_args.discord_webhook = None
        mock_parse_args.return_value = mock_args

        result = parse_args()

        assert result.username == "env_username"
        assert result.password == "env_password"
        assert result.discord_webhook is None  # Webhook is optional
        mock_parse_args.assert_called_once()


class TestNotifyOnFail:
    @patch("moodle_painkillers.send_notification")
    def test_success_case(self, mock_send_notification):
        # Test that when the decorated function succeeds,
        # it returns the correct value and doesn't call send_notification

        @notify_on_fail
        def success_func():
            return "success"

        result = success_func()

        assert result == "success"
        mock_send_notification.assert_not_called()

    @patch("moodle_painkillers.send_notification")
    def test_failure_case(self, mock_send_notification):
        # Test that when the decorated function fails,
        # send_notification is called and the exception is re-raised

        test_exception = ValueError("test error")

        @notify_on_fail
        def failing_func():
            raise test_exception

        # The exception should be re-raised
        with pytest.raises(ValueError) as excinfo:
            failing_func()

        # Verify the exception is the same one we raised
        assert excinfo.value == test_exception

        # Verify send_notification was called with the exception message
        mock_send_notification.assert_called_once_with("test error")

    @patch("moodle_painkillers.send_notification")
    def test_with_arguments(self, mock_send_notification):
        # Test that the decorator properly passes arguments to the function

        @notify_on_fail
        def func_with_args(a, b, c=3):
            return a + b + c

        result = func_with_args(1, 2)
        assert result == 6

        result = func_with_args(1, 2, c=10)
        assert result == 13

        mock_send_notification.assert_not_called()


class TestMain:
    @patch("moodle_painkillers.send_notification")
    @patch("moodle_painkillers.register_presence_status")
    @patch("moodle_painkillers.MoodleAuthenticatedSession")
    @patch("moodle_painkillers.parse_args")
    def test_main_successful_workflow(
        self,
        mock_parse_args,
        mock_session_class,
        mock_register_presence,
        mock_send_notification,
    ):
        # Setup mocks
        mock_args = Mock()
        mock_args.username = "test_user"
        mock_args.password = "test_pass"
        mock_args.discord_webhook = "test_webhook"
        mock_parse_args.return_value = mock_args

        # Mock session context manager
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Call main function
        main()

        # Verify all methods were called with correct parameters
        mock_parse_args.assert_called_once()
        mock_session_class.assert_called_once_with("test_user", "test_pass")
        mock_register_presence.assert_called_once_with(mock_session)
        mock_send_notification.assert_called_once_with(
            "Sent presence status!", discord_webhook="test_webhook"
        )

    @patch("moodle_painkillers.send_notification")
    @patch("moodle_painkillers.register_presence_status")
    @patch("moodle_painkillers.MoodleAuthenticatedSession")
    @patch("moodle_painkillers.parse_args")
    def test_main_without_webhook(
        self,
        mock_parse_args,
        mock_session_class,
        mock_register_presence,
        mock_send_notification,
    ):
        # Setup mocks with no webhook
        mock_args = Mock()
        mock_args.username = "test_user"
        mock_args.password = "test_pass"
        mock_args.discord_webhook = None
        mock_parse_args.return_value = mock_args

        # Mock session context manager
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Call main function
        main()

        # Verify notification called with None webhook
        mock_send_notification.assert_called_once_with(
            "Sent presence status!", discord_webhook=None
        )

    @patch("moodle_painkillers.register_presence_status")
    @patch("moodle_painkillers.MoodleAuthenticatedSession")
    @patch("moodle_painkillers.parse_args")
    def test_main_error_in_registration(
        self, mock_parse_args, mock_session_class, mock_register_presence
    ):
        # Setup mocks
        mock_args = Mock()
        mock_parse_args.return_value = mock_args

        # Mock session context manager
        mock_session = Mock()
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Make register_presence_status raise an exception
        mock_register_presence.side_effect = Exception("Registration failed")

        # The function is decorated with notify_on_fail, so the exception will be raised
        with pytest.raises(Exception, match="Registration failed"):
            main()
