MAX_COUNT = 2
count = MAX_COUNT

RESULT_MAX_COUNT = 2
result_count = RESULT_MAX_COUNT

PREFERENCES_MAX_COUNT = 2
preferences_count = PREFERENCES_MAX_COUNT

RESEND_OTP_COUNTER_NAME = 'resend_otp_count'
VERIFY_OTP_COUNTER_NAME = 'verify_otp_count'

MAX_COUNTS = {
    RESEND_OTP_COUNTER_NAME: 4,
    VERIFY_OTP_COUNTER_NAME: 3
}
session_counters_store = {}


class CounterIncreasingResponse():
    MAX_NOT_REACHED = "max_not_reached"
    MAX_REACHED = "max_reached"
    MAX_EXCEEDED = "max_exceeded"


def check_and_decrement():
    global count
    if count > 0:
        count -= 1
        return False
    else:
        count = MAX_COUNT
        return True


def result_check_and_decrement():
    global result_count
    if result_count > 0:
        result_count -= 1
        return False
    else:
        result_count = RESULT_MAX_COUNT
        return True

def preferences_check_and_decrement():
    global preference_count
    if preference_count > 0:
        preference_count -= 1
        return False
    else:
        preference_count = PREFERENCE_MAX_COUNT
        return True

def code_check_and_decrement():
    global code_count
    if code_count > 0:
        code_count -= 1
        return False
    else:
        code_count = CODE_MAX_COUNT
        return True


def preferences_check_and_decrement():
    global preferences_count
    if preferences_count > 0:
        preferences_count -= 1
        return False
    else:
        preferences_count = PREFERENCES_MAX_COUNT
        return True


def increase_counter_for(session_id, counter_name):
    """
    returns:
        "max_not_reached" if counter less than the maximum,
        "max_reached" if counter equals to maximum
        "max_exceeded" if counter is greater than the maximum
    """
    session_counters = session_counters_store.get(session_id)
    if not session_counters:
        session_counters_store[session_id] = {counter_name: 1}
        return CounterIncreasingResponse.MAX_NOT_REACHED

    counter = session_counters.get(counter_name)
    if not counter:
        session_counters[counter_name] = 1
        return CounterIncreasingResponse.MAX_NOT_REACHED

    counter += 1
    session_counters[counter_name] = counter
    if counter < MAX_COUNTS.get(counter_name):
        return CounterIncreasingResponse.MAX_NOT_REACHED

    if counter == MAX_COUNTS.get(counter_name):
        return CounterIncreasingResponse.MAX_REACHED

    return CounterIncreasingResponse.MAX_EXCEEDED
