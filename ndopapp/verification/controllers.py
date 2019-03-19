from flask import Blueprint, flash, render_template, redirect, session, current_app as app
from ..yourdetails.models import UserDetails
from .forms import VerificationOption, CodeForm
from .models import is_otp_verified_by_pds, resend_code_by_pds, request_code_by_pds
from ndopapp import routes, constants, utils
import json

verification_blueprint = Blueprint(
    "verification", __name__, template_folder="../templates/verification"
)


@verification_blueprint.route(routes.get_raw("verification.verification_option"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def verificationoption(session_id):
    app.logger.info("starting controller", {'controller': "verification.verification_option"})
    user_details = UserDetails()
    form = VerificationOption(user_details=user_details)

    if form.validate_on_submit():
        if form.radio.data in ('Email', 'SMS'):

            # below 2 lines can be removed when session cleaning
            # will be implemented
            session['is_resent'] = False
            session['is_resent_max_reached'] = False

            request_code_ret = request_code_by_pds(session_id, otp_delivery_type=str(form.radio.data).lower())
            if request_code_ret == constants.OTP_REQUEST_SUCCESS:
                app.logger.info("redirecting", {'location': "verification.enter_your_code"})
                return redirect(routes.get_absolute('verification.enter_your_code'))
            elif request_code_ret == constants.OTP_REQUEST_MAX_RETRIES:
                # it is reached when we already exceeded /resend_code limit and
                # we try to use /requestcode afterwards. Then API returns
                # 'max_count_exceeded' the content of the response
                app.logger.warning("max retries reached")
                app.logger.info("redirecting", {'location': "verification.resend_code_error"})
                return redirect(routes.get_absolute('verification.resend_code_error'))

        elif form.radio.data == 'Unrecognised':
            app.logger.info("redirecting", {'location': "verification.enter_your_code"})
            return redirect(routes.get_absolute('verification.contact_details_not_recognised'))
    elif form.errors:
        app.logger.info("submission contains errors", {'errors': json.dumps(form.errors)})

    app.logger.info('rendering page', {'page': 'verificationoption'})
    return render_template(
        'verificationoption.html',
        user_details=user_details,
        form=form,
        routes=routes
    )


@verification_blueprint.route(routes.get_raw("verification.enter_your_code"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def enteryourcode(session_id):
    app.logger.info("starting controller", {'controller': "verification.enter_your_code"})
    form = CodeForm()
    is_reenter_code = False

    def generate_template(form_local, sess, is_reenter):
        return {
            'template_name_or_list': 'enteryourcode.html',
            'form': form_local,
            'is_resent': sess.get('is_resent'),  # set in /resendcode
            'is_resent_max_reached': sess.get('is_resent_max_reached'),
            'is_reenter_code': is_reenter,
            'routes': routes,
        }

    if not form.validate_on_submit() or not form.validate():
        if form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

        app.logger.info('rendering page', {'page': 'enteryourcode'})
        return render_template(**generate_template(form, session, is_reenter_code))

    verification_result = is_otp_verified_by_pds(session_id, form.enterOtpInput.data)

    if verification_result == constants.CORRECT_OTP:
        app.logger.info("redirecting", {'location': "yourdetails.set_your_preference"})
        return redirect(routes.get_absolute('yourdetails.set_your_preference'))

    if verification_result == constants.INCORRECT_OTP_MAX_RETRIES:
        app.logger.info("max otp retries reached")
        app.logger.info("redirecting", {'location': "verification.incorrect_code_error"})
        return redirect(routes.get_absolute('verification.incorrect_code_error'))

    if verification_result == constants.INCORRECT_OTP:
        app.logger.info("incorrect otp")
        form.add_incorrect_otp_error()
        is_reenter_code = True
        flash(form.errors)
        return render_template(**generate_template(form, session, is_reenter_code))

    if verification_result == constants.CORRECT_OTP_EXPIRED:
        return redirect(routes.get_absolute('verification.expired_code_error'))

    return redirect(routes.get_absolute('yourdetails.generic_error'))


@verification_blueprint.route(routes.get_raw("verification.resend_code"))
@utils.check_session
@utils.catch_unhandled_exceptions
def resend_code(session_id):
    app.logger.info("starting controller", {'controller': "verification.resend_code"})

    result = resend_code_by_pds(session_id)

    if result == constants.RESEND_CODE_MAX_EXCEEDED:
        return redirect(routes.get_absolute('verification.resend_code_error'))

    if result == constants.RESEND_CODE_SUCCESS:
        session['is_resent'] = True
        session['is_resent_max_reached'] = False
    elif result == constants.RESEND_CODE_MAX_REACHED:
        session['is_resent'] = True
        session['is_resent_max_reached'] = True

    return redirect(routes.get_absolute('verification.enter_your_code'))


@verification_blueprint.route(routes.get_raw("verification.resend_code_error"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def resend_code_error(session_id):
    app.logger.info("starting controller", {'controller': "verification.resend_code_error"})
    app.logger.info('rendering page', {'page': 'resendcodeerror'})
    return render_template('resendcodeerror.html', routes=routes)


@verification_blueprint.route(routes.get_raw("verification.contact_details_not_recognised"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def contactdetailsnotrecognised(session_id):
    app.logger.info("starting controller", {'controller': "verification.contact_details_not_recognised"})
    if not utils.clean_state_model():
        return redirect(routes.get_absolute('yourdetails.generic_error'))

    app.logger.info('rendering page', {'page': 'contactdetailsnotrecognised'})
    return render_template('contactdetailsnotrecognised.html', routes=routes)


@verification_blueprint.route(routes.get_raw("verification.lookup_failure_error"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def lookupfailureerror(session_id):
    app.logger.info("starting controller", {'controller': "verification.lookup_failure_error"})

    user_details = UserDetails()

    if not utils.clean_state_model():
        return redirect(routes.get_absolute('yourdetails.generic_error'))

    if user_details.postcode:
        template = 'lookupfailureerrorpostcode.html'
        app.logger.info('rendering page', {'page': 'lookupfailureerrorpostcode'})
    else:
        template = 'lookupfailureerror.html'
        app.logger.info('rendering page', {'page': 'lookupfailureerror'})

    return render_template(template, routes=routes)


@verification_blueprint.route(routes.get_raw("verification.contact_details_not_found"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def contactdetailsnotfound(session_id):
    app.logger.info("starting controller", {'controller': "verification.contact_details_not_found"})
    app.logger.info('rendering page', {'page': 'contactdetailsnotfound'})
    return render_template('contactdetailsnotfound.html', routes=routes)


@verification_blueprint.route(routes.get_raw("verification.age_restriction_error"), methods=('GET', 'POST'))
@utils.check_session
@utils.catch_unhandled_exceptions
def agerestrictionerror(_):
    app.logger.info('rendering page', {'page': 'age_restriction_error'})
    return render_template("age-restriction-error.html", routes=routes)


@verification_blueprint.route(routes.get_raw("verification.incorrect_code_error"), methods=('GET', 'POST'))
@utils.check_session
def incorrectcodeerror(session_id):
    app.logger.info("starting controller", {'controller': "verification.incorrect_code_error"})
    app.logger.info('rendering page', {'page': 'incorrectcodeerror'})
    return render_template('incorrectcodeerror.html', routes=routes)


@verification_blueprint.route(routes.get_raw("verification.expired_code_error"), methods=['GET', 'POST'])
@utils.check_session
def expiredcodeerror(session_id):
    app.logger.info('rendering page', {'page': 'expiredcodeerror'})
    return render_template('expiredcodeerror.html', routes=routes)
