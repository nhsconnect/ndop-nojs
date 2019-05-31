from flask import Blueprint
from ndopapp.utils import log_safe_exception
from ndopapp.routes import redirect_to_route

errors_blueprint = Blueprint("errors", __name__)


@errors_blueprint.app_errorhandler(404)
def page_not_found(e):
    return "Page Not Found", 404


@errors_blueprint.app_errorhandler(Exception)
def handle_unexpected_error(exception):
    log_safe_exception(exception)
    return redirect_to_route('main.generic_error')
