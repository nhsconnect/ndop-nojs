import json
from http import HTTPStatus
from bs4 import BeautifulSoup

from ndopapp.yourdetails.controllers import yourdetails_blueprint
from ndopapp.main.errors import errors_blueprint

SESSION_COOKIE_KEY = "session_id"
SESSION_ID = "ca9d0f77-7c2b-4e8c-b161-50c79d559a2a"
USER_MOBILE = "07871248608"
SAMPLE_SESSION = "sample_session"

USER_DETAILS = {
    "firstName": "Ghosty",
    "lastName": "McGhostFace",
    "dateOfBirthDay": "6",
    "dateOfBirthMonth": "6",
    "dateOfBirthYear": "1966",
    "nhsNumber": "6666666666",
    "postcode": "GG66GG",
    "sms": "*******666",
    "email": "*********st@mail.com",
    'opted_out': "inactive",
    'otp_method': "sms",
    'preference': 'optedIn'
}

PDS_SEARCH_POST_BODY = {
    "firstName": USER_DETAILS.get("firstName"),
    "lastName": USER_DETAILS.get("lastName"),
    "dateOfBirthDay": USER_DETAILS.get("dateOfBirthDay"),
    "dateOfBirthMonth": USER_DETAILS.get("dateOfBirthMonth"),
    "dateOfBirthYear": USER_DETAILS.get("dateOfBirthYear"),
    "nhsNumber": USER_DETAILS.get("nhsNumber"),
    "postcode": USER_DETAILS.get("postcode"),
}


def get_user_details():
    return USER_DETAILS.copy()


def update_session_data(client, data):
    with client.session_transaction() as sess:
        sess.update(data)

def set_session_data(client, data):
    with client.session_transaction() as sess:
        sess.clear()
        sess.update(data)

def get_session_data(client):
    with client.session_transaction() as sess:
        return sess


def registerExceptionHandlers(app):
    """
    Exception Handlers by default are not connected when in test mode,
    but for tests which require them we can re-register the Exception Handlers
    """
    app.register_blueprint(errors_blueprint)


# DECORATOR HELPER METHODS

def unset_cookie_session_id(func):
    """Decorator function to null the cookie session id"""

    def set_cookie_wrapper(*args):
        client = args[0].client
        client.set_cookie("test_urls", SESSION_COOKIE_KEY, '')
        return func(*args)

    return set_cookie_wrapper


# REQUEST CALLBACK FUNCTIONS
def create_session_callback(request, context):
    context.status_code = HTTPStatus.OK.value
    context.headers['Set-Cookie'] = f"{SESSION_COOKIE_KEY}={SESSION_ID};session={SAMPLE_SESSION}"
    return 'response'


def html(response):
    return BeautifulSoup(response.data, 'html.parser')


def create_session_callback_fail(request, context):
    context.status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    return ''


def pds_search_callback(request, context):
    context.status_code = HTTPStatus.OK.value

    if "error" in request.body:
        context.status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value

    return ''


def get_preference_results_callback_inactive(request, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps(
        {"get_preference_result": "success", "opted_out": "inactive"})
    return body


def get_preference_results_callback_active(request, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps(
        {"get_preference_result": "success", "opted_out": "active"})
    return body


def pds_search_results_callback(request, context):
    context.status_code = HTTPStatus.OK.value
    body = json.dumps({"search_result": "success", "sms": USER_MOBILE})
    return body
