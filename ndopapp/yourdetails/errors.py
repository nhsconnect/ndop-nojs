from .models import NDOP_RequestError

from flask import Blueprint, render_template
from ndopapp import routes

yourdetails_errors_blueprint = Blueprint("errors", __name__)


@yourdetails_errors_blueprint.app_errorhandler(NDOP_RequestError)
def handle_request_error(error):

    try:
        messages = [str(error.args[0][1])]

    except Exception:
        messages = "EXCEPTION_ERROR"

    return render_template("error.html", messages=messages, routes=routes), 500


@yourdetails_errors_blueprint.app_errorhandler(404)
def page_not_found(e):
    return "Page Not Found", 404


@yourdetails_errors_blueprint.app_errorhandler(Exception)
def handle_unexpected_error(error):
    messages = [str(x) for x in error.args]

    return render_template("error.html", messages=messages, routes=routes), 500
