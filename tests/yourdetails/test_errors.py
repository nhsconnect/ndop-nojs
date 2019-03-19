
import unittest
from http import HTTPStatus
from unittest.mock import patch
from ndopapp import create_app
from ndopapp.yourdetails import errors
from tests import common


class ErrorsTests(unittest.TestCase):
    """ Tests for forms in the yourdetails module """

    def setUp(self):
        self.app = create_app('ndopapp.config.TestConfig')
        common.registerExceptionHandlers(self.app)

    def tearDown(self):
        del self.app

    @patch('ndopapp.yourdetails.errors.render_template', return_value="_")
    def test_handle_requests_error_render_template(self, render_mock):

        common.registerExceptionHandlers(self.app)
        error = Exception()
        error.args = [['error', 'arg']]

        errors.handle_request_error(error)

        render_mock.assert_called_once()

    @patch('ndopapp.yourdetails.errors.render_template', return_value="_")
    def test_handle_requests_error_render_template_if_exception(self, render_mock):

        errors.handle_request_error(None)
        render_mock.assert_called_once()

    def test_404s(self):
        app = create_app('ndopapp.config.Config')
        client = app.test_client()
        result = client.get('/missingpage')

        self.assertEqual(result.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(result.data, b"Page Not Found")

    @patch('ndopapp.yourdetails.errors.render_template', return_value="_")
    def test_handle_unexpected_error_render_template(self, render_mock):

        error = Exception()
        error.args = [['error', 'arg']]
        errors.handle_unexpected_error(error)
        render_mock.assert_called_once()


if __name__ == '__main__':
    unittest.main()
