import uuid, datetime, functools
from errors.InvalidSessionCookie import InvalidSessionCookie
from flask import request, make_response
from flask import current_app as app
import session, os
import mock

COOKIE_EXPIRY = 59


def create_session_cookie():
    return f"session_id={uuid.uuid4()}; expires={__format_date()}; HttpOnly; Secure"


def __format_date():
    global COOKIE_EXPIRY
    now = datetime.datetime.now()
    expiry = now + datetime.timedelta(minutes=COOKIE_EXPIRY)
    return expiry.strftime("%a, %d %b %Y %H:%M:%S GMT")


def check_cookies(func):
    @functools.wraps(func)
    def cookies_wrapper(*args):
        session_cookie = check_session_cookie()
        resp = make_response()
        return func(session_cookie, resp, *args)

    return cookies_wrapper


def check_session_cookie():
    session_cookie = request.cookies.get('session_id')

    session_string = f'session_id={session_cookie}'
    if session_string not in session.get_sessions():
        raise InvalidSessionCookie("Invalid session cookie", status_code=403)

    return session_cookie
