import sys
import json
import requests
from http import HTTPStatus

from flask import current_app

from ndopapp import routes, constants
from ndopapp.models import NDOP_RequestError
from ndopapp.utils import log_safe_exception


def is_otp_verified_by_pds(session_id, code):

    code_json = json.dumps({'enterOtpInput': str(code)})
    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        pds_search_request = requests.post(
            url=current_app.config["VERIFY_CODE_URL"], headers=headers, data=code_json, cookies=cookies
        )

        pds_search_request.raise_for_status()

        if pds_search_request.status_code is HTTPStatus.OK.value:
            return constants.CORRECT_OTP
        elif pds_search_request.status_code is HTTPStatus.PARTIAL_CONTENT.value:
            return constants.INCORRECT_OTP

        return constants.UNKNOWN_RESULT

    except requests.exceptions.RequestException as exc:

        if isinstance(exc, requests.exceptions.HTTPError) \
                and exc.response.status_code == HTTPStatus.FORBIDDEN.value:
            return constants.INCORRECT_OTP

        if isinstance(exc, requests.exceptions.HTTPError) \
                and exc.response.status_code == HTTPStatus.NOT_ACCEPTABLE.value:
            return constants.INCORRECT_OTP_MAX_RETRIES

        if isinstance(exc, requests.exceptions.HTTPError) \
                and exc.response.status_code == HTTPStatus.UNAUTHORIZED.value:
            return constants.CORRECT_OTP_EXPIRED

        return constants.UNKNOWN_RESULT


def resend_code_by_pds(session_id):
    result = constants.UNKNOWN_RESULT

    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        pds_search_request = requests.get(
            url=current_app.config["PDS_RESEND_CODE_URL"], headers=headers, cookies=cookies
        )

        pds_search_request.raise_for_status()

        if pds_search_request.status_code is HTTPStatus.OK.value:
            ret = pds_search_request.json()

            if ret.get("resend_count"):
                return ret.get("resend_count")

        return result

    except requests.exceptions.RequestException as exc:

        if isinstance(exc, requests.exceptions.HTTPError) \
            and exc.response.status_code == HTTPStatus.NOT_ACCEPTABLE.value:
            return constants.RESEND_CODE_MAX_EXCEEDED

        exception_type = type(exc).__name__
        status_code = exc.response.status_code or "not_applicable"
        log_safe_exception(exc)
        raise NDOP_RequestError(f'resend code failed, original exception type {exception_type}, response status code {status_code}')


def request_code_by_pds(session_id, otp_delivery_type):
    result = constants.OTP_REQUEST_FAILURE

    json_content = json.dumps({'otp_delivery_type': str(otp_delivery_type)})
    headers = {"Content-type": "application/json"}
    cookies = dict(session_id=session_id)

    try:
        pds_search_request = requests.post(
            url=current_app.config["PDS_REQUEST_CODE_URL"], headers=headers, data=json_content, cookies=cookies
        )

        pds_search_request.raise_for_status()

        if pds_search_request.status_code is HTTPStatus.OK.value:
            result = constants.OTP_REQUEST_SUCCESS

        return result

    except requests.exceptions.RequestException as exc:

        if isinstance(exc, requests.exceptions.HTTPError) \
                and exc.response.status_code == 406:

            ret = exc.response.json()
            if ret.get("error") == \
                    constants.OTP_REQUEST_MAX_RETRIES:
                return constants.OTP_REQUEST_MAX_RETRIES
            return constants.OTP_REQUEST_FAILURE

        exception_type = type(exc).__name__
        status_code = exc.response.status_code or "not_applicable"
        log_safe_exception(exc)
        raise NDOP_RequestError(f'request code failed, original exception type {exception_type}, response status code {status_code}')
