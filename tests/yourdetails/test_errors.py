import unittest
from http import HTTPStatus
from unittest.mock import patch
from ndopapp import create_app, routes
from tests import common


class ErrorsTests(unittest.TestCase):
    """ Tests for forms in the yourdetails module """

    def setUp(self):
        self.app = create_app('ndopapp.config.TestConfig')
        common.registerExceptionHandlers(self.app)

    def tearDown(self):
        del self.app

    @patch('ndopapp.main.errors.log_safe_exception', return_value="_")
    @patch('ndopapp.main.errors.redirect_to_route', return_value="_")
    @patch('ndopapp.yourdetails.controllers.NameForm')
    def test_handle_requests_when_an_exception_is_raised(self, name_form_mock, redirect_mock, log_safe_exception_mock):
            
        app = create_app('ndopapp.config.Config')
        # force raising exception on a controller logic
        test_exception = Exception('message')
        name_form_mock.side_effect = test_exception

        client = app.test_client()
        result = client.get(routes.get_absolute("yourdetails.your_details"))

        log_safe_exception_mock.assert_called_with(test_exception)
        redirect_mock.assert_called_with("main.generic_error")

    def test_404s(self):
        app = create_app('ndopapp.config.Config')
        client = app.test_client()
        result = client.get('/missingpage')

        self.assertEqual(result.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn(b"Not Found", result.data)


if __name__ == '__main__':
    unittest.main()
