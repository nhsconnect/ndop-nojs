import difflib
from ndopapp.models import NDOP_Error
prefix = ''
host = ''


def get_raw(controller_name):
    routes = {
        "main.root": "",
        "main.landing_page": "landingpage",


        "yourdetails.your_details": "yourdetails",
        "yourdetails.details_dob": "detailsdob",
        "yourdetails.details_auth_option": "detailsauthoption",
        "yourdetails.details_nhs_number": "detailsnhsnumber",
        "yourdetails.details_postcode": "detailspostcode",
        "yourdetails.your_details_review": "yourdetailsreview",
        "yourdetails.generic_error": "genericerror",
        "yourdetails.set_your_preference": "setyourpreference",
        "yourdetails.submit_preference": "submitpreference",
        "yourdetails.review_your_choice": "reviewyourchoice",
        "yourdetails.store_preference_result": "storepreferenceresult",
        "yourdetails.confirmation_sender": "confirmationsender",
        "yourdetails.thank_you": "thankyou",
        "yourdetails.choice_not_saved": "choicenotsaved",

        "verification.enter_your_code": "enteryourcode",
        "verification.contact_details_not_recognised": "contactdetailsnotrecognised",
        "verification.contact_details_not_found": "contactdetailsnotfound",
        "verification.incorrect_code_error": "incorrectcodeerror",
        "verification.expired_code_error": "expiredcodeerror",
        "verification.waiting_for_results": "waitingforresults",
        "verification.resend_code_error": "resendcodeerror",
        "verification.age_restriction_error": "agerestrictionerror",
        "verification.resend_code": "resendcode",
        "verification.verification_option": "verificationoption",
        "verification.lookup_failure_error": "lookupfailureerror",
    }
    try:
        return '/' + routes[controller_name]
    except KeyError:
        maybe = difflib.get_close_matches(controller_name, routes)
        raise NDOP_Error(f"Invalid route {controller_name}, did you mean {maybe}?")


def get_relative(controller_name):
    return prefix + get_raw(controller_name)


def get_absolute(controller_name):
    return make_absolute(get_relative(controller_name))


def make_absolute(path):
    return host.strip('/') + path
