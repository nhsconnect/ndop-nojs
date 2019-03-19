import json
import unittest
from unittest.mock import patch
from http import HTTPStatus

import requests_mock

from ndopapp import create_app
from ndopapp.constants import PDS_RESULT_INVALID_AGE
from ndopapp.yourdetails import models
from tests import common


def confirmation_delivery_method_callback(status_code, expected_result):
    def confirmation_delivery_method_callback_inner(request, context):
        context.status_code = status_code
        result = json.dumps(
            {"search_result": "success", expected_result: common.USER_MOBILE})
        return result
    return confirmation_delivery_method_callback_inner


def pds_search_result_callback(status_code, deliv_method, expected_result):
    def pds_search_result_callback_inner(request, context):
        context.status_code = status_code
        result = json.dumps(
            {"search_result": expected_result, deliv_method: common.USER_MOBILE})
        return result
    return pds_search_result_callback_inner


def get_current_preference_callback(status_code, opted_out, exp_result):
    def pds_search_result_callback_inner(request, context):
        context.status_code = status_code
        result = json.dumps(
            {"get_preference_result": exp_result, "opted_out": opted_out})
        return result
    return pds_search_result_callback_inner


class YourDetailsModelsTests(unittest.TestCase):
    """ Tests for models in the yourdetails module """

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    # UserDetails class

    @requests_mock.Mocker(kw='mock')
    def test_get_session_id__on_success(self, **kwargs):
        """ Test get_session_id() returns a session id string"""
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['CREATE_SESSION_URL'],
                           text=common.create_session_callback)

        with self.app.test_request_context():
            sessionId = models.get_session_id()
            self.assertEqual(common.SESSION_ID, sessionId)

    @requests_mock.Mocker(kw='mock')
    def test_get_session_id__on_fail(self, **kwargs):
        """ Test get_session_id() returns a session id string"""
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['CREATE_SESSION_URL'],
                           text=common.create_session_callback_fail)

        with self.assertRaises(models.NDOP_RequestError):
            with self.app.test_request_context():
                sessionId = models.get_session_id()

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.app')
    def test_get_current_preference_returns_proper_result(self, app_mock, **kwargs):
        """Verify that get_current_preference returns expected result per status_code"""
        
        test_cases = [
            # (status_code, get_preference_result, opted_out, expected_result)
            (HTTPStatus.OK.value, 'success', 'active', 'active'),
            (HTTPStatus.OK.value, 'success', 'inactive', 'inactive'),
            (HTTPStatus.OK.value, 'success', 'empty', 'preference_empty'),
            (HTTPStatus.OK.value, 'empty', 'empty', 'preference_empty'),
            (HTTPStatus.ACCEPTED.value, 'preference_empty', '', 'preference_empty'),
            (HTTPStatus.PARTIAL_CONTENT.value, 'preference_empty', '', 'incomplete'),
            (HTTPStatus.UNAUTHORIZED.value, 'preference_failure', '', 'preference_failure'),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                status_code, pref_result, opted_out, exp_result = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']
                the_requests_mock.get(requests_mock.ANY, status_code=status_code,
                        text=get_current_preference_callback(status_code, opted_out, pref_result))

                self.assertEqual(models.get_current_preference('some session id'), exp_result)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.app')
    def test_store_preference_returns_proper_result(self, app_mock, **kwargs):
        """Verify that store_preference returns expected result per status_code"""

        test_cases = [
            # (status_code, expected_result)
            (HTTPStatus.OK.value, 'success'),
            (HTTPStatus.PARTIAL_CONTENT.value, 'not_completed'),
            (HTTPStatus.ACCEPTED.value, 'failure'),
            (HTTPStatus.UNAUTHORIZED.value, 'failure'),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                status_code, expected_result = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']
                the_requests_mock.get(requests_mock.ANY, status_code=status_code)

                self.assertEqual(models.store_preference('some session id'), expected_result)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.app')
    def test_confirm_preference_returns_proper_result(self, app_mock, **kwargs):
        """Verify that confirm_preference returns expected result per status_code"""

        test_cases = [
            # (status_code, expected_result)
            (HTTPStatus.OK.value, True),
            (HTTPStatus.PARTIAL_CONTENT.value, False),
            (HTTPStatus.UNAUTHORIZED.value, False),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                status_code, expected_result = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']
                the_requests_mock.get(requests_mock.ANY, status_code=status_code)

                self.assertEqual(models.confirm_preference('some session id'), expected_result)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.app')
    @patch('ndopapp.yourdetails.models.UserDetails')
    def test_set_preference_returns_proper_result(self, user_details_mock, app_mock, **kwargs):
        """Verify that set_preference returns expected result per status_code"""

        test_cases = [
            # (status_code, expected_result)
            (HTTPStatus.OK.value, True),
            (HTTPStatus.PARTIAL_CONTENT.value, False),
            (HTTPStatus.FORBIDDEN.value, False),
            (HTTPStatus.UNAUTHORIZED.value, False),
        ]

        user_details_mock.preference = "optedOut"

        for case in test_cases:
            with self.subTest(case=case):
                status_code, expected_result = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']
                the_requests_mock.post(requests_mock.ANY, status_code=status_code)

                self.assertEqual(
                    models.set_preference(user_details_mock, 'some session id'),
                    expected_result
                )

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.app')
    def test_get_confirmation_delivery_details_returns_method(self, app_mock, **kwargs):

        test_cases = [
            # (status_code, expected_result)
            (HTTPStatus.OK.value, 'sms'),
            (HTTPStatus.OK.value, 'email'),
            (HTTPStatus.UNAUTHORIZED.value, None),
            (HTTPStatus.PARTIAL_CONTENT.value, False),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                status_code, exp_ret = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']

                the_requests_mock.get(
                    requests_mock.ANY,
                    status_code=status_code,
                    text=confirmation_delivery_method_callback(
                        status_code,
                        exp_ret
                    )
                )

                ret = models.get_confirmation_delivery_details('some session id')

                self.assertIn(exp_ret, ret) if exp_ret else self.assertEqual(ret, None)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.session')
    @patch('ndopapp.yourdetails.models.app')
    def test_check_status_of_pds_search_result_returns_search_result(self, app_mock, _, **kwargs):

        test_cases = [
            # (status_code, expected_result)
            (HTTPStatus.OK.value, 'sms', 'success'),
            (HTTPStatus.OK.value, 'email', 'success'),
            (HTTPStatus.UNAUTHORIZED.value, 'sms', "invalid_user"),
            (HTTPStatus.UNPROCESSABLE_ENTITY.value, 'sms', "insufficient_data"),
            (HTTPStatus.NOT_ACCEPTABLE.value, 'email', "age_restriction_error"),
            (HTTPStatus.ACCEPTED.value, 'email', ""),
        ]

        for case in test_cases:
            with self.subTest(case=case):
                status_code, delivery_method, exp_ret = case

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']

                the_requests_mock.get(
                    requests_mock.ANY,
                    status_code=status_code,
                    text=pds_search_result_callback(
                        status_code,
                        delivery_method,
                        exp_ret
                    )
                )

                ret = models.check_status_of_pds_search_result('some session id')

                self.assertEqual(ret, exp_ret)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.session')
    @patch('ndopapp.yourdetails.models.app')
    def test_check_status_of_pds_search_result_returns_raises(self, app_mock, _, **kwargs):
        """ Test check_status_of_pds_search_result() throws exception"""

        with self.assertRaises(models.NDOP_RequestError):
            with self.app.test_request_context():

                app_mock.config = self.app.config

                the_requests_mock = kwargs['r_mock']

                the_requests_mock.get(
                    requests_mock.ANY,
                    status_code=HTTPStatus.FORBIDDEN.value,
                    text=pds_search_result_callback(
                        HTTPStatus.FORBIDDEN.value,
                        'sms',
                        None
                    )
                )

                models.check_status_of_pds_search_result('some session id')

        the_requests_mock = kwargs['r_mock']
        the_requests_mock.get(requests_mock.ANY, status_code=401)

        self.assertEqual(models.get_confirmation_delivery_details('some session id'), None)

    @requests_mock.Mocker(kw='r_mock')
    @patch('ndopapp.yourdetails.models.clean_state_model', return_value="_")
    @patch('ndopapp.yourdetails.models.app')
    def test_do_pds_search_returns_invalid_age_when_api_response_is_406(self, app_mock, _, **kwargs):

        app_mock.config = self.app.config

        the_requests_mock = kwargs['r_mock']
        the_requests_mock.post(requests_mock.ANY, status_code=406)

        self.assertEqual(models.do_pds_search(type("user_details", (object, ), {
            "firstName": "Joan",
            "lastName": "Smith",
            "dateOfBirthDay": 1,
            "dateOfBirthMonth": 1,
            "dateOfBirthYear": 2099,
            "nhsNumber": "11111111111",
            "postcode": ""
        }), 'some session id'), PDS_RESULT_INVALID_AGE)

    def test_dob_string_returns_no_padded_numbers(self):
        sut = models.UserDetails()
        sut.dateOfBirthDay = ' 1'
        sut.dateOfBirthMonth = ' 5'
        sut.dateOfBirthYear = '1981'

        self.assertEqual(sut.dob, "1 5 1981")


if __name__ == '__main__':
    unittest.main()
