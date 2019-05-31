import time

from flask import (
    Blueprint,
    flash,
    render_template,
    session,
    redirect,
    request,
    make_response,
    g,
    current_app as app
)

from ndopapp import routes, constants, utils
from ndopapp.utils import TemplateView
from ndopapp.routes import redirect_to_route

from .models import (
    UserDetails,
    get_session_id,
    do_pds_search,
    check_status_of_pds_search_result,
    get_current_preference,
    get_confirmation_delivery_details,
    get_store_preference_result,
    confirm_preference,
    set_preference
)
from .forms import (
    NameForm,
    DOBForm,
    AuthOption,
    NHSNumberForm,
    PostcodeForm,
    ReviewForm,
    ChoiceOption
)

yourdetails_blueprint = Blueprint(
    "yourdetails", __name__, template_folder="../templates/yourdetails"
)

FIRST_NAME = "first_name"
LAST_NAME = "last_name"
DOB_DAY = "dob_day"
DOB_MONTH = "dob_month"
DOB_YEAR = "dob_year"
DOB = "dob"
DAY = "day"
MONTH = "month"
YEAR = "year"
NHS_NUMBER = "nhs_number"
POST_CODE = "postcode"


yourdetails_blueprint.add_url_rule(
    routes.get_raw("yourdetails.choice_not_saved"),
    view_func=TemplateView.as_view(
        'choice_not_saved',
        'choice-not-saved.html',
        requires_session=False
    )
)


yourdetails_blueprint.add_url_rule(
    routes.get_raw("yourdetails.invalid_nhs_number"),
    view_func=TemplateView.as_view(
        'invalid_nhs_number',
        'invalid-nhs-number.html',
        requires_session=True
    )
)


yourdetails_blueprint.add_url_rule(
    routes.get_raw("yourdetails.nhs_number_not_accepted"),
    view_func=TemplateView.as_view(
        'nhs_number_not_accepted',
        'nhs-number-not-accepted.html',
        requires_session=True
    )
)


yourdetails_blueprint.add_url_rule(
    routes.get_raw("yourdetails.set_preference_error"),
    view_func=TemplateView.as_view(
        'set_preference_error',
        'set-preference-error.html'
    )
)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.your_details"), methods=("GET", "POST"))
def your_details():
    form = NameForm(data={
        'first_name': session.get(FIRST_NAME),
        'last_name': session.get(LAST_NAME),
    })

    if form.validate_on_submit():
        session[FIRST_NAME] = form.first_name.data
        session[LAST_NAME] = form.last_name.data
        session.modified = True
        app.logger.info("redirecting", {'location': routes.get_raw("yourdetails.details_dob")})
        redirect_url = utils.ensure_safe_redirect_url(
            request.args.get('next', routes.get_relative("yourdetails.details_dob")))
        return redirect(redirect_url)
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    # if still not 'session' cookie at this point we assume cookies are
    # disabled on user's web browser
    if not request.cookies.get('session'):
        return make_response(render_template('cookies-disabled.html'), 400)

    response = make_response(render_template("your-details.html", form=form, routes=routes))

    # get session id
    if not request.cookies.get("session_id_nojs"):
        session_id = get_session_id()
        g.session_id_override = session_id
        if session_id:
            # set session_id cookie to expire after 59 minutes
            response.set_cookie("session_id_nojs", value=session_id, max_age=60 * 59,
                                secure=app.config.get("SESSION_COOKIE_SECURE"), httponly=True)

    return response


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_dob"), methods=("GET", "POST"))
@utils.check_session
def details_dob(session_id):
    form = DOBForm(data={
        'day': session.get(DOB_DAY),
        'month': session.get(DOB_MONTH),
        'year': session.get(DOB_YEAR)
    })

    if form.validate_on_submit():
        session[DOB_DAY] = str(form.day.data)
        session[DOB_MONTH] = str(form.month.data)
        session[DOB_YEAR] = str(form.year.data)
        session[DOB] = (
            str(request.form[DAY]) + "/" + str(request.form[MONTH]) + "/" + str(request.form[YEAR])
        )
        session.modified = True
        app.logger.info("redirecting", {'location': "yourdetails.details_auth_option"})
        return redirect(utils.ensure_safe_redirect_url(
            request.args.get('next', routes.get_relative("yourdetails.details_auth_option"))))
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    return render_template(
        "details-dob.html",
        form=form,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_auth_option"), methods=("GET", "POST"))
@utils.check_session
def details_auth_option(session_id):
    form = AuthOption()

    if form.validate_on_submit():
        if form.radio.data == "Yes":
            return redirect_to_route("yourdetails.details_nhs_number")
        return redirect_to_route("yourdetails.details_postcode")
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    return render_template(
        "details-auth-option.html",
        form=form,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_nhs_number"), methods=("GET", "POST"))
@utils.check_session
def details_nhs_number(session_id):
    form = NHSNumberForm(data={
        'nhs_number': session.get(NHS_NUMBER)
    })

    if form.validate_on_submit():
        session[NHS_NUMBER] = form.nhs_number.data
        session[POST_CODE] = ""
        session.modified = True
        app.logger.info("redirecting", {'location': "yourdetails.your_details_review"})
        return redirect(utils.ensure_safe_redirect_url(
            request.args.get('next', routes.get_relative("yourdetails.your_details_review"))))
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    return render_template(
        "details-nhs-number.html",
        form=form,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_postcode"), methods=("GET", "POST"))
@utils.check_session
def details_postcode(session_id):
    form = PostcodeForm(data={
        'postcode': session.get(POST_CODE)
    })

    if form.validate_on_submit():
        session[POST_CODE] = form.postcode.data
        session[NHS_NUMBER] = ""
        session.modified = True
        app.logger.info("redirecting", {'location': "yourdetails.your_details_review"})
        return redirect(utils.ensure_safe_redirect_url(
            request.args.get('next', routes.get_relative("yourdetails.your_details_review"))))
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    return render_template(
        "details-postcode.html",
        form=form,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.your_details_review"), methods=('GET', 'POST'))
@utils.check_session
def your_details_review(session_id):
    form = ReviewForm()
    user_details = UserDetails()

    if not session.get(FIRST_NAME) or not session.get(LAST_NAME):
        return redirect_to_route("yourdetails.your_details")

    if not session.get(DOB_DAY) or not session.get(DOB_MONTH) or not session.get(DOB_YEAR):
        return redirect_to_route("yourdetails.details_dob")

    if not session.get(NHS_NUMBER) and not session.get(POST_CODE):
        return redirect_to_route("yourdetails.details_auth_option")

    if form.validate_on_submit():
        if session[NHS_NUMBER] and not utils.is_nhs_number_valid(session[NHS_NUMBER]):
            if session.get('nhs_number_failed'):
                return redirect_to_route("yourdetails.invalid_nhs_number")
            else:
                session['nhs_number_failed'] = True
                return redirect_to_route("yourdetails.nhs_number_not_accepted")

        result = do_pds_search(user_details, session_id)

        if result == constants.PDS_SEARCH_SUCCESS:
            session.pop('timeout_threshold', None)
            return redirect_to_route("verification.waiting_for_results")
        elif result == constants.PDS_RESULT_INVALID_AGE:
            session.pop('timeout_threshold', None)
            return redirect_to_route("verification.age_restriction_error")
        else:
            app.logger.warning("pds search failure")

        # for PDS_REQUEST_TIMEOUT and other unknown errors
        return redirect_to_route("main.generic_error")
    elif form.errors:
        app.logger.info("submission contains errors")

    return render_template(
        "your-details-review.html",
        form=form,
        details=user_details,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.set_your_preference"), methods=('GET', 'POST'))
@utils.check_session
def set_your_preference(session_id):
    form = ChoiceOption()
    is_timeout = None

    if form.validate_on_submit():
        session['opted_out'] = 'inactive' if form.radio.data == 'Yes' else 'active'
        session['preference'] = 'optedOut' if form.radio.data == 'Yes' else 'optedIn'
        session.pop('timeout_threshold', None)

        user_details = UserDetails()
        result = set_preference(user_details, session_id)

        if result is True:
            return redirect_to_route('yourdetails.review_your_choice')
        return redirect_to_route('yourdetails.set_preference_error')

    else:
        if form.errors:
            flash(form.errors)

    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        is_timeout = constants.PDS_REQUEST_TIMEOUT

    if is_timeout:
        session.pop('timeout_threshold', None)
        return redirect_to_route('yourdetails.set_preference_error')

    if session.get('pds_opted_out') not in ('active', 'inactive', constants.GET_PREFERENCE_EMPTY):
        session['pds_opted_out'] = get_current_preference(session_id)
        if session.get('pds_opted_out') == constants.GET_PREFERENCE_INCOMPLETE:
            return render_template(
                'waiting-for-results.html',
                waiting_message=constants.PDS_SEARCH_WAITING_MESSAGE
            )
        if session.get('pds_opted_out') == constants.GET_PREFERENCE_FAILURE:
            session.pop('timeout_threshold', None)
            return redirect_to_route('yourdetails.set_preference_error')

    if session.get('pds_opted_out') in ('active', 'inactive'):
        form.radio.data = 'Yes' if session.get('pds_opted_out') == 'inactive' else 'No'

    session.pop('timeout_threshold', None)

    return render_template(
        'set-your-preferences.html',
        form=form,
        current_preference=session.get('pds_opted_out'),
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("verification.waiting_for_results"))
@utils.check_session
def waiting_for_results(session_id):
    search_result = None

    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        search_result = constants.PDS_REQUEST_TIMEOUT

    if not search_result:
        search_result = check_status_of_pds_search_result(session_id)

    result_redirects = {
        'success': ("verification.verification_option", False),
        'invalid_user': ("verification.lookup_failure_error", True),
        'insufficient_data': ('verification.contact_details_not_found', False),
        'age_restriction_error': ('verification.age_restriction_error', False),
        constants.PDS_REQUEST_TIMEOUT: ('main.generic_error', False)
    }

    if search_result in result_redirects:
        redirect_controller, clean_state_model = result_redirects[search_result]

        if clean_state_model and not utils.clean_state_model():
            return redirect_to_route('main.generic_error')

        session.pop('timeout_threshold', None)
        return redirect_to_route(redirect_controller)

    return render_template(
        "waiting-for-results.html",
        waiting_message=constants.PDS_SEARCH_WAITING_MESSAGE,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.review_your_choice"), methods=('GET', 'POST',))
@utils.check_session
def review_your_choice(session_id):
    user_details = UserDetails()

    delivery_ret = get_confirmation_delivery_details(session_id)

    if not delivery_ret or delivery_ret.get('method') not in ("sms", "email"):
        return redirect_to_route('main.generic_error')

    if request.method == "POST":
        result = confirm_preference(session_id)

        if result is True:
            return redirect_to_route('yourdetails.store_preference_result')
        return redirect_to_route('main.generic_error')

    return render_template(
        "review-your-choice.html",
        user_details=user_details,
        confirmation_delivery_details=delivery_ret,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.store_preference_result"))
@utils.check_session
def store_preference_result(session_id):
    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        session.pop('timeout_threshold', None)
        return redirect_to_route('main.generic_error')

    result = get_store_preference_result(session_id)

    if result == "success":
        session['is_successfully_stored'] = True
        session.pop('timeout_threshold', None)
        return redirect_to_route('yourdetails.thank_you')

    if result == "failure":
        session.pop('timeout_threshold', None)
        return redirect_to_route('yourdetails.choice_not_saved')

    return render_template(
        "waiting-for-results.html",
        waiting_message=constants.PREF_WAITING_MESSAGE,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.thank_you"))
@utils.check_session_id_if_no_flask_session
def thank_you():
    if not session.get('is_successfully_stored'):
        return redirect_to_route('yourdetails.choice_not_saved')

    user_details = UserDetails()
    session.clear()

    response = make_response(render_template("thank-you.html", user_details=user_details, routes=routes))
    response.set_cookie("session_id_nojs", '', max_age=0)
    return response
