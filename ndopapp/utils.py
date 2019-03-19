import functools
import requests
import json
import boto3
from http import HTTPStatus

from flask import request, current_app as app, \
        render_template, session, make_response, redirect

from ndopapp import routes
import traceback


def create_error_messages_dict(*args):
    messages = {}
    counter = 0

    for message in args:
        messages[counter] = [message]
        counter = counter + 1

    return messages

def catch_unhandled_exceptions(func):
    """catching the unhandled exceptions bubbled up and redirect them to generic error page"""
    @functools.wraps(func)
    def catch_exceptions_wrapper(*args):
        try:
            return func(*args)
        except Exception as e:
            log_safe_exception(e)
            return redirect(routes.get_absolute("yourdetails.generic_error"))
    
    return catch_exceptions_wrapper


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

    clean_state_model = {
        "session_id":  session_id,
        "state_model": {
            "session_id": session_id,
            "contact_centre": state_model_json.get('contact_centre'),
            "expiry_time_key": state_model_json.get('expiry_time_key', ''),
            "flow": state_model_json.get('flow', ''),
        }
    }

    return json.dumps(clean_state_model)


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
