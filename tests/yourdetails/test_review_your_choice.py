import unittest
import requests_mock
import json
from ndopapp import routes, create_app
from unittest.mock import patch
from http import HTTPStatus
from unittest.mock import patch

from tests import common
from ndopapp.yourdetails.controllers import review_your_choice


def confirmation_delivery_method_callback(request, context):
    context.status_code = HTTPStatus.OK.value
    result = json.dumps(
        {"search_result": "success", "sms": common.USER_MOBILE})
    return result


class YourDetailsReviewYourChoiceTests(unittest.TestCase):
    """ Tests for the reviewyourchoice url """

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    # Test GET requests to /review-your-choice

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid')
    def test_review_your_choice_yes(self, is_session_valid_mock, **kwargs):
        is_session_valid_mock.return_value = True
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['GET_CONFIRMATION_DELIVERY_METHOD'],
                           text=confirmation_delivery_method_callback)
        expected_choice = 'can'
        user_details = common.get_user_details()
        user_details['opted_out'] = 'inactive'
        common.update_session_data(self.client, user_details)
        result = self.client.get('/reviewyourchoice')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        doc = common.html(result)
        choice = doc.find(id='choice')
        assert choice.text.strip() == expected_choice

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid')
    def test_review_your_choice_no(self, is_session_valid_mock, **kwargs):
        is_session_valid_mock.return_value = True
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['GET_CONFIRMATION_DELIVERY_METHOD'],
                           text=confirmation_delivery_method_callback)
        expected_choice = 'cannot'
        user_details = common.get_user_details()
        user_details['opted_out'] = 'active'
        common.update_session_data(self.client, user_details)
        result = self.client.get('/reviewyourchoice')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        doc = common.html(result)
        choice = doc.find(id='choice').text.strip()
        assert choice == expected_choice

    @patch('ndopapp.yourdetails.controllers.get_confirmation_delivery_details', return_value=None)
    @patch('ndopapp.yourdetails.controllers.redirect')
    def test_review_your_choice_redirects_to_generic_error_when_get_confirmation_delivery_details_returns_none(self, redirect_mock, _):

        review_your_choice.__wrapped__('some session id')

        redirect_mock.assert_called_with(routes.get_absolute('yourdetails.generic_error'))

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.get_confirmation_delivery_details')
    def test_review_your_choice_redirects_to_genericerror(self,
            confirmation_delivery_mock, _, **kwargs):

        confirmation_delivery_mock.return_value = None

        mock = kwargs['mock']
        adapter = mock.get(self.app.config['GET_CONFIRMATION_DELIVERY_METHOD'],
                           text=confirmation_delivery_method_callback)
        user_details = common.get_user_details()
        user_details['opted_out'] = 'active'
        common.set_session_data(self.client, user_details)
        result = self.client.get(routes.get_raw('yourdetails.review_your_choice'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert routes.get_absolute('yourdetails.generic_error') == result.headers['Location']

if __name__ == '__main__':
    unittest.main()
