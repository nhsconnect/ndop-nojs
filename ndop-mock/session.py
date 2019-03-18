import pickle, functools, os
from flask import current_app

data_file = "sessions.pickle"


def pickle_store(func):
    @functools.wraps(func)
    def pickle_wrapper(*args):
        if not os.path.isfile(data_file):
            file = open("sessions.pickle", "wb")
            file.close()
        if os.path.getsize(data_file) > 0:
            pickle_in = open("sessions.pickle", "rb")
            sessions = pickle.load(pickle_in)
        else:
            sessions = {}
        act = func(sessions, *args)

        pickle_out = open("sessions.pickle", "wb")
        pickle.dump(sessions, pickle_out)
        pickle_out.close()
        return act

    return pickle_wrapper


@pickle_store
def add_session(sessions, session):
    current_app.logger.info(f"Adding new session {session}")
    sessions[f'session_id={session}'] = ""


@pickle_store
def add_user_to_session(sessions, session, user):
    current_app.logger.info(
        f"Adding user {user.firstname} {user.lastname} to session {session}"
    )
    sessions[session] = user


@pickle_store
def remove_session(sessions, session):
    del sessions[session]


@pickle_store
def get_user_from_session(sessions, session_id):
    current_app.logger.info(
        f"Getting user {sessions[session_id].firstname} {sessions[session_id].lastname} from session {session_id}"
    )
    return sessions[session_id]


@pickle_store
def get_sessions(sessions):
    return sessions.keys()
