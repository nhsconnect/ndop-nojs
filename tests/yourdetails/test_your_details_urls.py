import requests_mock
import unittest
from unittest.mock import patch, MagicMock
import json
from flask import session
from ndopapp import routes, create_app
from ndopapp.yourdetails.controllers import render_template, redirect
from http import HTTPStatus

from tests import common


class TestYourDetailsURLs(unittest.TestCase):
    """ Test yourdetails routes"""

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie(
            "test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    # Your Details Route

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.request')
    def test_yourdetails_get(self, request_mock, _, **kwargs):
        """ Test your_details page returns a 200 """
        mock = kwargs['mock']
        request_mock.cookies.get('session_id').return_value = None
        request_mock.cookies.get('session').return_value = "some_session"
        
        mock.get(self.app.config['CREATE_SESSION_URL'],
                           status_code=HTTPStatus.OK,
                           text=common.create_session_callback)
        result = self.client.get('/yourdetails')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template', return_value='cookies-disabled_template')
    @patch('ndopapp.yourdetails.controllers.make_response', return_value='_')
    def test_yourdetails_renders_cookies_disabled(self, make_response_mock, render_mock, _, **kwargs):
        """ Test your_details page returns a 200 and renders_cookies disabled """
        mock = kwargs['mock']

        self.client.set_cookie("test", 'session', '')
        mock.get(self.app.config['CREATE_SESSION_URL'],
                 text=common.create_session_callback)
        result = self.client.get('/yourdetails')

        render_mock.assert_called_with('cookies-disabled.html')
        make_response_mock.assert_called_with('cookies-disabled_template', 400)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template', wraps=render_template)
    def test_yourdetails_set_form_values_from_session(self, render_template_spy, _):
        """ Test yourdetails set values from session """

        with self.client as c:
            with c.session_transaction() as session:
                session["first_name"] = "Greg"
                session["last_name"] = "General"

        self.client.get('/yourdetails')

        self.assertEqual("Greg", render_template_spy.mock_calls[0][2]['form'].first_name.data)
        self.assertEqual("General", render_template_spy.mock_calls[0][2]['form'].last_name.data)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template', wraps=render_template)
    def test_detailsdob_set_form_values_from_session(self, render_template_spy, _):
        """ Test details_dob set values from session """

        with self.client as c:
            with c.session_transaction() as session:
                session["dob"] = "something"
                session["dob_day"] = "10"
                session["dob_month"] = "11"
                session["dob_year"] = "1966"

        self.client.get('/detailsdob')

        self.assertEqual("10", render_template_spy.mock_calls[0][2]['form'].day.data)
        self.assertEqual("11", render_template_spy.mock_calls[0][2]['form'].month.data)
        self.assertEqual("1966", render_template_spy.mock_calls[0][2]['form'].year.data)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template', wraps=render_template)
    def test_detailsnhsnumber_set_form_values_from_session(self, render_template_spy, _):
        """ Test details_nhs_number set values from session """

        with self.client as c:
            with c.session_transaction() as session:
                session["nhs_number"] = "7777770003"

        self.client.get('/detailsnhsnumber')

        render_template_spy.assert_called_once()

        self.assertEqual("7777770003", render_template_spy.mock_calls[0][2]['form'].nhs_number.data)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template', wraps=render_template)
    def test_detailspostcode_set_form_values_from_session(self, render_template_spy, _):
        """ Test postcode set values from session """

        with self.client as c:
            with c.session_transaction() as session:
                session["postcode"] = "LS77DG"

        self.client.get('/detailspostcode')

        self.assertEqual("LS77DG", render_template_spy.mock_calls[0][2]['form'].postcode.data)

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @requests_mock.Mocker(kw='mock')
    def test_yourdetails_get_fetches_session_id_handle_error(self, _, **kwargs):
        """
        Test your_details page returns a 200 on fetch session id error
        but does not set session_id in cookie
        """
        common.registerExceptionHandlers(self.app)
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['CREATE_SESSION_URL'],
                           text=common.create_session_callback_fail)
        result = self.client.get('/yourdetails')

        assert HTTPStatus(result.status_code) == HTTPStatus.BAD_REQUEST
        assert not result.headers.get('Set-Cookie')

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @requests_mock.Mocker(kw='mock')
    def test_yourdetails_does_not_fetch_session_id_if_already_exists(self, _, **kwargs):
        """ Test your_details page returns a 400 and does not fetch session id if already exists """
        mock = kwargs['mock']
        adapter = mock.get(self.app.config['CREATE_SESSION_URL'])
        result = self.client.get('/yourdetails')

        assert HTTPStatus(result.status_code) == HTTPStatus.BAD_REQUEST
        assert mock.called_once is False

    def test_yourdetails_post(self):
        """ Test your-details page posts to details-dob """
        result = self.client.post(
            '/yourdetails', data=dict(first_name='firstname', last_name='lastname'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/detailsdob' in result.headers['Location']

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_yourdetails_post_invalid_does_not_redirect(self, _, **kwargs):
        """ Test your_details page with validation errors """
        mock = kwargs['mock']

        adapter = mock.get(self.app.config['CREATE_SESSION_URL'],
                           status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
        result = self.client.post(
            '/yourdetails', data=dict(first_name='first_name', last_name=''))

        assert HTTPStatus(result.status_code) == HTTPStatus.BAD_REQUEST

    # Your DOB Route
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_dob_get(self, _):
        """ Test details-dob page returns a 200 """
        result = self.client.get('/detailsdob')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_dob_post(self, _):
        """ Test details-dob  page posts to details-auth-option """
        result = self.client.post(
            '/detailsdob', data=dict(day=12, month=6, year=2000))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/detailsauthoption' in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_dob_invalid_does_not_redirect(self, _):
        """ Test details-dob page with validation errors """
        result = self.client.post(
            '/detailsdob', data=dict(day='', month='12', year=''))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    # Choose your auth method Route
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_auth_option_get(self, _):
        """ Test details-auth-option returns 200 """
        result = self.client.get('/detailsauthoption')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_auth_option_post_with_NHS_number(self, _):
        """ Test details_auth_option redirects to NHS number with NHS number option"""
        result = self.client.post(
            '/detailsauthoption', data=dict(radio='Yes'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/detailsnhsnumber' in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_auth_option_post_with_postcode(self, _):
        """ Test details_auth_option redirects to postcode with postcode option"""
        result = self.client.post(
            '/detailsauthoption', data=dict(radio='No'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/detailspostcode' in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_auth_option_invalid_does_not_redirect(self, _):
        """ Test details_auth_option with no choice made"""
        result = self.client.post('/detailsauthoption', data=dict(radio=''))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    # Your NHS number Route
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_nhs_number_get(self, _):
        """ Test details_nhs_number page returns a 200 """
        result = self.client.get('/detailsnhsnumber')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_nhs_number_post(self, _):
        """ Test details_nhs_number page posts to details-dob """
        result = self.client.post(
            '/detailsnhsnumber', data=dict(nhs_number='1234567890'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/yourdetailsreview' in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_nhs_number_post_invalid_does_not_redirect(self, _):
        """ Test details_nhs_number page with validation errors """
        result = self.client.post(
            '/detailsnhsnumber', data=dict(nhs_number='98765DDFNBH'))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_nhs_number_post_invalid_too_short__does_not_redirect(self, _):
        """ Test details_nhs_number page with validation errors """
        result = self.client.post(
            '/detailsnhsnumber', data=dict(nhs_number='9'))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    # Your Postcode Route
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_postcode_get(self, _):
        """ Test details_postcode page returns a 200 """
        result = self.client.get('/detailspostcode')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_postcode_post(self, _):
        """ Test details_postcode page posts to details-dob """
        result = self.client.post(
            '/detailspostcode', data=dict(postcode='LS12 6YU'))

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/yourdetailsreview' in result.headers['Location']

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_postcode_post_invalid_does_not_redirect(self, _):
        """ Test details_postcode page with validation errors """
        result = self.client.post(
            '/detailspostcode', data=dict(postcode='%RT YT5'))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_details_postcode_post_blank_does_not_redirect(self, _):
        """ Test details_postcode page with validation errors """
        result = self.client.post('/detailspostcode', data=dict(postcode=''))

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    # Your Details Review Route
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_your_details_review_postcode_get(self, _):
        """ Test your_details_review page returns a 200 when all session data is present """
        with self.client as c:
            with c.session_transaction() as session:
                session["first_name"] = "Adrian"
                session["last_name"] = "Smith"
                session["dob_day"] = "1"
                session["dob_month"] = "1"
                session["dob_year"] = "2000"
                session["nhs_number"] = "2345454545"

        result = self.client.get('/yourdetailsreview')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.yourdetails.models.clean_state_model', return_value="_")
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_your_details_review_post(self, _, __, **kwargs):
        """ Test your_details_review page posts to PDS_SEARCH_URL """

        mock = kwargs['mock']
        adapter = mock.post(
            self.app.config['PDS_SEARCH_URL'], text=common.pds_search_callback)
        headers = {'Content-type': 'application/json', 'cookie': None}

        with self.client as c:
            with c.session_transaction() as session:
                session["first_name"] = common.USER_DETAILS.get("firstName")
                session["last_name"] = common.USER_DETAILS.get("lastName")
                session["dob_day"] = common.USER_DETAILS.get("dateOfBirthDay")
                session["dob_month"] = common.USER_DETAILS.get("dateOfBirthMonth")
                session["dob_year"] = common.USER_DETAILS.get("dateOfBirthYear")
                session["nhs_number"] = common.USER_DETAILS.get("nhsNumber")
                session["postcode"] = common.USER_DETAILS.get("postcode")
                session["sms"] = common.USER_DETAILS.get("sms")
                session["email"] = common.USER_DETAILS.get("email")
                session["opted_out"] = common.USER_DETAILS.get("opted_out")
                session["otp_method"] = common.USER_DETAILS.get("otp_method")
                session["preference"] = common.USER_DETAILS.get("preference")

        result = self.client.post('/yourdetailsreview',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/waitingforresults' in result.headers['Location']
        assert mock.called_once is True
        assert adapter.last_request.json() == json.loads(common.PDS_SEARCH_POST_BODY.__str__().replace('\'', '"'))

    @requests_mock.Mocker(kw='mock')
    @patch('ndopapp.yourdetails.models.clean_state_model', return_value="_")
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_your_details_review_post_fail(self, _, __, **kwargs):
        """ Test generic error page rendered when post to PDS_SEARCH_URL unsuccessful"""

        common.registerExceptionHandlers(self.app)
        mock = kwargs['mock']
        adapter = mock.post(
            self.app.config['PDS_SEARCH_URL'], text=common.pds_search_callback)
        headers = {'Content-type': 'application/json',
                   'cookie': common.SESSION_ID}
        # headers={'Content-type': 'application/json', 'cookie': None}

        with self.client as c:
            with c.session_transaction() as session:
                session["first_name"] = "error"
                session["last_name"] = "Smith"
                session["dob_day"] = "1"
                session["dob_month"] = "1"
                session["dob_year"] = "2000"
                session["nhs_number"] = "9998880009"

        result = self.client.post('/yourdetailsreview',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert '/genericerror' in result.headers['Location']
        assert mock.called_once is True

    @patch('ndopapp.yourdetails.models.clean_state_model', return_value="_")
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_redirected_to_invalid_nhs_number_on_invalid_nhs_number_retry(self, *_):
        """The client is redirected to /invalidnhsnumber when an invalid nhs number is entered for a second time"""

        common.registerExceptionHandlers(self.app)
        headers = {'Content-type': 'application/json',
                   'cookie': common.SESSION_ID}

        with self.client as c:
            with c.session_transaction() as session:
                session["nhs_number_failed"] = True
                session["first_name"] = "Sam"
                session["last_name"] = "Smith"
                session["dob_day"] = "1"
                session["dob_month"] = "1"
                session["dob_year"] = "2000"
                session["nhs_number"] = "9998880000"

        result = self.client.post('/yourdetailsreview',
                                  data=json.dumps(common.USER_DETAILS),
                                  headers=headers)

        self.assertEqual(HTTPStatus(result.status_code), HTTPStatus.FOUND)
        self.assertIn('/invalidnhsnumber', result.headers['Location'])

    @patch('ndopapp.yourdetails.models.clean_state_model', return_value="_")
    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_redirected_to_nhs_number_not_accepted_on_invalid_nhs_number(self, *_):
        """The client is redirected to /nhsnumbernotaccepted when an invalid nhs number is entered"""

        common.registerExceptionHandlers(self.app)
        headers = {'Content-type': 'application/json',
                   'cookie': common.SESSION_ID}

        with self.client as c:
            with c.session_transaction() as sess:
                sess["first_name"] = "Sam"
                sess["last_name"] = "Smith"
                sess["dob_day"] = "1"
                sess["dob_month"] = "1"
                sess["dob_year"] = "2000"
                sess["nhs_number"] = "9998880000"

            result = self.client.post('/yourdetailsreview',
                                      data=json.dumps(common.USER_DETAILS),
                                      headers=headers)

            self.assertEqual(HTTPStatus(result.status_code), HTTPStatus.FOUND)
            self.assertIn('/nhsnumbernotaccepted', result.headers['Location'])

            # The failure is stored in the session
            self.assertTrue(session['nhs_number_failed'])

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    @patch('ndopapp.yourdetails.controllers.render_template')
    @patch('ndopapp.yourdetails.controllers.ReviewForm')
    def test_review_your_details_rerender(self, review_form_mock, render_mock, _):
        """ Test your_details_review rerender when invalid form """
        with self.client as c:
            with c.session_transaction() as session:
                session["first_name"] = "Andy"
                session["last_name"] = "Smith"
                session["dob_day"] = "1"
                session["dob_month"] = "1"
                session["dob_year"] = "2000"
                session["nhs_number"] = "2345454545"

        headers = {'Content-type': 'application/json', 'cookie': common.SESSION_ID}
        form_mock = MagicMock()
        form_mock.validate_on_submit.return_value = False

        review_form_mock.return_value = form_mock

        render_mock.return_value = "_"

        self.client.post('/yourdetailsreview',
                         data=json.dumps(common.USER_DETAILS),
                         headers=headers)

        render_mock.assert_called()

    @patch('ndopapp.utils.is_session_valid', return_value=True)
    def test_review_your_details_redirects_on_missing_data(self, _):
        """Review your details redirects to the appropriate page when session data is missing"""

        test_data = [
            ('/yourdetails', 'first_name'),
            ('/yourdetails', 'last_name'),
            ('/detailsdob', 'dob_day'),
            ('/detailsdob', 'dob_month'),
            ('/detailsdob', 'dob_year'),
        ]
        for redirect_url, missing_field in test_data:
            with self.subTest(redirect_url=redirect_url, missing_field=missing_field):

                with self.client as c:
                    with c.session_transaction() as session:
                        session["first_name"] = "Andy" if missing_field != "first_name" else None
                        session["last_name"] = "Smith" if missing_field != "last_name" else None
                        session["dob_day"] = "1" if missing_field != "dob_day" else None
                        session["dob_month"] = "1" if missing_field != "dob_month" else None
                        session["dob_year"] = "2000" if missing_field != "dob_year" else None
                        session["nhs_number"] = "2345454545" if missing_field != "nhs_number" else None

                response = self.client.get(
                    '/yourdetailsreview',
                    headers={'cookie': common.SESSION_ID}
                )

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.headers['Location'].endswith(redirect_url))

    @patch('ndopapp.utils.render_template')
    def test_choice_not_saved_renders_proper_template(self, render_mock):
        """ Test your_details_review rerender when invalid form """

        render_mock.return_value = "_"

        self.client.get('/choicenotsaved')

        render_mock.assert_called_with('choice-not-saved.html', routes=unittest.mock.ANY)


if __name__ == '__main__':
    unittest.main()
