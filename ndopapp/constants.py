UNKNOWN_RESULT = 'unknown'

#pdssearch responses
PDS_SEARCH_SUCCESS = "success"
PDS_REQUEST_TIMEOUT = "pds_request_timeout"
PDS_RESULT_INVALID_AGE = "invalid_age"

# function return statuses as constants
CORRECT_OTP = "success"
INCORRECT_OTP = "failure"
CORRECT_OTP_EXPIRED = "expired"
INCORRECT_OTP_MAX_RETRIES = "failure_max"

# resendcode responses
RESEND_CODE_SUCCESS = "success"
RESEND_CODE_MAX_REACHED = "max_count_reached"
RESEND_CODE_MAX_EXCEEDED = "max_count_exceeded"

# requestcode responses
OTP_REQUEST_SUCCESS = "success"
OTP_REQUEST_FAILURE = "failure"
OTP_REQUEST_MAX_RETRIES = "max_count_exceeded"

# waiting messages
PREF_WAITING_MESSAGE = "Saving your choice"
PDS_SEARCH_WAITING_MESSAGE = "Finding your details"

# get preference messages
GET_PREFERENCE_SUCCESS = "success"
GET_PREFERENCE_EMPTY = "preference_empty"
GET_PREFERENCE_FAILURE = "preference_failure"
GET_PREFERENCE_INCOMPLETE = "incomplete"

# timestamp constants
FAR_IN_THE_FUTURE = 10**30
