import unittest
from unittest.mock import patch
from ndopapp import routes, create_app

from tests import common
from ndopapp import constants


class YourDetailsWaitingForResultsTests(unittest.TestCase):
    """ Test waiting_for_results routes"""

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    @patch('ndopapp.utils.clean_state_model', return_value=True)
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    @patch('ndopapp.yourdetails.controllers.check_status_of_pds_search_result')
    def test_waiting_for_results_redirecting_when_search_fails(self,
            check_status_of_pds_search_result_mock, redirect_mock, *_):
        """ Test waiting_for_results page redirect to lookupfailureerror when pds search fails"""

        redirect_mock.return_value = "_"
        check_status_of_pds_search_result_mock.return_value = "invalid_user"

        with self.client as c:
            with c.session_transaction() as session:
                session['timeout_threshold'] = constants.FAR_IN_THE_FUTURE

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        redirect_mock.assert_called_with("verification.lookup_failure_error")

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    def test_waiting_for_results_redirecting_on_timeout(self, redirect_mock, _):
        """ Test waiting_for_results page redirect to genericerror on timeout"""

        redirect_mock.return_value = "_"

        with self.client as c:
            with c.session_transaction() as session:
                session['timeout_threshold'] = 1

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        redirect_mock.assert_called_with("main.generic_error")

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template')
    @patch('ndopapp.yourdetails.controllers.check_status_of_pds_search_result')
    def test_rerender_waiting_for_results(self, 
            check_status_of_pds_search_result_mock, render_mock, _):
        """ Test waiting_for_results rerender itself"""

        render_mock.return_value = "_"
        check_status_of_pds_search_result_mock.return_value = "incomplete"

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        render_mock.assert_called_with('waiting-for-results.html',
                waiting_message=constants.PDS_SEARCH_WAITING_MESSAGE, routes=routes)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    @patch('ndopapp.yourdetails.controllers.check_status_of_pds_search_result')
    def test_waiting_for_results_redirecting_when_no_contact_details(self,
            check_status_of_pds_search_result_mock, redirect_mock, _):
        """ Test waiting_for_results page redirect to contactdetailsnotfound when no contact details"""

        redirect_mock.return_value = "_"
        check_status_of_pds_search_result_mock.return_value = "insufficient_data"

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        redirect_mock.assert_called_with("verification.contact_details_not_found")
        with self.client as c:
            with c.session_transaction() as session:
                assert not session.get("email")
                assert not session.get("sms")

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    @patch('ndopapp.yourdetails.controllers.check_status_of_pds_search_result')
    def test_waiting_for_results_redirecting_when_timeout(self,
            check_status_of_pds_search_result_mock, redirect_mock, _):
        """ Test waiting_for_results page redirect to error when timeout"""
        common.registerExceptionHandlers(self.app)
        redirect_mock.return_value = "_"
        check_status_of_pds_search_result_mock.return_value = "pds_request_timeout"

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        redirect_mock.assert_called_with("main.generic_error")

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    @patch('ndopapp.yourdetails.controllers.check_status_of_pds_search_result')
    def test_waiting_for_results_redirecting_when_having_contact_details(self,
            check_status_of_pds_search_result_mock, redirect_mock, _):
        """ Test waiting_for_results page redirect to verificationoption when having contact details"""

        redirect_mock.return_value = "_"
        check_status_of_pds_search_result_mock.return_value = "success"
        with self.client as c:
            with c.session_transaction() as session:
                session["sms"] = common.USER_DETAILS.get("sms")
                session["email"] = common.USER_DETAILS.get("email")

        self.client.get(routes.get_raw("verification.waiting_for_results"))

        redirect_mock.assert_called_with("verification.verification_option")


if __name__ == '__main__':
    unittest.main()
