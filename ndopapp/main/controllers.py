from flask import Blueprint, render_template, request, make_response, session, current_app as app
from ndopapp.utils import TemplateView
from .forms import LandingPageForm
from ndopapp import routes
from ndopapp.routes import redirect_to_route
from ndopapp.csrf import csrf


main_blueprint = Blueprint(
    "main", __name__, template_folder="../templates/main"
)


@main_blueprint.route(routes.get_raw("main.root"), strict_slashes=False)
def index():
    return redirect_to_route("main.landing_page")


@main_blueprint.route(routes.get_raw("main.landing_page"), methods=("GET", "POST"))
@csrf.exempt
def landing_page():
    if request.method == "POST":
        return make_response(redirect_to_route('yourdetails.your_details'))

    session.clear()
    app.logger.info("session cleared")

    form = LandingPageForm()
    resp = make_response(
        render_template(
            "landing-page.html",
            form=form,
            routes=routes,
            page="landing",
            display_cookie_banner=request.cookies.get('ndop_seen_cookie_message')
        )
    )

    if 'ndop_seen_cookie_message' not in request.cookies:
        resp.set_cookie('ndop_seen_cookie_message', 'true', max_age=2592000)
    resp.set_cookie('session_id_nojs', '', max_age=0)

    return resp


main_blueprint.add_url_rule(
    routes.get_raw("main.generic_error"),
    view_func=TemplateView.as_view(
        'generic_error',
        'error.html',
        requires_session=False
    )
)
