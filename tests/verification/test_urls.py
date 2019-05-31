import unittest
import json
from unittest.mock import patch, MagicMock
from ndopapp import routes, create_app, constants
from http import HTTPStatus
from ndopapp.verification.controllers import lookup_failure_error
from tests import common


class TestVerificationURLs(unittest.TestCase):

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_verification_option_get(self, _):
        """ Test verification option page returns a 200 """
        with self.client as c:
            with c.session_transaction() as session:
                session["sms"] = common.USER_MOBILE
            result = c.get('/verificationoption')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.utils.clean_state_model')
    @patch('ndopapp.verification.controllers.render_template')
    @patch('ndopapp.verification.controllers.request_code_by_pds')
    @patch('ndopapp.verification.controllers.redirect_to_route')
    @patch('ndopapp.verification.controllers.VerificationOption')
    def test_verificationoption_redirecting(self, verification_option_mock,
            client_redirect_mock, request_code_by_pds_mock, render_mock,
            clean_state_model_mock, _):
        """ Test that verificationoption template is redirecting properly """
        test_cases = (
            #(delivery_type, expected_result)
            ('Email', constants.OTP_REQUEST_SUCCESS),
            ('Email', constants.OTP_REQUEST_MAX_RETRIES),
            ('SMS', constants.OTP_REQUEST_SUCCESS),
            ('SMS', constants.OTP_REQUEST_MAX_RETRIES),
            ('SMS', constants.OTP_REQUEST_FAILURE),
        )

        headers = {'Content-type': 'application/json', 'cookie': None}

        for case in test_cases:
            with self.subTest(case=case):
                delivery_type, expected_result, *optional_cases = case

                form_mock = MagicMock()

                form_mock.validate_on_submit.return_value = True
                form_mock.radio.data = delivery_type

                verification_option_mock.return_value = form_mock
                client_redirect_mock.return_value = "_"

                request_code_by_pds_mock.return_value = expected_result

                render_mock.return_value = "_"

                clean_state_model_successful = None
                if optional_cases:
                    clean_state_model_successful, = optional_cases
                    clean_state_model_mock.return_value = clean_state_model_successful

                with self.client as c:
                    with c.session_transaction() as session:
                        session["sms"] = common.USER_DETAILS.get("sms")
                        session["email"] = common.USER_DETAILS.get("email")

                self.client.post('/verificationoption',
                                 data=json.dumps(common.USER_DETAILS),
                                 headers=headers)

                if delivery_type not in ('Email', 'SMS'):
                    if clean_state_model_successful == True:
                        client_redirect_mock.assert_called_with("verification.contact_details_not_recognised")
                    elif clean_state_model_successful == False:
                        client_redirect_mock.assert_called_with("main.generic_error")
                elif expected_result == constants.OTP_REQUEST_SUCCESS:
                    client_redirect_mock.assert_called_with("verification.enter_your_code")
                elif expected_result == constants.OTP_REQUEST_MAX_RETRIES:
                    client_redirect_mock.assert_called_with("verification.resend_code_error")
                else:
                    render_mock.assert_called()


    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_verificationoption_template_rendering(self, _):
        """ Test that verificationoption template is rendered properly """

        headers = {'Content-type': 'application/json', 'cookie': None}

        with self.client as c:
            with c.session_transaction() as session:
                session["sms"] = common.USER_DETAILS.get("sms")
                session["email"] = common.USER_DETAILS.get("email")

        result = self.client.post('/verificationoption',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        assert common.USER_DETAILS['sms'] in str(result.data)
        assert 'wrong_value_with_randomxxxx' not in str(result.data)
        assert common.USER_DETAILS['email'] in str(result.data)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.request_code_by_pds')
    def test_verificationoption_without_email_address(self, 
            request_code_by_pds_mock, _):
        """ Test that verificationoption template is rendered properly
        without email"""

        headers = {'Content-type': 'application/json', 'cookie': None}

        with self.client as c:
            with c.session_transaction() as session:
                session["sms"] = common.USER_DETAILS.get("sms")

        request_code_by_pds_mock.return_value = constants.OTP_REQUEST_SUCCESS
        result = self.client.post('/verificationoption',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert "enteryourcode" in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.request_code_by_pds')
    def test_verificationoption_without_phone_number(self, 
            request_code_by_pds_mock, _):
        """ Test that verificationoption template is rendered properly
        without sms"""

        headers = {'Content-type': 'application/json', 'cookie': None}

        with self.client as c:
            with c.session_transaction() as session:
                session["email"] = common.USER_DETAILS.get("email")

        request_code_by_pds_mock.return_value = constants.OTP_REQUEST_SUCCESS
        result = self.client.post('/verificationoption',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert "enteryourcode" in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.redirect_to_route')
    @patch('ndopapp.verification.controllers.CodeForm')
    @patch('ndopapp.verification.controllers.is_otp_verified_by_pds')
    def test_enteryourcode_status_is_200(self, is_otp_verified_by_pds_mock,
            code_form_mock, client_redirect_mock, _):
        """Test that enteryourcode redirects properly and returns code 200"""

        form_mock = MagicMock()
        form_mock.validate_on_submit.return_value = True
        code_form_mock.return_value = form_mock
        client_redirect_mock.return_value = "_"

        is_otp_verified_by_pds_mock.return_value = constants.CORRECT_OTP

        headers = {'Content-type': 'application/json', 'cookie': None}
        result = self.client.post('/enteryourcode',
                                  headers=headers)
        client_redirect_mock.assert_called_with('yourdetails.set_your_preference')

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.app')
    @patch('ndopapp.verification.controllers.flash')
    @patch('ndopapp.verification.controllers.render_template')
    @patch('ndopapp.verification.controllers.CodeForm')
    def test_enteryourcode_renders_errors(self, code_form_mock, render_mock, *_):
        """Test that enteryourcode renders errors"""

        form_mock = MagicMock()
        form_mock.validate_on_submit.return_value = False
        code_form_mock.return_value = form_mock
        code_form_mock.errors = {'errors'}
        render_mock.return_value = "_"


        headers = {'Content-type': 'application/json', 'cookie': None}
        self.client.post('/enteryourcode', headers=headers)
        render_mock.assert_called()

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.is_otp_verified_by_pds')
    def test_enteryourcode_post_redirects(self, is_otp_verified_by_pds_mock, _):
        """ Test enteryourcode page posts redirects for correct otp"""
        test_cases = (
            (666665, constants.CORRECT_OTP, '/setyourpreference'),
            (666665, constants.CORRECT_OTP_EXPIRED, '/expiredcodeerror'),
            (123456, constants.CORRECT_OTP, '/setyourpreference'),
            (111234, constants.CORRECT_OTP, '/setyourpreference'),
            ('001234', constants.CORRECT_OTP, '/setyourpreference'),
            (132000, constants.CORRECT_OTP, '/setyourpreference'),
            (132000, 'unknown', '/genericerror'),
        )

        for case in test_cases:
            with self.subTest(case=case):
                number, exp_ret, location = case
                is_otp_verified_by_pds_mock.return_value = exp_ret

                result = self.client.post(
                    '/enteryourcode', data=dict(enterOtpInput=number))

                assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
                assert location in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.is_otp_verified_by_pds')
    @patch('ndopapp.verification.controllers.CodeForm')
    def test_enteryourcode_post_invalid_does_not_redirect(self,
                                                          code_form_mock,
                                                          is_otp_verified_by_pds_mock,
                                                          _):
        """ Test enteryourcode page posts to does not redirect for
        invalid otp """
        test_cases = (
            (66666, constants.INCORRECT_OTP_MAX_RETRIES),
            (23456, constants.INCORRECT_OTP),
            (11234, constants.INCORRECT_OTP_MAX_RETRIES),
            (None, constants.INCORRECT_OTP_MAX_RETRIES),
            (0, constants.INCORRECT_OTP),
            ('string', constants.INCORRECT_OTP_MAX_RETRIES),
            (32000, constants.INCORRECT_OTP),
        )


        form_mock = MagicMock()
        add_incorrect_otp_error_mock = MagicMock()
        form_mock.add_incorrect_otp_error = add_incorrect_otp_error_mock
        code_form_mock.return_value = form_mock

        for case in test_cases:
            with self.subTest(case=case):
                number, status_result = case

                is_otp_verified_by_pds_mock.return_value = status_result
                result = self.client.post(
                    '/enteryourcode', data=dict(enterOtpInput=str(number)))

                if status_result == constants.INCORRECT_OTP:
                    assert add_incorrect_otp_error_mock.called
                    assert HTTPStatus(result.status_code) == HTTPStatus.OK
                else:
                    assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
                    assert '/incorrectcodeerror' in result.headers['Location']

    @patch('ndopapp.utils.session')
    @patch('ndopapp.utils.request')
    @patch('ndopapp.utils.clean_state_model', return_value=True)
    @patch('ndopapp.utils.is_session_valid', return_value=True) 
    @patch('ndopapp.verification.controllers.render_template', return_value="_")
    def test_contactdetailsnotrecognised_make_response(self, render_mock,
            _, __, ___, ____):
        """Test that contactdetailsnotrecognised make response"""

        headers = {'Content-type': 'application/json', 'cookie': None}
        result = self.client.get('/contactdetailsnotrecognised', headers=headers)
        render_mock.assert_called_with('contact-details-not-recognised.html', routes=routes)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.utils.render_template', return_value="_")
    def test_resendcodeerror_make_response(self, render_template_mock, _):
        """Test that make response"""
        self.client.get('/resendcodeerror')
        render_template_mock.assert_called_with('resend-code-error.html', routes=unittest.mock.ANY)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.utils.render_template', return_value="_")
    def test_clear_session_and_make_response_for_pages(self, render_mock, _):
        """Test that resendcodeerror clear session and make response"""

        endpoints = [
            ('resendcodeerror', 'resend-code-error'),
            ('contactdetailsnotfound', 'contact-details-not-found'),
            ('agerestrictionerror', 'age-restriction-error'),
            ('incorrectcodeerror', 'incorrect-code-error'),
            ('expiredcodeerror', 'expired-code-error'),
        ]
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                endpoint, page = endpoint
                self.client.get(f'/{endpoint}')
                render_mock.assert_called_with(f'{page}.html', routes=unittest.mock.ANY)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.verification.controllers.app')
    @patch('ndopapp.verification.controllers.resend_code_by_pds')
    def test_resendcode_status_is_200(self, resend_code_by_pds_mock, _, __):
        """Test that resendcode exists and returns 200"""
        test_cases = (
            #(return, expected_is_resent, expected_is_resent_max_reached)
            (constants.UNKNOWN_RESULT, None, None),
            (constants.RESEND_CODE_SUCCESS, True, False),
            (constants.RESEND_CODE_MAX_REACHED, True, True),
        )

        for case in test_cases:
            with self.subTest(case=case):
                result, is_resent, is_resent_max_reached = case

                resend_code_by_pds_mock.return_value = result

                result = self.client.post('/resendcode')
                with self.client as c:
                    with c.session_transaction() as session:
                        assert session.get('is_resent') is is_resent
                        assert session.get('is_resent_max_reached') is is_resent_max_reached

    @patch('ndopapp.utils.request')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.utils.clean_state_model')
    @patch('ndopapp.verification.controllers.app')
    @patch('ndopapp.utils.session')
    @patch('ndopapp.verification.controllers.render_template', return_value=True)
    @patch('ndopapp.verification.controllers.UserDetails')
    def test_lookupfailureerror_renders_correct_html_according_to_the_auth_flow_used(
            self,
            user_details_mock,
            render_template,
            *_,
    ):
        test_cases = (
            # postcode, expected_html_file_to_render
            ('abc132', 'lookup-failure-error-postcode.html'),
            ('',       'lookup-failure-error.html')
        )

        for case in test_cases:
            with self.subTest(case=case):
                postcode, expected_html_file_to_render = case

                user_details = MagicMock()
                user_details.postcode = postcode
                user_details_mock.return_value = user_details

                lookup_failure_error.__wrapped__('')

                render_template.assert_called_with(expected_html_file_to_render, routes=routes)
