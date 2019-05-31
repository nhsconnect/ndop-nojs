import unittest
from unittest import mock
from unittest.mock import patch
from ndopapp import routes, create_app
from http import HTTPStatus

from tests import common
from ndopapp.yourdetails.controllers import thank_you


class YourDetailsTestThankYouTests(unittest.TestCase):
    """ Tests for the thank-you routes """

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

        self.app_patcher = patch('ndopapp.yourdetails.controllers.app')
        self.app_mock = self.app_patcher.start()
        self.addCleanup(self.app_patcher.stop)

    def tearDown(self):
        self.client = None
        self.app = None

    @patch('ndopapp.utils.is_session_valid')
    @mock.patch('ndopapp.yourdetails.controllers.UserDetails')
    def test_thank_you(self, user_details_mock, is_session_valid_mock):
        """Test correct text is displayed if user has opted_out"""
        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        userDetails = common.get_user_details()

        test_cases = [
            # (is_session_valid, opted_out, flask_session, expected_status, expected_text, expected_text_id, expected_location)
            (True,  'active',   {'is_successfully_stored': True},  HTTPStatus.OK,    'will not be shared', 'not-shared', None),
            (True,  'inactive', {'is_successfully_stored': True},  HTTPStatus.OK,    'can be shared',      'shared',     None),
            (True,  'active',   {'is_successfully_stored': False}, HTTPStatus.FOUND, None, None, routes.get_absolute('yourdetails.choice_not_saved')),
            (True,  'inactive', {'is_successfully_stored': False}, HTTPStatus.FOUND, None, None, routes.get_absolute('yourdetails.choice_not_saved')),
            (False, 'inactive', {},                                HTTPStatus.OK, 'Sorry, you\'ll need to start again', 'mainBody', None),
            (True,  'inactive', {},                                HTTPStatus.OK, 'Sorry, you\'ll need to start again', 'mainBody', None),
        ]


        for case in test_cases:
            is_session_valid, opted_out, flask_session, expected_status, expected_text, \
                expected_text_id, expected_location = case
            with self.subTest(case=case):
                userDetails["opted_out"] = opted_out
                user_details_mock.return_value = userDetails
                is_session_valid_mock.return_value = is_session_valid

                common.set_session_data(self.client, flask_session)

                result = self.client.get(routes.get_raw('yourdetails.thank_you'), headers=headers)

                self.assertEqual(result.status_code, expected_status)
                
                if expected_text:
                    doc = common.html(result)
                    self.assertIn(expected_text, str(doc.find(id=expected_text_id)))
                if expected_location:
                    self.assertIn(expected_location, result.headers['Location'])

    @patch('ndopapp.yourdetails.controllers.render_template')
    @patch('ndopapp.yourdetails.controllers.make_response')
    @patch('ndopapp.yourdetails.controllers.session')
    def test_thank_you_clears_session(self, session_mock, _, __):
        def get_mock(key):
            if key == 'is_successfully_stored':
                return True
            return False

        session_mock.get.side_effect = get_mock
        thank_you.__wrapped__()
        session_mock.clear.assert_called()

    @patch('ndopapp.utils.render_template', return_value='_')
    def test_generic_error_renders_error_html(self, render_template_mock):

        self.client.get(routes.get_raw('main.generic_error'))

        render_template_mock.assert_called_with('error.html', routes=unittest.mock.ANY)


if __name__ == '__main__':
    unittest.main()
