import functools
import requests
import json
import boto3
from http import HTTPStatus

from flask import request, current_app as app, render_template, session
from flask.views import View

from ndopapp import routes
import traceback


class TemplateView(View):
    methods = ['GET']

    def __init__(self, view_name, template, requires_session=True):
        self.view_name = view_name
        self.template = template
        self.requires_session = requires_session

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        return super().as_view(name, name, *class_args, **class_kwargs)

    def dispatch_request(self):
        if self.requires_session:
            session_id = request.cookies.get('session_id_nojs')
            if not is_session_valid(session_id):
                return render_template('session-expired.html', routes=routes)
        return render_template(self.template, routes=routes)


def create_error_messages_dict(*args):
    return {i: [message] for i, message in enumerate(args)}
    

def check_session_id_if_no_flask_session(func):
    @functools.wraps(func)
    def skip_check_session_wrapper(*args):
        if session:
            return func(*args)
        return render_template('session-expired.html', routes=routes)
    return skip_check_session_wrapper


def check_session(func):
    @functools.wraps(func)
    def check_session_wrapper(*args):
        session_id = request.cookies.get('session_id_nojs')
        if is_session_valid(session_id):
            return func(session_id, *args)
        return render_template('session-expired.html', routes=routes)

    return check_session_wrapper


def is_session_valid(session_id):
    if not session_id:
        return False
    headers = {"Accept": "application/json"}
    cookies = dict(session_id=session_id)
    response = requests.get(url=app.config["CHECK_SESSION_URL"], headers=headers, cookies=cookies)
    return json.loads(response.text).get('valid')


def ensure_safe_redirect_url(target):

    white_list_endpoints = (
        routes.get_relative('yourdetails.your_details'),
        routes.get_relative('yourdetails.details_dob'),
        routes.get_relative('yourdetails.details_auth_option'),
        routes.get_relative('yourdetails.details_nhs_number'),
        routes.get_relative('yourdetails.details_postcode'),
        routes.get_relative('yourdetails.your_details_review')
    )

    if target not in white_list_endpoints:
        return routes.get_absolute('main.landing_page')

    return routes.make_absolute(target)


def log_safe_exception(exception):
    """logs the minimum details needed to debug an exception, and not the full exception to avoid leaking patient 
    confidential information"""

    exception_type = type(exception).__name__
    exception_traceback = exception.__traceback__
    exception_traceback_summary = traceback.extract_tb(exception_traceback).format()

    exception_info = {'exception_type': exception_type, 
                      'exception_traceback_summary': exception_traceback_summary}

    exception_message = getattr(exception, 'safe_message', None)

    if exception_message:
        exception_info.update({'exception_message': exception_message})
    
    app.logger.error('exception', exception_info)


def clean_state_model_locally(state_model_json):
    app.logger.info("clean_state_model_locally")

    session_id = request.cookies.get('session_id_nojs', '')

    return json.dumps({
        "session_id":  session_id,
        "state_model": {
            "session_id": session_id,
            "contact_centre": state_model_json.get('contact_centre'),
            "expiry_time_key": state_model_json.get('expiry_time_key', ''),
            "flow": state_model_json.get('flow', ''),
        }
    })


def get_full_aws_lambda_function_name(function_name):
    return "arn:aws:lambda:{}:{}:function:{}-{}".format(
        str(app.config.get("AWS_DEFAULT_REGION")),
        str(app.config.get("AWS_ACCOUNT_ID")),
        str(app.config.get("AWS_ENV_NAME")),
        function_name,
    )


def aws_lambda_invoke(func, data):
    app.logger.info(f"aws_lambda_invoke: {func}")

    resp = boto3.client('lambda').invoke(
        FunctionName=get_full_aws_lambda_function_name(func),
        Payload=data
    )

    status_code = resp['StatusCode']
    payload = json.loads(resp['Payload'].read())
    if status_code is not HTTPStatus.OK.value:
        app.logger.info(f'ERROR: aws_lambda_invoke: func={func}: status_code={status_code}')
        return None
    return payload


def aws_lambda_get_state_model():
    session_id = request.cookies.get('session_id_nojs', '')
    data = json.dumps({'session_id': session_id})
    return aws_lambda_invoke(func='get-state-model', data=data)


def aws_lambda_put_state_model(state_model_json):
    return aws_lambda_invoke(func='put-state-model', data=state_model_json)


def clean_state_model():
    """
    This function gets full state_model which we retrieved using
    aws_lambda_get_state_model and prepare 'fresh' state model with only few 
    json arguments  which is then passed back using put-state-model endpoint. 

    Such method of 'clearning state model' was implemented in JS version in file:
    ndop-front-end/screens/lookup-failure-error/renderer-ES6.js 
    """

    state_model_json = aws_lambda_get_state_model()
    if state_model_json:
        clear_state_model = clean_state_model_locally(state_model_json)
        aws_lambda_put_state_model(clear_state_model)
    else:
        app.logger.info("error while cleaning state model")

    return True


def is_nhs_number_valid(nhs_number):
    """ Checks if a given nhs number is a valid one

    For more information, see:
    https://www.datadictionary.nhs.uk/data_dictionary/attributes/n/nhs/nhs_number_de.asp?shownav=1

    Args:
        nhs_number (str): The NHS number

    Returns:
        bool: True if the NHS number is valid, False otherwise
    """
    if not nhs_number:
        app.logger.info("nhs_number_invalid", {'cause': 'no_number_provided'})
        return False

    nhs_number = str(nhs_number).replace(" ", "")

    if not nhs_number.isdigit():
        app.logger.info("nhs_number_invalid", {'cause': 'not_numeric'})
        return False

    if len(nhs_number) != 10:
        app.logger.info("nhs_number_invalid", {'cause': 'not_10_characters'})
        return False

    if calculate_nhs_number_check_digit(nhs_number) != int(nhs_number[9]):
        app.logger.info("nhs_number_invalid", {'cause': 'check_digit_failure'})
        return False

    app.logger.info("nhs_number_valid")
    return True


def calculate_nhs_number_check_digit(nhs_number):
    """Calculates the check digit for the NHS number

    For more information, see:
    https://www.datadictionary.nhs.uk/data_dictionary/attributes/n/nhs/nhs_number_de.asp?shownav=1

    Args:
        nhs_number (str):  NHS number

    Returns:
        int: The expected check digit for NHS number
    """
    check_digit_sum = sum(int(nhs_number[i]) * (10 - i) for i in range(9))
    check_digit = 11 - (check_digit_sum % 11)
    if check_digit == 11:
        return 0
    return check_digit

