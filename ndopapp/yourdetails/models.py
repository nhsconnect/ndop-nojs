import sys
import json
import requests

from http import HTTPStatus
from flask import session, g, current_app as app

from ndopapp import constants
from ndopapp.models import NDOP_RequestError
from ndopapp.utils import log_safe_exception, clean_state_model


class UserDetails:
    def __init__(self):
        if session:
            self.firstName = session.get('first_name', '')
            self.lastName = session.get('last_name', '')
            self.dateOfBirthDay = session.get('dob_day', '')
            self.dateOfBirthMonth = session.get('dob_month', '')
            self.dateOfBirthYear = session.get('dob_year', '')
            self.nhsNumber = str(session.get('nhs_number', ''))
            self.postcode = session.get('postcode', '')
            self.sms = session.get('sms', '')
            self.email = session.get('email', '')
            self.opted_out = session.get('opted_out', '')
            self.otp_method = session.get('otp_method', '')

            self.preference = ""
            if self.opted_out == 'active':
                self.preference = "optedOut"

            if self.opted_out == 'inactive':
                self.preference = "optedIn"

    def __str__(self):
        """ method to print out string representation of object"""
        return str(self.__class__) + ": " + str(self.__dict__)

    @property
    def dob(self):
        """ method to build dob string"""
        return " ".join([
            self.dateOfBirthDay.strip(' '),
            self.dateOfBirthMonth.strip(' '),
            self.dateOfBirthYear.strip(' ')
        ])


def get_session_id():
    session_id = ""

    try:
        app.logger.info("creating new session")
        create_session_request = requests.get(
            url=app.config["CREATE_SESSION_URL"]
        )
        create_session_request.raise_for_status()

        if HTTPStatus(create_session_request.status_code) is HTTPStatus.OK:
            session_id = create_session_request.cookies.get("session_id")
            g.session_id_override = session_id
        app.logger.info("session created", {'session_id': session_id})
        return session_id

    except requests.exceptions.RequestException as exc:
        exception_type = type(exc).__name__
        status_code = exc.response.status_code or "not_applicable"
        log_safe_exception(exc)
        raise NDOP_RequestError(f'session creation failed, original exception type {exception_type}, response status code {status_code}')


def do_pds_search(user_details, session_id):
    search_result = ""
    user_json = json.dumps({
        "firstName": user_details.firstName,
        "lastName": user_details.lastName,
        "dateOfBirthDay": user_details.dateOfBirthDay,
        "dateOfBirthMonth": user_details.dateOfBirthMonth,
        "dateOfBirthYear": user_details.dateOfBirthYear,
        "nhsNumber": user_details.nhsNumber,
        "postcode": user_details.postcode
    })

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    #TDBAT-415 - clean state model before each PDS search
    clean_state_model()

    try:
        app.logger.info("submitting pds search")
        pds_search_request = requests.post(
            url=app.config["PDS_SEARCH_URL"],
            headers=headers,
            data=user_json,
            cookies=cookies,
            timeout=app.config["PDS_REQUEST_TIMEOUT"],
        )

        pds_search_request.raise_for_status()

        if HTTPStatus(pds_search_request.status_code) is HTTPStatus.OK:
            search_result = "success"

        app.logger.info("pds search submitted", {"search_result": search_result})
        return search_result

    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.Timeout):
            return constants.PDS_REQUEST_TIMEOUT

        if (isinstance(e, requests.exceptions.HTTPError) and
                e.response.status_code == HTTPStatus.NOT_ACCEPTABLE):
            return constants.PDS_RESULT_INVALID_AGE

        exc_info = sys.exc_info()
        app.logger.warning("pds search failed", exc_info=exc_info)
        return constants.UNKNOWN_RESULT


def check_status_of_pds_search_result(session_id):
    search_result = ""
    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        app.logger.info("submitting pds search result request")
        pds_search_result_request = requests.get(
            url=app.config["PDS_SEARCH_RESULT_URL"],
            headers=headers,
            cookies=cookies,
            timeout=app.config["PDS_REQUEST_TIMEOUT"],
        )
        pds_search_result_request.raise_for_status()

        if HTTPStatus(pds_search_result_request.status_code) is HTTPStatus.OK:
            result = pds_search_result_request.json()

            # TODO: Remove functional side effects of writing to session
            if result.get("sms"):
                session["sms"] = result.get("sms")
            if result.get("email"):
                session["email"] = result.get("email")

            search_result = result.get("search_result")

        app.logger.info("pds search result response received", {"search_result": search_result})
        return search_result

    except requests.exceptions.RequestException as exc:
        if isinstance(exc, requests.exceptions.Timeout):
            return constants.PDS_REQUEST_TIMEOUT
        if isinstance(exc, requests.exceptions.HTTPError) \
                and HTTPStatus(exc.response.status_code) == HTTPStatus.UNAUTHORIZED:
            return "invalid_user"
        if isinstance(exc, requests.exceptions.HTTPError) \
                and HTTPStatus(exc.response.status_code) == HTTPStatus.UNPROCESSABLE_ENTITY:
            return "insufficient_data"
        if isinstance(exc, requests.exceptions.HTTPError) \
                and HTTPStatus(exc.response.status_code) == HTTPStatus.NOT_ACCEPTABLE:
            return "age_restriction_error"

        exception_type = type(exc).__name__
        status_code = exc.response.status_code or "not_applicable"
        log_safe_exception(exc)
        raise NDOP_RequestError(f'pds search result request failed, original exception type {exception_type}, response status code {status_code}')


def get_current_preference(session_id):
    """retunrs False if not successful """
    app.logger.info("getting current preference")

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        preference_result_request = requests.get(
            url=app.config["PREFERENCE_RESULT_URL"], headers=headers, cookies=cookies
        )
        preference_result_request.raise_for_status()

        if HTTPStatus(preference_result_request.status_code) is HTTPStatus.OK:
            result = preference_result_request.json()
            if result.get("get_preference_result") == constants.GET_PREFERENCE_SUCCESS:
                if result.get("opted_out") in ('active', 'inactive'):
                    return result.get("opted_out")
                else:
                    return constants.GET_PREFERENCE_EMPTY
        elif HTTPStatus(preference_result_request.status_code) is HTTPStatus.PARTIAL_CONTENT:
            return constants.GET_PREFERENCE_INCOMPLETE

    except requests.exceptions.RequestException:
        return constants.GET_PREFERENCE_FAILURE

    return constants.GET_PREFERENCE_EMPTY


def get_confirmation_delivery_details(session_id):
    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        pds_search_result_request = requests.get(
            url=app.config["GET_CONFIRMATION_DELIVERY_METHOD"], headers=headers, cookies=cookies
        )
        pds_search_result_request.raise_for_status()

        if HTTPStatus(pds_search_result_request.status_code) is HTTPStatus.OK:
            result = pds_search_result_request.json()

            if 'email' in result:
                result['method'] = 'email'

            if 'sms' in result:
                result['method'] = 'sms'

            return result

        app.logger.info("confirmationdeliverymethod incorrect status: {}".\
                format(str(pds_search_result_request.status_code)))
        return None

    except requests.exceptions.RequestException as exc:
        app.logger.info("exception in confirmationdeliverymethod")
        return None


def set_preference(user_details, session_id):
    app.logger.info("setting preference")

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)
    user_json = json.dumps({"preference" : user_details.preference})

    try:
        preference_result_request = requests.post(
            url=app.config["SET_PREFERENCE_URL"], headers=headers, data=user_json, cookies=cookies
        )
        preference_result_request.raise_for_status()

        if HTTPStatus(preference_result_request.status_code) is HTTPStatus.OK:
            return True

    except requests.exceptions.RequestException as e:
        if isinstance(e, requests.exceptions.HTTPError) \
                and HTTPStatus(e.response.status_code) == HTTPStatus.FORBIDDEN:
            app.logger.info("set_preference: {status_code: 403, status: FORBIDDEN}")
            return False

    app.logger.info("preference not set successfully")
    return False


def store_preference(session_id):
    app.logger.info("storing preference result")

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        preference_result_request = requests.get(
            url=app.config["SET_PREFERENCE_RESULT_URL"],
            headers=headers,
            cookies=cookies
        )
        preference_result_request.raise_for_status()
        app.logger.info("store_preference_result", {"status_code": preference_result_request.status_code})

        if HTTPStatus(preference_result_request.status_code) is HTTPStatus.OK:
            return "success"

        if HTTPStatus(preference_result_request.status_code) is HTTPStatus.PARTIAL_CONTENT:
            return "not_completed"

    except requests.exceptions.RequestException as e:
        app.logger.info("storing preference exception")
        return "failure"

    app.logger.info("storing preference result failure")
    return "failure"


def confirm_preference(session_id):
    app.logger.info("confirming preference result")

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        preference_result_request = requests.get(
            url=app.config["CONFIRMATION_SENDER_URL"],
            headers=headers,
            cookies=cookies
        )
        preference_result_request.raise_for_status()

        if HTTPStatus(preference_result_request.status_code) is HTTPStatus.OK:
            return True

    except requests.exceptions.RequestException as e:
        app.logger.info("confirming preference exception")
        return False

    app.logger.info("confirming preference result failure")
    return False
