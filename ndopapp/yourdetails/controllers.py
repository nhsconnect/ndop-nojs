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

from .models import (
    UserDetails,
    get_session_id,
    do_pds_search,
    check_status_of_pds_search_result,
    get_current_preference,
    get_confirmation_delivery_details,
    store_preference,
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


@yourdetails_blueprint.route(routes.get_raw("yourdetails.your_details"), methods=("GET", "POST"))
@utils.catch_unhandled_exceptions
def your_details():
    app.logger.info("starting controller", {'controller': "yourdetails.your_details"})
    form = NameForm()

    if FIRST_NAME in session and LAST_NAME in session:
        form.first_name.data = session[FIRST_NAME]
        form.last_name.data = session[LAST_NAME]

    if form.is_submitted():
        form.first_name.data = request.form[FIRST_NAME]
        form.last_name.data = request.form[LAST_NAME]
        session[FIRST_NAME] = form.first_name.data
        session[LAST_NAME] = form.last_name.data
        if form.validate():
            session.modified = True
            app.logger.info("redirecting", {'location': routes.get_raw("yourdetails.details_dob")})
            redirect_url = utils.ensure_safe_redirect_url(
                request.args.get('next', routes.get_relative("yourdetails.details_dob")))
            return redirect(redirect_url)
        elif form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

    #if still not 'session' cookie at this point we assume cookies are
    #disabled on user's web browser
    if not request.cookies.get('session'):
        app.logger.info('rendering page', {'page': 'cookies-disabled.html'})
        return make_response(render_template('cookies-disabled.html'), 400)

    response = make_response(render_template("your-details.html", form=form, routes=routes))

    # get session id
    if not request.cookies.get("session_id_nojs"):
        session_id = get_session_id()
        g.session_id_override = session_id
        if session_id:
            # set session_id cookie to expire after 59 minutes
            response.set_cookie("session_id_nojs", value=session_id, max_age=60 * 59,
                                secure=True, httponly=True)

    app.logger.info('rendering page', {'page': 'your_details_name'})
    return response


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_dob"), methods=("GET", "POST"))
@utils.check_session
@utils.catch_unhandled_exceptions
def details_dob(session_id):
    app.logger.info("starting controller", {'controller': "yourdetails.details_dob"})
    form = DOBForm()

    if DOB in session:
        form.day.data = int(session[DOB_DAY])
        form.month.data = int(session[DOB_MONTH])
        form.year.data = int(session[DOB_YEAR])

    if form.is_submitted():
        form.day.data = int(request.form[DAY] if request.form[DAY] else '0')
        form.month.data = int(request.form[MONTH] if request.form[MONTH] else '0')
        form.year.data = int(request.form[YEAR] if request.form[YEAR] else '0')
        session[DOB_DAY] = str(form.day.data)
        session[DOB_MONTH] = str(form.month.data)
        session[DOB_YEAR] = str(form.year.data)
        if form.validate():
            session.modified = True
            session[DOB] = (
                    str(request.form[DAY]) + "/" + str(request.form[MONTH]) + "/" + str(request.form[YEAR])
            )
            app.logger.info("redirecting", {'location': "yourdetails.details_auth_option"})
            return redirect(utils.ensure_safe_redirect_url(
                request.args.get('next', routes.get_relative("yourdetails.details_auth_option"))))
        elif form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

    app.logger.info('rendering page', {'page': 'your_details_dob'})
    return render_template("details-dob.html", form=form, routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_auth_option"), methods=("GET", "POST"))
@utils.check_session
@utils.catch_unhandled_exceptions
def details_auth_option(session_id):
    app.logger.info("starting controller", {'controller': "yourdetails.details_auth_option"})
    form = AuthOption()

    if form.validate_on_submit() and form.validate():
        if form.radio.data == "Yes":
            app.logger.info("redirecting", {'location': "yourdetails.details_nhs_number"})
            return redirect(routes.get_absolute("yourdetails.details_nhs_number"))

        app.logger.info("redirecting", {'location': "yourdetails.details_postcode"})
        return redirect(routes.get_absolute("yourdetails.details_postcode"))
    elif form.errors:
        app.logger.info("submission contains errors")
        flash(form.errors)

    app.logger.info('rendering page', {'page': 'your_details_route_selector'})
    return render_template("details-auth-option.html", form=form, routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_nhs_number"), methods=("GET", "POST"))
@utils.check_session
@utils.catch_unhandled_exceptions
def details_nhs_number(session_id):
    app.logger.info("starting controller", {'controller': "yourdetails.details_nhs_number"})
    form = NHSNumberForm()

    if NHS_NUMBER in session:
        form.nhs_number.data = session[NHS_NUMBER]

    if form.is_submitted():
        form.nhs_number.data = request.form[NHS_NUMBER]
        session[NHS_NUMBER] = form.nhs_number.data
        session[POST_CODE] = ""

        if form.validate():
            session.modified = True
            app.logger.info("redirecting", {'location': "yourdetails.your_details_review"})
            return redirect(utils.ensure_safe_redirect_url(
                request.args.get('next', routes.get_relative("yourdetails.your_details_review"))))
        elif form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

    app.logger.info('rendering page', {'page': 'your_details_nhs_number'})
    return render_template("details-nhs-number.html", form=form, routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.details_postcode"), methods=("GET", "POST"))
@utils.check_session
@utils.catch_unhandled_exceptions
def details_postcode(session_id):
    app.logger.info("starting controller", {'controller': "yourdetails.details_postcode"})
    form = PostcodeForm()

    if POST_CODE in session:
        form.postcode.data = session[POST_CODE]

    if form.is_submitted():
        form.postcode.data = request.form[POST_CODE]
        session[POST_CODE] = form.postcode.data
        session[NHS_NUMBER] = ""

        if form.validate():
            session.modified = True
            app.logger.info("redirecting", {'location': "yourdetails.your_details_review"})
            return redirect(utils.ensure_safe_redirect_url(
                request.args.get('next', routes.get_relative("yourdetails.your_details_review"))))
        elif form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

    app.logger.info('rendering page', {'page': 'your_details_postcode'})
    return render_template("details-postcode.html", form=form, routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.your_details_review"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def your_details_review(session_id):
    app.logger.info("starting controller", {'controller': "yourdetails.your_details_review"})
    form = ReviewForm()
    user_details = UserDetails()

    if form.validate_on_submit():
        result = do_pds_search(user_details, session_id)

        if result == constants.PDS_SEARCH_SUCCESS:
            app.logger.info("redirecting", {'location': "verification.waiting_for_results"})
            session.pop('timeout_threshold', None)
            return redirect(routes.get_absolute("verification.waiting_for_results"))
        elif result == constants.PDS_RESULT_INVALID_AGE:
            app.logger.info("redirecting", {'location': "verification.age_restriction_error"})
            session.pop('timeout_threshold', None)
            return redirect(routes.get_absolute("verification.age_restriction_error"))
        else:
            app.logger.warning("pds search failure")

        # for PDS_REQUEST_TIMEOUT and other unknown errors
        return redirect(routes.get_absolute("yourdetails.generic_error"))
    elif form.errors:
        app.logger.info("submission contains errors")

    app.logger.info('rendering page', {'page': 'your_details_review'})
    return render_template(
        "your-details-review.html",
        form=form,
        details=user_details,
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("yourdetails.set_your_preference"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def set_your_preference(session_id):
    form = ChoiceOption()
    is_timeout = None

    if form.validate_on_submit() and form.validate():

        if form.radio.data == 'Yes':
            session['opted_out'] = 'inactive'
            session['preference'] = 'optedOut'

        if form.radio.data == 'No':
            session['opted_out'] = 'active'
            session['preference'] = 'optedIn'

        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute('yourdetails.submit_preference'))

    else:
        if form.errors:
            flash(form.errors)

    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        is_timeout = constants.PDS_REQUEST_TIMEOUT

    if is_timeout:
        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute('yourdetails.generic_error'))

    if session.get('pds_opted_out') not in ('active', 'inactive', constants.GET_PREFERENCE_EMPTY):
        session['pds_opted_out'] = get_current_preference(session_id)
        if session.get('pds_opted_out') == constants.GET_PREFERENCE_INCOMPLETE:
            return render_template(
                'waiting-for-results.html',
                waiting_message=constants.PDS_SEARCH_WAITING_MESSAGE
            )
        if session.get('pds_opted_out') == constants.GET_PREFERENCE_FAILURE:
            session.pop('timeout_threshold', None)
            return redirect(routes.get_absolute('yourdetails.generic_error'))

    if session.get('pds_opted_out') in ('active', 'inactive'):
        form.radio.data = 'Yes' if session.get('pds_opted_out') == 'inactive' else 'No'

    session.pop('timeout_threshold', None)

    app.logger.info('rendering page', {'page': 'setyourpreferences'})
    return render_template(
        'setyourpreferences.html',
        form=form,
        current_preference=session.get('pds_opted_out'),
        routes=routes
    )


@yourdetails_blueprint.route(routes.get_raw("verification.waiting_for_results"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def waiting_for_results(session_id):
    app.logger.info("starting controller", {'controller': "verification.waiting_for_results"})

    search_result = None

    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        search_result = constants.PDS_REQUEST_TIMEOUT

    if not search_result:
        search_result = check_status_of_pds_search_result(session_id)

    result_redirects = {
        'success': "verification.verification_option",
        'invalid_user': "verification.lookup_failure_error",
        'insufficient_data': 'verification.contact_details_not_found',
        'age_restriction_error': 'verification.age_restriction_error',
        constants.PDS_REQUEST_TIMEOUT: 'yourdetails.generic_error'
    }
    redirect_controller = result_redirects.get(search_result)
    if redirect_controller:
        app.logger.info("redirecting", {'location': routes.get_absolute(redirect_controller)})
        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute(redirect_controller))

    app.logger.info('rendering page', {'page': 'waiting_for_pds_results'})
    return render_template("waiting-for-results.html",
                           waiting_message=constants.PDS_SEARCH_WAITING_MESSAGE,
                           routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.review_your_choice"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def review_your_choice(session_id):
    user_details = UserDetails()

    delivery_ret = get_confirmation_delivery_details(session_id)

    if delivery_ret and delivery_ret.get('method') in ("sms", "email"):
        app.logger.info('rendering page', {'page': 'review_your_choice'})
        return render_template("reviewyourchoice.html",
                               user_details=user_details,
                               confirmation_delivery_details=delivery_ret,
                               routes=routes)

    return redirect(routes.get_absolute('yourdetails.generic_error'))


@yourdetails_blueprint.route(routes.get_raw("yourdetails.submit_preference"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def submit_preference(session_id):
    user_details = UserDetails()
    result = set_preference(user_details, session_id)

    if result is True:
        return redirect(routes.get_absolute('yourdetails.review_your_choice'))

    return redirect(routes.get_absolute('yourdetails.generic_error'))


@yourdetails_blueprint.route(routes.get_raw("yourdetails.confirmation_sender"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def confirmation_sender(session_id):
    result = confirm_preference(session_id)

    if result is True:
        return redirect(routes.get_absolute('yourdetails.store_preference_result'))

    return redirect(routes.get_absolute('yourdetails.generic_error'))


@yourdetails_blueprint.route(routes.get_raw("yourdetails.store_preference_result"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def store_preference_result(session_id):
    if not session.get('timeout_threshold'):
        session['timeout_threshold'] = int(time.time()) + int(app.config["PDS_REQUEST_TIMEOUT"])
    elif int(session.get('timeout_threshold')) <= int(time.time()):
        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute('yourdetails.generic_error'))

    result = store_preference(session_id)

    if result == "success":
        session['is_successfully_stored'] = True
        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute('yourdetails.thank_you'))

    if result == "failure":
        session.pop('timeout_threshold', None)
        return redirect(routes.get_absolute('yourdetails.choice_not_saved'))

    app.logger.info('rendering page', {'page': 'waiting_for_store_preference_results'})
    return render_template("waiting-for-results.html",
                           waiting_message=constants.PREF_WAITING_MESSAGE,
                           routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.thank_you"), methods=('GET', 'POST'))
@utils.check_session_id_if_no_flask_session
@utils.catch_unhandled_exceptions
def thank_you():
    if not session.get('is_successfully_stored'):
        return redirect(routes.get_absolute('yourdetails.choice_not_saved'))

    user_details = UserDetails()
    session.clear()
    app.logger.info('rendering page', {'page': 'thank_you'})
    response = make_response(render_template("thank-you.html", user_details=user_details, routes=routes))
    response.set_cookie("session_id_nojs", '', max_age=0)
    return response


@yourdetails_blueprint.route(routes.get_raw("yourdetails.generic_error"), methods=('GET', 'POST'))
def genericerror():
    app.logger.info('rendering page', {'page': 'generic_error'})
    return render_template('error.html', routes=routes)


@yourdetails_blueprint.route(routes.get_raw("yourdetails.choice_not_saved"), methods=('GET', 'POST'))
@utils.catch_unhandled_exceptions
def choice_not_saved():
    return render_template('choice-not-saved.html', routes=routes)
