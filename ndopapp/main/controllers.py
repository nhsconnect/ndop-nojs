from flask import Blueprint, redirect, render_template, request, make_response, session, current_app as app
from .forms import LandingPageForm
from ndopapp import utils
from ndopapp import routes

main_blueprint = Blueprint(
    "main", __name__, template_folder="../templates/main")


@main_blueprint.route(routes.get_raw("main.root"), strict_slashes=False)
@utils.catch_unhandled_exceptions
def index():
    app.logger.info("starting controller", {'controller': "main.index"})
    app.logger.info("session cleared")
    app.logger.info("redirecting", {'location': routes.get_absolute("main.landing_page")})
    return redirect(routes.get_absolute("main.landing_page"))


@main_blueprint.route(routes.get_raw("main.landing_page"), methods=("GET", "POST"))
@utils.catch_unhandled_exceptions
def landingpage():
    app.logger.info("starting controller", {'controller': "main.landing_page"})
    form = LandingPageForm()
    if request.method == "POST":
        app.logger.info("redirecting", {'location': "yourdetails.your_details"})
        resp = make_response(redirect(routes.get_absolute('yourdetails.your_details')))
        return resp

    app.logger.info('rendering page', {'page': 'landing_page'})
    resp = make_response(render_template("landing-page.html", form=form, routes=routes, page="landing",
                                         display_cookie_banner=request.cookies.get('ndop_seen_cookie_message')))

    if 'ndop_seen_cookie_message' not in request.cookies:
        resp.set_cookie('ndop_seen_cookie_message', 'true', max_age=2592000)

    session.clear()
    resp.set_cookie('session_id_nojs', '', max_age=0)

    return resp
