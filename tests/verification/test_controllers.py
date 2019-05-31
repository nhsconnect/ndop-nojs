import unittest
from flask import Flask
from mock import patch
from ndopapp.verification import controllers
from ndopapp import routes, constants


class TestVerificationController(unittest.TestCase):

    def setUp(self):

        self.app_patcher = patch('ndopapp.verification.controllers.app')
        self.app_mock = self.app_patcher.start()
        self.addCleanup(self.app_patcher.stop)

        self.session_patcher = patch('ndopapp.verification.controllers.session')
        self.session_mock = self.session_patcher.start()
        self.addCleanup(self.session_patcher.stop)

        self.redirect_patcher = patch('ndopapp.verification.controllers.redirect_to_route')
        self.redirect_mock = self.redirect_patcher.start()
        self.addCleanup(self.redirect_patcher.stop)

    @patch('ndopapp.verification.controllers.CodeForm')
    @patch('ndopapp.verification.controllers.is_otp_verified_by_pds')
    def test_enteryourcode_when_code_expired_is_redirecting_to_expiredcodeerror(self, is_otp_verified_by_pds_mock, _):
        is_otp_verified_by_pds_mock.return_value = constants.CORRECT_OTP_EXPIRED

        with Flask(__name__).app_context():
            controllers.enter_your_code.__wrapped__('session_id')

        self.redirect_mock.assert_called_with('verification.expired_code_error')

    @patch('ndopapp.verification.controllers.resend_code_by_pds')
    def test_resendcode_when_retries_exceeded_max_is_redirecting_to_resendcodeerror(self, resend_code_by_pds_mock):
        resend_code_by_pds_mock.return_value = constants.RESEND_CODE_MAX_EXCEEDED

        with Flask(__name__).app_context():
            controllers.resend_code.__wrapped__('session_id')

        self.redirect_mock.assert_called_with('verification.resend_code_error')
