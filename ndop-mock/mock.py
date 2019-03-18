import json, os

from flask import Flask, make_response, request, jsonify, url_for
from flask_swagger_ui import get_swaggerui_blueprint
from errors.InvalidSessionCookie import InvalidSessionCookie
from errors.InvalidContentType import InvalidContentType
from errors.BadUserException import BadUserException
from models.user import User
import counter, cookies, session
import json
from urllib import parse
from http.cookies import SimpleCookie
from logging.config import dictConfig
from data.invalid_sessions import INVALID_SESSIONS

app = Flask(__name__)

SWAGGER_URL = '/docs'
SWAGGER_API_URL = app.static_url_path + '/swagger.yaml'
SWAGGER_FILE = 'swagger.yaml'
dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
            }
        },
    }
)


@app.route("/swagger", methods=["GET"])
def swagger():
    return SWAGGER_FILE


blueprint = get_swaggerui_blueprint(SWAGGER_URL, SWAGGER_API_URL)
app.register_blueprint(blueprint, url_prefix=SWAGGER_URL)


@app.route("/")
def root():
    return list_routes()


@app.route("/createsession", methods=["GET"])
def create_session():
    session_id = cookies.create_session_cookie()
    cookie = SimpleCookie()
    cookie.load(session_id)
    session.add_session(cookie["session_id"].value)
    resp = make_response("{}", 200)
    resp.set_cookie(session_id)
    return resp


@app.route("/checksession", methods=["GET"])
def check_session():
    session_id = request.cookies.get('session_id')
    if not session_id or session_id in INVALID_SESSIONS:
        return make_response(json.dumps({"valid": False}), 200)
    return make_response(json.dumps({"valid": True}), 200)


@app.route("/details", methods=["POST"])
@cookies.check_cookies
def details(session_cookie, resp):
    check_content_type(request)
    user = User(request.get_json(force=True))
    session.add_user_to_session(session_cookie, user)
    resp.set_data("{}")
    return resp


@app.route("/patientsearchresult", methods=["GET"])
@cookies.check_cookies
def patient_search_result(session_cookie, resp):
    if check_user_returning_500(session_cookie):
        return make_response({}, 500)
    if not counter.check_and_decrement():
        return make_response('{"search_result": "incomplete"}', 206)
    user = session.get_user_from_session(session_cookie)
    return user.generate_pds_search_response()


@app.route("/requestcode", methods=["POST"])
@cookies.check_cookies
def request_code(session_cookie, resp):
    if check_user_returning_500(session_cookie):
        return make_response({}, 500)
    user = session.get_user_from_session(session_cookie)
    user.communication_type = request.get_json(force=True)["otp_delivery_type"]
    session.add_user_to_session(session_cookie, user)

    counter_response = counter.increase_counter_for(session_cookie, counter.RESEND_OTP_COUNTER_NAME)

    if counter_response is counter.CounterIncreasingResponse.MAX_NOT_REACHED:
        check_content_type(request)
        return make_response(json.dumps({}))

    return make_response('{"error": "max_count_exceeded"}', 406)


@app.route("/resendcode", methods=["GET"])
@cookies.check_cookies
def resend_code(session_cookie, resp):

    if check_user_returning_500(session_cookie):
        return make_response({}, 500)

    counter_response = counter.increase_counter_for(session_cookie, counter.RESEND_OTP_COUNTER_NAME)

    if counter_response is counter.CounterIncreasingResponse.MAX_NOT_REACHED:
        return make_response(json.dumps({"resend_count": "success"}))

    if counter_response is counter.CounterIncreasingResponse.MAX_REACHED:
        return make_response(json.dumps({"resend_count": "max_count_reached"}))

    return make_response(json.dumps({"resend_count": "max_count_exceeded"}), 406)


@app.route("/verifycode", methods=["POST"])
@cookies.check_cookies
def verify_code(session_cookie, resp):
    check_content_type(request)
    code = request.get_json(force=True)["enterOtpInput"]

    if code == "000000":
        # expired valid code
        return make_response(json.dumps({'error': 'unauthorized'}), 401)

    if code != "666666":
        # valid code
        return make_response('', 200)

    counter_response = counter.increase_counter_for(session_id=session_cookie,
                                                    counter_name=counter.VERIFY_OTP_COUNTER_NAME)

    if counter_response is counter.CounterIncreasingResponse.MAX_NOT_REACHED:
        return make_response(json.dumps({"warning": "invalid_otp_entered"}), 206)

    return make_response(json.dumps({"warning": "invalid_otp_entered"}), 406)


@app.route("/getpreferenceresult", methods=["GET"])
@cookies.check_cookies
def get_preference_result(session_cookie, resp):
    user = session.get_user_from_session(session_cookie)

    if not counter.preferences_check_and_decrement():
        return make_response(json.dumps({"get_preference_result": "incomplete"}), 206)

    # special case to test 401 status
    if user.firstname == "Fauro" and user.lastname == "Wan":
        return make_response(json.dumps({"get_preference_result": "get_preference_error"}), 401)

    return make_response(json.dumps({"get_preference_result": "success", "opted_out": user.opted_out}), 200)


@app.route("/setpreferences", methods=["POST"])
@cookies.check_cookies
def set_preferences(session_cookie, resp):
    check_content_type(request)
    user = session.get_user_from_session(session_cookie)
    if any(key != "preference" for key in request.get_json()):
        return make_response('{}', 403)
    user.preference = request.get_json(force=True)["preference"]
    print(f'User preference: {user.preference}')
    if user.preference == "optedIn":
        user.opted_out = "inactive"
    if user.preference == "optedOut":
        user.opted_out = "active"
    session.add_user_to_session(session_cookie, user)
    print(f'User opted_out is: {user.opted_out}')
    resp.set_data("{}")
    return resp


@app.route("/confirmationdeliverymethod", methods=["GET"])
@cookies.check_cookies
def confirmation_delivery_method(session_cookie, resp):
    user = session.get_user_from_session(session_cookie)

    data = {'preference': user.preference}
    print(f'User preference in confirmationdeliverymethod is {user.preference}')

    if user.communication_type == "email":
        data['email'] = user.email

    if user.communication_type == "sms":
        data['sms'] = user.sms

    resp.set_data(json.dumps(data))
    return resp


@app.route("/confirmationsender", methods=["GET"])
@cookies.check_cookies
def confirmation_sender(session_cookie, resp):
    resp.set_data("{}")
    return resp


@app.route("/storepreferencesresult", methods=["GET"])
@cookies.check_cookies
def store_preferences_result(session_cookie, resp):
    if not counter.result_check_and_decrement():
        return make_response('{"search_result": "incomplete"}', 206)
    user = session.get_user_from_session(session_cookie)
    if user.firstname == 'Wan' and user.lastname == 'Fauro':
        return make_response(json.dumps({"store_result": "store_preference_error"}), 401)
    print(f'User preference now is: {user.preference}')
    resp.set_data(json.dumps({"store_result": "success", "preference": user.preference}))
    resp.headers["set-cookie"] = 'session_id=""'
    return resp


@app.errorhandler(InvalidSessionCookie)
def handle_invalid_session_cookie(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(InvalidContentType)
def handle_invalid_content_type(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(BadUserException)
def handle_bad_user(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/pdssearchresult", methods=["GET"])
def get_pds_search_result():
    pds_search_result = {
        "search_result": "success",
        "email": "emai****@nhs.net",
        "sms": "*******1524"
    }
    resp = make_response(json.dumps(pds_search_result), 200)
    return resp


def check_content_type(request):
    if not request.headers["Content-Type"] == "application/json":
        raise InvalidContentType("Invalid content type")
        

def check_user_returning_500(session_cookie):
    user = session.get_user_from_session(session_cookie)
    if user.firstname == "Five" and user.lastname == "Hundred":
        return True
    return False

if __name__ == "__main__":
    app.run()


def list_routes():
    output = "<HTML>NDOP Mock<ul>"
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = "<li>{} {}</li>".format(methods, parse.unquote(url))
        output += line

    output += "</ul>"
    return output

@app.route("/get-state-model", methods=["GET"])
@cookies.check_cookies
def get_state_model_endpoint(session_cookie, resp):
    session_id = request.get_json(force=True)["session_id"]
    SAMPLE_STATE_MODEL = {
        "session_id":  session_id,
        "state_model": {
            "session_id": session_id,
            "contact_centre": False,
            "expiry_time_key": "1551374328",
            "flow": "nhs_number", #+test None
            "code": "SMSP-0000",
            "message_id": "6E2DDAE3-00D9-4084-8059-48530D3EAA37",
            "email_address": "greg0003@tbd-test.com",
            "nhs_number": "7777770003",
            "ndop_code_type": "ndop_info",
            "otp": {
                "salt": "db9e70994b8544dfa8f120e8d6b7b057",
                "hashed_otp": "b'3a2969309cd6d691b6b452f7f77099a424c4652ff53acb491da5190442f768c6'",
                "created": 1551372551
            },
            "validated_user": True,
            "existing_preference": {
                "is_present": True,
                "id": "7777770003.4f35c034-1b24-4f07-afd6-c6099de5cbb1",
                "status": "inactive"
            },
            "get_preference_result": "success"
        }
    }
    print(f'get_state_model_endpoint: {SAMPLE_STATE_MODEL}')
    resp.set_data(json.dumps(SAMPLE_STATE_MODEL))
    return resp


@app.route("/put-state-model", methods=["POST"])
@cookies.check_cookies
def put_state_model_endpoint(session_cookie, resp):
    state_model_json = request.get_json(force=True)
    print(f'put_state_model_endpoint: {state_model_json}')
    return resp
