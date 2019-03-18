import json, os, datetime
from flask import make_response, current_app


class User:
    DATA_PATH = "../../data/"

    def __init__(self, user_json):
        users = self.load_users_from_file()

        current_app.logger.info("Making a user")

        self.firstname = ''
        self.lastname = ''
        self.communication_type = ''


        # find specific user with specific equality rules
        for user in users:
            if user["firstname"].lower() == user_json.get("firstName").lower() \
                    and user["lastname"].lower() == user_json.get("lastName").lower() \
                    and (user["nhsnumber"] == user_json.get("nhsNumber") or user["postcode"] == user_json.get("postcode")):

                self.firstname = user.get("firstname")
                self.lastname = user.get("lastname")
                self.nhsnumber = user.get("nhsnumber")
                self.postcode = user.get("postcode")
                self.email = user.get("email")
                self.sms = user.get("sms")
                self.opted_out = user.get("opted_out")
                self.preference = user.get("preference")
                self.dob = datetime.date(int(user.get("dobyear")), int(user.get("dobmonth")), int(user.get("dobday")))
                return


    def load_users_from_file(self):
        with open(
                os.path.abspath(os.path.join(__file__, self.DATA_PATH, "users.json"))
        ) as f:
            users = json.load(f)
        return users

    def generate_pds_search_response(self):

        if not self.firstname:
            current_app.logger.info("User does not exist")
            return make_response('{"search_result": "incomplete"}', 401)

        if self.dob > datetime.date(2006, 2, 19):
            return make_response(json.dumps({"error": "age_verification_failed"}), 406)

        if self.sms and self.email:
            current_app.logger.info("User has email and mobile")
            return make_response(f'{{"search_result": "success", "sms": "{self.sms}", "email": "{self.email}"}}')

        if self.email:
            current_app.logger.info("User has no email but does have mobile")
            return make_response(f'{{"search_result": "success", "email": "{self.email}"}}')

        if self.sms:
            current_app.logger.info("User has no mobile but does have email")
            return make_response(f'{{"search_result": "success", "sms": "{self.sms}"}}')

        current_app.logger.info("User has neither email nor mobile")
        return make_response('{"search_result": "ndop_info"}', 422)
