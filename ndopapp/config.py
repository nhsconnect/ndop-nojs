import os
from base64 import b64decode


def ensure_trailing_slash(string):
    return string.strip("/") + "/"


def ensure_leading_slash(string):
    if string.startswith('/'):
        return string
    return "/" + string


basedir = os.path.abspath(os.path.dirname(__file__))
ENCODED_SECRET_KEY = os.environ.get('SECRET_KEY', '2ci+prYkenQShibIB9+tCntSeH3fJ8Li')

NDOP_MOCK_HOST = os.environ.get('NDOP_MOCK_HOST', "localhost")
NDOP_MOCK_PORT = os.environ.get('NDOP_MOCK_PORT', 5001)
NDOP_MOCK_URL = f'http://{NDOP_MOCK_HOST}:{NDOP_MOCK_PORT}/'

CLIENT_FACING_URL = ensure_trailing_slash(os.environ.get("CLIENT_FACING_URL", "http://localhost:5000/"))
API_URL = ensure_trailing_slash(os.environ.get("API_URL", NDOP_MOCK_URL))
URL_PREFIX = os.environ.get("URL_PREFIX", "")
SERVER_NAME = os.environ.get('SERVER_NAME')

if len(URL_PREFIX) > 0:
    URL_PREFIX = ensure_leading_slash(URL_PREFIX)


class Config(object):
    SECRET_KEY = b64decode(ENCODED_SECRET_KEY)
    PDS_REQUEST_TIMEOUT = 30
    META_REFRESH_INTERVAL = 5
    SERVICE_NAME = "Choose if data from your health records is shared for research and planning"
    CLIENT_FACING_URL = CLIENT_FACING_URL
    URL_PREFIX = URL_PREFIX
    PDS_SEARCH_URL = API_URL + "details"
    CREATE_SESSION_URL = API_URL + "createsession"
    CHECK_SESSION_URL = API_URL + "checksession"
    PREFERENCE_RESULT_URL = API_URL + "getpreferenceresult"
    PDS_SEARCH_RESULT_URL = API_URL + "patientsearchresult"
    VERIFY_CODE_URL = API_URL + "verifycode"
    PDS_RESEND_CODE_URL = API_URL + "resendcode"
    PDS_REQUEST_CODE_URL = API_URL + "requestcode"
    SET_PREFERENCE_URL = API_URL + "setpreferences"
    SET_PREFERENCE_RESULT_URL = API_URL + "storepreferencesresult"
    GET_CONFIRMATION_DELIVERY_METHOD = API_URL + "confirmationdeliverymethod"
    CONFIRMATION_SENDER_URL = API_URL + "confirmationsender"
    GET_STATE_MODEL_FUNCTION_NAME = API_URL + "get-state-model"
    PUT_STATE_MODEL_FUNCTION_NAME = API_URL + "put-state-model"

    AWS_ACCOUNT_ID = os.environ.get('AWS_ACCOUNT_ID')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', "eu-west-2")
    AWS_ENV_NAME = os.environ.get('ENV_NAME')


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False


