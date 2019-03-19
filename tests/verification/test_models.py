import unittest
from unittest.mock import patch
import requests_mock
from http import HTTPStatus

from ndopapp import routes, create_app, constants

from ndopapp.verification.models import *

from tests import common


# REQUEST CALLBACK FUNCTIONS

def otp_verification_callback(status_code):
    def otp_verification_callback_inner(request, context):
        context.status_code = status_code
        return ''

    return otp_verification_callback_inner


def resend_code_by_pds_callback(status_code, expected_result):
    def resend_code_by_pds_callback_inner(request, context):
        context.status_code = status_code
        context.headers['Set-Cookie'] = f"{common.SESSION_COOKIE_KEY}={common.SESSION_ID}"
        response = json.dumps({'resend_count': expected_result})
        return response
    return resend_code_by_pds_callback_inner


def request_code_by_pds_callback(status_code, expected_result):
    def request_code_by_pds_callback_inner(request, context):
        context.status_code = status_code
        context.headers['Set-Cookie'] = f"{common.SESSION_COOKIE_KEY}={common.SESSION_ID}"
        response = json.dumps({'error': expected_result})
        return response
    return request_code_by_pds_callback_inner


class TestVerificationModels(unittest.TestCase):
    """
    Tests related to verification/models
    """

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.app = None
        self.client = None

    @requests_mock.Mocker(kw='mock')
    def test_verification_of_otp_codes(self, **kwargs):
        """
        Test that we make a valid request to otp validation endpoint
        also test that we get expected results for responses with specified status codes
        """
        code = '555666'
        mock = kwargs['mock']
        headers = {"Content-type": "application/json"}

        def match_request_text(request):
            # request.text may be None, or '' prevents a TypeError.
            return code in (request.text or '')

        status_codes = [
            (HTTPStatus.OK.value, constants.CORRECT_OTP),
            (HTTPStatus.PARTIAL_CONTENT.value, constants.INCORRECT_OTP),
            (HTTPStatus.FORBIDDEN.value, constants.INCORRECT_OTP),
            (HTTPStatus.NOT_ACCEPTABLE.value, constants.INCORRECT_OTP_MAX_RETRIES),
            (HTTPStatus.UNAUTHORIZED.value, constants.CORRECT_OTP_EXPIRED),
            (HTTPStatus.ACCEPTED.value, constants.UNKNOWN_RESULT),
            (HTTPStatus.INTERNAL_SERVER_ERROR.value, constants.UNKNOWN_RESULT),
        ]

        # loop over statusCodes and verify the result
        with self.app.test_request_context():

            for counter, (http_status, expected_result) in enumerate(status_codes):

                # mock fulfills the test as it will only match the request if 
                # all the parts are present
                mock.register_uri('POST', self.app.config['VERIFY_CODE_URL'],
                                  headers=headers, additional_matcher=match_request_text,
                                  text=otp_verification_callback(http_status))

                result = is_otp_verified_by_pds(common.SESSION_ID, code)
                self.assertEqual(mock.call_count, counter + 1)
                self.assertEqual(result, expected_result)


    @requests_mock.Mocker(kw='mock')
    def test_resend_code_by_pds(self, **kwargs):
        mock = kwargs['mock']

        status_codes = [
            (HTTPStatus.OK.value, constants.RESEND_CODE_SUCCESS, constants.RESEND_CODE_SUCCESS),
            (HTTPStatus.OK.value, None, constants.UNKNOWN_RESULT),
            (HTTPStatus.ACCEPTED.value, None, constants.UNKNOWN_RESULT),
            (HTTPStatus.NOT_ACCEPTABLE.value, None, constants.RESEND_CODE_MAX_EXCEEDED),
        ]

        with self.app.test_request_context():
            for counter, (http_status, resend_count, expected_result) in enumerate(status_codes):
                headers = {'Content-type': 'text/plain', 'cookie': common.SESSION_ID}

                mock.get(self.app.config['PDS_RESEND_CODE_URL'],
                         headers=headers,
                         text=resend_code_by_pds_callback(http_status, resend_count))

                result = resend_code_by_pds(common.SESSION_ID)

                self.assertEqual(mock.call_count, counter + 1)
                self.assertEqual(result, expected_result)

    @requests_mock.Mocker(kw='mock')
    def test_resend_code_by_pds_throws_exception(self, **kwargs):
        """ Test resend_code_byt_pds throws exception"""

        mock = kwargs['mock']

        with self.assertRaises(NDOP_RequestError):
            with self.app.test_request_context():

                headers = {'Content-type': 'text/plain', 'cookie': common.SESSION_ID}
                mock.get(self.app.config['PDS_RESEND_CODE_URL'],
                         headers=headers,
                         text=resend_code_by_pds_callback(
                             HTTPStatus.FORBIDDEN.value,
                             constants.RESEND_CODE_SUCCESS
                         )
                        )

                resend_code_by_pds(common.SESSION_ID)

    @requests_mock.Mocker(kw='mock')
    def test_request_code_by_pds(self, **kwargs):
        mock = kwargs['mock']

        status_codes = [
            (HTTPStatus.OK.value, constants.OTP_REQUEST_SUCCESS, constants.OTP_REQUEST_SUCCESS),
            (HTTPStatus.ACCEPTED.value, constants.OTP_REQUEST_FAILURE, constants.OTP_REQUEST_FAILURE),
            (HTTPStatus.NOT_ACCEPTABLE.value, constants.OTP_REQUEST_MAX_RETRIES, constants.OTP_REQUEST_MAX_RETRIES),
            (HTTPStatus.NOT_ACCEPTABLE.value, None, constants.OTP_REQUEST_FAILURE),
        ]

        with self.app.test_request_context():
            for counter, (http_status, error, expected_result) in enumerate(status_codes):
                headers = {'Content-type': 'text/plain', 'cookie': common.SESSION_ID}

                mock.post(self.app.config['PDS_REQUEST_CODE_URL'],
                          headers=headers,
                          text=request_code_by_pds_callback(http_status, error))

                result = request_code_by_pds(common.SESSION_ID, "sms")

                self.assertEqual(mock.call_count, counter + 1)
                self.assertEqual(result, expected_result)

    @requests_mock.Mocker(kw='mock')
    def test_request_code_by_pds_throws_exception(self, **kwargs):
        """ Test request_code_byt_pds throws exception"""

        mock = kwargs['mock']

        with self.assertRaises(NDOP_RequestError):
            with self.app.test_request_context():

                headers = {'Content-type': 'text/plain', 'cookie': common.SESSION_ID}
                mock.post(self.app.config['PDS_REQUEST_CODE_URL'],
                         headers=headers,
                         text=request_code_by_pds_callback(
                             HTTPStatus.FORBIDDEN.value,
                             constants.OTP_REQUEST_SUCCESS
                         )
                        )

                request_code_by_pds(common.SESSION_ID, 'sms')
