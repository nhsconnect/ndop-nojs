import requests_mock
import unittest
from unittest.mock import patch, MagicMock
import json
from ndopapp import routes, create_app
from http import HTTPStatus

from tests import common
from ndopapp import constants


def get_preference_results_callback_inactive(_, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps({"get_preference_result": "success", "opted_out": "inactive"})
    return body


def get_preference_results_callback_active(_, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps({"get_preference_result": "success", "opted_out": "active"})
    return body


def get_preference_results_callback_no_preference(_, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps({"get_preference_result": "success", "opted_out": ""})
    return body


class YourDetailsSetYourPreferenceTests(unittest.TestCase):
    """ Tests for the setyourpreference routes """

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    # Test GET requests to /setyourpreference

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_set_your_preference_active(self, _, **kwargs):
        """ Test set-preference page returns a 200 """

        mock = kwargs['mock']
        mock.get(self.app.config['PREFERENCE_RESULT_URL'], text=get_preference_results_callback_active)

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        result = self.client.get('/setyourpreference', headers=headers)

        self.assertEqual(HTTPStatus(result.status_code), HTTPStatus.OK)
        doc = common.html(result)
        self.assertNotIn('checked', doc.find_all(id='single-opted-in')[0].attrs)
        self.assertIn('checked', doc.find_all(id='single-opted-out')[0].attrs)


    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_set_your_preference_inactive(self, _, **kwargs):
        """ Test set-preference page is inactive when expected """

        mock = kwargs['mock']
        mock.get(self.app.config['PREFERENCE_RESULT_URL'], text=get_preference_results_callback_inactive)

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        result = self.client.get('/setyourpreference', headers=headers)

        self.assertEqual(HTTPStatus(result.status_code), HTTPStatus.OK)
        doc = common.html(result)
        self.assertIn('checked', doc.find_all(id='single-opted-in')[0].attrs)
        self.assertNotIn('checked', doc.find_all(id='single-opted-out')[0].attrs)


    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    def test_post_set_preference(self, choice_option_mock, _, **kwargs):
        """ Test your_details_review page returns a 200 """

        test_cases = ('Yes', 'No')
        form_mock = MagicMock()

        for case in test_cases:
            with self.subTest(case=case):
                form_mock.validate_on_submit.return_value = True
                form_mock.radio.data = case

                choice_option_mock.return_value = form_mock

                mock = kwargs['mock']
                mock.get(self.app.config['PREFERENCE_RESULT_URL'],
                         text=get_preference_results_callback_inactive)
                mock.post(self.app.config['SET_PREFERENCE_URL'], text="{}")

                with self.client as c:
                    with c.session_transaction() as session:
                        session['timeout_threshold'] = 1

                result = self.client.post('/setyourpreference')

                assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
                assert routes.get_absolute("yourdetails.submit_preference") in result.headers['Location']
                with self.client as c:
                    with c.session_transaction() as session:
                        assert not 'timeout_threshold' in session

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    @patch('ndopapp.yourdetails.controllers.flash')
    def test_flash_errors(self, flash_mock, choice_option_mock, _, **kwargs):
        """ Test errors are flashed when setpreference not validated """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False
        form_mock.radio.data = "Yes"
        form_mock.errors = ['sample_fot_tests']

        choice_option_mock.return_value = form_mock
        flash_mock.return_value = "_"

        mock = kwargs['mock']
        mock.get(self.app.config['PREFERENCE_RESULT_URL'], text=get_preference_results_callback_inactive)
        mock.post(self.app.config['SET_PREFERENCE_URL'], text="{}")

        result = self.client.post('/setyourpreference')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        flash_mock.assert_called()

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    def test_render_set_preferences_again_when_active(self, choice_option_mock,
            _, **kwargs):
        """ Test rerender setpreference when active """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False

        choice_option_mock.return_value = form_mock

        with self.client as c:
            with c.session_transaction() as session:
                session['pds_opted_out'] = 'active' 

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        result = self.client.post('/setyourpreference', headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        assert form_mock.radio.data == 'No'

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    def test_render_set_preferences_again_when_get_preference_empty(self, 
            choice_option_mock, _):
        """ Test rerender setpreference when empty preference """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False

        choice_option_mock.return_value = form_mock

        with self.client as c:
            with c.session_transaction() as session:
                session['pds_opted_out'] = constants.GET_PREFERENCE_EMPTY

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        result = self.client.post('/setyourpreference', headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        assert form_mock.radio.data not in ('Yes', 'No')

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    def test_post_set_preference_timeout(self, choice_option_mock, _, **kwargs):
        """ Test set preference timeout """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False
        form_mock.radio.data = "Yes"
        form_mock.errors = None

        choice_option_mock.return_value = form_mock

        mock = kwargs['mock']
        mock.get(self.app.config['PREFERENCE_RESULT_URL'],
                 text=get_preference_results_callback_inactive)
        mock.post(self.app.config['SET_PREFERENCE_URL'], text="{}")

        with self.client as c:
            with c.session_transaction() as session:
                session['timeout_threshold'] = 1

        result = self.client.post('/setyourpreference')

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert 'genericerror' in result.headers['Location']
        with self.client as c:
            with c.session_transaction() as session:
                assert not 'timeout_threshold' in session

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.get_current_preference', return_value=constants.GET_PREFERENCE_FAILURE)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    def test_post_set_preference_when_failure(self, choice_option_mock, _, __, **kwargs):
        """ Test set preference goes to genericerror when failure """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False
        form_mock.radio.data = "Yes"
        form_mock.errors = None

        choice_option_mock.return_value = form_mock

        mock = kwargs['mock']
        mock.get(self.app.config['PREFERENCE_RESULT_URL'],
                 text=get_preference_results_callback_inactive)
        mock.post(self.app.config['SET_PREFERENCE_URL'], text="{}")

        with self.client as c:
            with c.session_transaction() as session:
                session['timeout_threshold'] = constants.FAR_IN_THE_FUTURE

        result = self.client.post('/setyourpreference')

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert 'genericerror' in result.headers['Location']
        with self.client as c:
            with c.session_transaction() as session:
                assert not 'timeout_threshold' in session

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.ChoiceOption')
    @patch('ndopapp.yourdetails.controllers.get_current_preference')
    def test_render_set_preferences_again_when_get_incomplete(self, 
            get_current_preference_mock, choice_option_mock, _):
        """ Test rerender setpreference when incomplete """

        form_mock = MagicMock()

        form_mock.validate_on_submit.return_value = False

        choice_option_mock.return_value = form_mock

        get_current_preference_mock.return_value = constants.GET_PREFERENCE_INCOMPLETE

        with self.client as c:
            with c.session_transaction() as session:
                session['pds_opted_out'] = None

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        result = self.client.post('/setyourpreference', headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        assert not form_mock.radio.data == "Yes" and not form_mock.radio.data == "No"

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.store_preference')
    def test_store_preference_result(self, store_preference_mock, _):
        """ Test store_preference_result redirects properly """

        test_cases = (
            #(store_ret, is_timeout_in_session, timeout_threshold, expected_status, expected_endpoint)
            ("success", False, 1, HTTPStatus.FOUND, routes.get_absolute('yourdetails.generic_error')),
            ("success", False, constants.FAR_IN_THE_FUTURE, HTTPStatus.FOUND, routes.get_absolute('yourdetails.thank_you')),
            ("not_completed", True, None, HTTPStatus.OK, None),
            ("failure", False, None, HTTPStatus.FOUND, routes.get_absolute('yourdetails.choice_not_saved')),
        )
        for case in test_cases:
            with self.subTest(case=case):
                store_ret, is_timeout_in_session, timeout_threshold, status, endpoint = case

                store_preference_mock.return_value = store_ret

                common.update_session_data(self.client, {'timeout_threshold': timeout_threshold})

                headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
                result = self.client.post(routes.get_raw("yourdetails.store_preference_result"), headers=headers)

                self.assertEqual(result.status_code, status)
                if status == HTTPStatus.FOUND:
                    self.assertIn(endpoint, result.headers['Location'])
                self.assertEqual('timeout_threshold' in common.get_session_data(self.client), is_timeout_in_session)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.set_preference')
    @patch('ndopapp.yourdetails.controllers.UserDetails')
    def test_submit_preference_redirects(self, user_details_mock,
            set_preference_mock, _):
        """ Test submit_preference redirects properly """

        test_cases = (
            #(result, expected_endpoint)
            (False, 'genericerror'),
            (True, 'reviewyourchoice'),
        )

        user_details_mock.return_value = None

        for case in test_cases:
            with self.subTest(case=case):
                set_preference_mock.return_value, endpoint = case

                headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
                result = self.client.post('/submitpreference', headers=headers)

                assert result.status_code == HTTPStatus.FOUND
                assert endpoint in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.confirm_preference')
    @patch('ndopapp.yourdetails.controllers.UserDetails')
    def test_confirmation_sender_redirects(self, user_details_mock, set_preference_mock, _):
        """ Test confirmation_sender redirects properly """

        test_cases = (
            #(result, expected_endpoint)
            (False, routes.get_absolute("yourdetails.generic_error")),
            (True, routes.get_absolute("yourdetails.store_preference_result")),
        )

        user_details_mock.return_value = None

        for case in test_cases:
            with self.subTest(case=case):
                set_preference_mock.return_value, endpoint = case

                headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
                result = self.client.post(routes.get_raw("yourdetails.confirmation_sender"), headers=headers)

                assert result.status_code == HTTPStatus.FOUND
                self.assertIn(endpoint, result.headers['Location'])


if __name__ == '__main__':
    unittest.main()
