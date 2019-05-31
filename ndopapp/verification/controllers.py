from flask import Blueprint, flash, render_template, session, current_app as app
from .forms import VerificationOption, CodeForm
from .models import is_otp_verified_by_pds, resend_code_by_pds, request_code_by_pds
from ndopapp import routes, constants, utils
from ndopapp.utils import TemplateView
from ndopapp.routes import redirect_to_route
from ndopapp.yourdetails.models import UserDetails
import json


verification_blueprint = Blueprint(
    "verification", __name__, template_folder="../templates/verification"
)

verification_blueprint.add_url_rule(
    routes.get_raw("verification.resend_code_error"),
    view_func=TemplateView.as_view(
        'resend_code_error',
        'resend-code-error.html'
    )
)

verification_blueprint.add_url_rule(
    routes.get_raw("verification.contact_details_not_found"),
    view_func=TemplateView.as_view(
        'contact_details_not_found',
        'contact-details-not-found.html'
    )
)

verification_blueprint.add_url_rule(
    routes.get_raw("verification.age_restriction_error"),
    view_func=TemplateView.as_view(
        'age_restriction_error',
        'age-restriction-error.html'
    )
)

verification_blueprint.add_url_rule(
    routes.get_raw("verification.incorrect_code_error"),
    view_func=TemplateView.as_view(
        'incorrect_code_error',
        'incorrect-code-error.html'
    )
)


verification_blueprint.add_url_rule(
    routes.get_raw("verification.expired_code_error"),
    view_func=TemplateView.as_view(
        'expired_code_error',
        'expired-code-error.html'
    )
)


@verification_blueprint.route(routes.get_raw("verification.verification_option"), methods=('GET', 'POST'))
@utils.check_session
def verification_option(session_id):
    user_details = UserDetails()
    form = VerificationOption(user_details=user_details)

    if form.validate_on_submit():
        # below 2 lines can be removed when session cleaning
        # will be implemented
        session['is_resent'] = False
        session['is_resent_max_reached'] = False

        request_code_ret = request_code_by_pds(session_id, otp_delivery_type=str(form.radio.data).lower())
        if request_code_ret == constants.OTP_REQUEST_SUCCESS:
            session['selected_option'] = form.radio.data
            return redirect_to_route('verification.enter_your_code')
        elif request_code_ret == constants.OTP_REQUEST_MAX_RETRIES:
            # it is reached when we already exceeded /resend_code limit and
            # we try to use /requestcode afterwards. Then API returns
            # 'max_count_exceeded' the content of the response
            app.logger.warning("max retries reached")
            return redirect_to_route('verification.resend_code_error')

    elif form.errors:
        app.logger.info("submission contains errors", {'errors': json.dumps(form.errors)})

    return render_template(
        'verification-option.html',
        user_details=user_details,
        form=form,
        routes=routes
    )


@verification_blueprint.route(routes.get_raw("verification.enter_your_code"), methods=('GET', 'POST'))
@utils.check_session
def enter_your_code(session_id):
    form = CodeForm()
    is_reenter_code = False

    def get_text_of_selected_option(sess):
        selected_option = sess.get('selected_option')
        user_details = UserDetails()
        if selected_option == 'SMS':
            return f'text to {user_details.sms}'
        elif selected_option == 'Email':
            return f'email to {user_details.email}'
        else:
            #we shouldn't be here
            app.logger.error("unknown option selected")
            return ''


    def generate_template(form_local, sess, is_reenter):
        return {
            'template_name_or_list': 'enter-your-code.html',
            'form': form_local,
            'is_resent': sess.get('is_resent'),  # set in /resendcode
            'is_resent_max_reached': sess.get('is_resent_max_reached'),
            'selected_option': get_text_of_selected_option(sess),  # set in /verification_option
            'is_reenter_code': is_reenter,
            'routes': routes,
        }

    if not form.validate_on_submit() or not form.validate():
        if form.errors:
            app.logger.info("submission contains errors")
            flash(form.errors)

        return render_template(**generate_template(form, session, is_reenter_code))

    verification_result = is_otp_verified_by_pds(session_id, form.enterOtpInput.data)

    if verification_result == constants.CORRECT_OTP:
        return redirect_to_route('yourdetails.set_your_preference')

    if verification_result == constants.INCORRECT_OTP_MAX_RETRIES:
        app.logger.info("max otp retries reached")
        return redirect_to_route('verification.incorrect_code_error')

    if verification_result == constants.INCORRECT_OTP:
        app.logger.info("incorrect otp")
        form.add_incorrect_otp_error()
        is_reenter_code = True
        flash(form.errors)
        return render_template(**generate_template(form, session, is_reenter_code))

    if verification_result == constants.CORRECT_OTP_EXPIRED:
        return redirect_to_route('verification.expired_code_error')

    return redirect_to_route('main.generic_error')


@verification_blueprint.route(routes.get_raw("verification.resend_code"), methods=("POST",))
@utils.check_session
def resend_code(session_id):
    result = resend_code_by_pds(session_id)

    if result == constants.RESEND_CODE_MAX_EXCEEDED:
        return redirect_to_route('verification.resend_code_error')

    if result == constants.RESEND_CODE_SUCCESS:
        session['is_resent'] = True
        session['is_resent_max_reached'] = False
    elif result == constants.RESEND_CODE_MAX_REACHED:
        session['is_resent'] = True
        session['is_resent_max_reached'] = True

    return redirect_to_route('verification.enter_your_code')


@verification_blueprint.route(routes.get_raw("verification.contact_details_not_recognised"))
@utils.check_session
def contactdetailsnotrecognised(session_id):

    app.logger.info("starting controller", {'controller': "verification.contact_details_not_recognised"})
    if not utils.clean_state_model():
        return redirect_to_route('main.generic_error')

    app.logger.info('rendering page', {'page': 'contactdetailsnotrecognised'})
    return render_template('contact-details-not-recognised.html', routes=routes)


@verification_blueprint.route(routes.get_raw("verification.lookup_failure_error"))
@utils.check_session
def lookup_failure_error(session_id):
    user_details = UserDetails()

    if user_details.postcode:
        template = 'lookup-failure-error-postcode.html'
    else:
        template = 'lookup-failure-error.html'

    return render_template(template, routes=routes)
