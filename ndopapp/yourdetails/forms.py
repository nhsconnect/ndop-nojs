import re
from datetime import datetime, date
from flask_wtf import FlaskForm as Form
from wtforms import StringField, IntegerField, RadioField
from wtforms.validators import Length, NumberRange
from wtforms.widgets.html5 import NumberInput
from ..main.ndop_validator import PostcodeValidator, NumberLengthValidator

postcode_validator = PostcodeValidator()
number_length_validator = NumberLengthValidator()


class NameForm(Form):
    first_name = StringField("First name", validators=[Length(max=255)])
    last_name = StringField("Last name", validators=[Length(max=255)])
    return_value = True

    def validate(self):
        return_value = Form.validate(self)
        if not return_value:
            return False

        if not self.first_name.data:
            self.first_name.errors.append({
                "id": "firstNameInputLink",
                "message": "Enter your first name",
                "href": "firstNameContainer",
                "error_alert": "Enter your first name"
            })
            return_value = False
        else:
            result = re.match(r"^[a-zA-Z0-9,-.'\s]+$", self.first_name.data)
            if not result:
                self.first_name.errors.append({
                    "id": "firstNameInputLink",
                    "message": "Check your first name",
                    "href": "firstNameContainer",
                    "error_alert": "Check that you've entered your first name correctly"
                })
                return_value = False

        if not self.last_name.data:
            self.last_name.errors.append({
                "id": "lastNameInputLink",
                "message": "Enter your last name",
                "href": "lastNameContainer",
                "error_alert": "Enter your last name"
            })
            return_value = False
        else:
            result = re.match(r"^[a-zA-Z0-9,-.'\s]+$", self.last_name.data)
            if not result:
                self.last_name.errors.append({
                    "id": "lastNameInputLink",
                    "message": "Check your last name",
                    "href": "lastNameContainer",
                    "error_alert": "Check that you've entered your last name correctly"
                })
                return_value = False

        return return_value


class DOBForm(Form):
    day = IntegerField(
        "Day", validators=[NumberRange(min=1, max=31)], widget=NumberInput()
    )
    month = IntegerField(
        "Month", validators=[NumberRange(min=1, max=12)], widget=NumberInput()
    )
    year = IntegerField(
        "Year", validators=[NumberRange(1000, 9999)], widget=NumberInput()
    )

    error_message = None
    valid_fields = {'day': True, 'month': True, 'year': True}

    

    def validate(self):
        # special case where year can take `e` character
        if(self.year._value() and not self.year.data):
            self.year.data = 9999
            self.errors['year'] = 'Error year contains character'

        valid_form = Form.validate(self)

        valid_date = is_valid_date(self.year.data, self.month.data, self.day.data)
        past_date = is_past_date(self.year.data, self.month.data, self.day.data)

        if not valid_form or not valid_date or not past_date:
            self.valid_fields = {'day': not bool(self.errors.get('day')),
                                'month': not bool(self.errors.get('month')),
                                'year': not bool(self.errors.get('year'))}

            
            flashing_message, error_message = self.build_error_messages(self.valid_fields)

            self.error_message = error_message
            new_message = {
                "dob": [
                    {'message': flashing_message, "href": "dateOfBirthDayContainer",
                        "id": "dateOfBirthInputLink", "error_alert": flashing_message}
                ]
            }
            self.errors.update(new_message)

            return False

        self.valid_fields = {'day': True, 'month': True, 'year': True}

        return True


    def build_error_messages(self, valid_fields):

        if(not self.day.data and not self.month.data and not self.year.data):
            return 'Enter your date of birth', 'Enter your date of birth'
        if(not self.day.data and not self.month.data and self.year.data):
            return 'Date of birth must include a day and a month', 'Date of birth must include a day and a month'
        if(not self.day.data and self.month.data and not self.year.data):
            return 'Date of birth must include a day and a year', 'Date of birth must include a day and a year'
        if(self.day.data and not self.month.data and not self.year.data):
            return 'Date of birth must include a month and a year', 'Date of birth must include a month and a year'
        if(not self.day.data and self.month.data and self.year.data):
            return 'Date of birth must include a day', 'Date of birth must include a day'
        if(self.day.data and not self.month.data and self.year.data):
            return 'Date of birth must include a month', 'Date of birth must include a month'
        if(self.day.data and self.month.data and not self.year.data):
            return 'Date of birth must include a year', 'Date of birth must include a year'
        if(all(v for _,v in valid_fields.items())):
            valid_date = is_valid_date(self.year.data, self.month.data, self.day.data)
            past_date = is_past_date(self.year.data, self.month.data, self.day.data)
            if(not valid_date):
                self.valid_fields = {'day': False, 'month': False, 'year': False}
                return 'Check your date of birth', "Check that you've entered your date of birth correctly"
            if(not past_date):
                self.valid_fields = {'day': False, 'month': False, 'year': False}
                return 'Date of birth must be in the past', "Date of birth must be in the past"
        if(not valid_fields.get('day') and valid_fields.get('month') and valid_fields.get('year')):
            return 'Check your date of birth', "Check that you've entered the day you were born correctly"
        if(valid_fields.get('day') and not valid_fields.get('month') and valid_fields.get('year')):
            return 'Check your date of birth', "Check that you've entered the month you were born correctly"
        if(valid_fields.get('day') and valid_fields.get('month') and not valid_fields.get('year')):
            return 'Check your date of birth', "Check that you've entered the year you were born correctly"

        return 'Check your date of birth', "Check that you've entered your date of birth correctly"


def is_valid_date(year, month, day):
    if (not year or not month or not day):
        return False
    try:
        date(year, month, day)
    except ValueError:
        return False
    else:
        return True


def is_past_date(year, month, day):
    if not is_valid_date(year, month, day):
        return False
    return date(year, month, day) < date.today()


class AuthOption(Form):
    radio = RadioField("test", choices=[("Yes", "Yes"), ("No", "No")])

    def validate(self):
        return_value = Form.validate(self)

        if not return_value:
            self.errors.update({
                "nhs_number": [
                    {"message": "Select yes if you know your NHS number",
                     "href": "radioFormLegend", "id": "authOptionErrorLink"}
                ]
            })
            return False

        return True


class NHSNumberForm(Form):
    nhs_number = StringField("nhs_number")
    NHS_NUMBER_LENGTH = 10

    def validate(self):
        return_value = Form.validate(self)
        if not return_value:
            pass

        if not self.nhs_number.data:
            self.nhs_number.errors.append({"message": "Enter your NHS number",
                                           "href": "nhsNumberContainer", "id": "nhsNumberInputLink",
                                           "error_alert": "Enter your NHS number" })
            return False

        if number_length_validator.ni_number_check(self.nhs_number.data):
            self.nhs_number.errors.append({"message": "We think you've entered a National Insurance number. You need to enter your NHS number",
                                           "href": "nhsNumberContainer", "id": "nhsNumberInputLink",
                                           "error_alert": "We think you've entered a National Insurance number. You need to enter your NHS number"})
            return False

        if number_length_validator.number_only(self.nhs_number.data):
            self.nhs_number.errors.append({"message": "Your NHS number should not contain letters",
                                           "href": "nhsNumberContainer", "id": "nhsNumberInputLink",
                                           "error_alert": "Your NHS number should not contain letters"})
            return False

        if len(self.nhs_number.data.replace(' ', '')) < self.NHS_NUMBER_LENGTH:
            self.nhs_number.errors.append({"message": "Your NHS number is too short",
                                           "href": "nhsNumberContainer", "id": "nhsNumberInputLink",
                                           "error_alert": "Your NHS number is too short"})
            return False

        if len(self.nhs_number.data.replace(' ', '')) > self.NHS_NUMBER_LENGTH:
            self.nhs_number.errors.append({"message": "Your NHS number is too long",
                                           "href": "nhsNumberContainer", "id": "nhsNumberInputLink",
                                           "error_alert": "Your NHS number is too long"})
            return False

        return True


class PostcodeForm(Form):
    postcode = StringField("postcode")

    def validate(self):
        return_value = Form.validate(self)
        if not return_value:
            pass

        if not self.postcode.data:
            self.postcode.errors.append({"message": "Enter your postcode", "id": "postcodeInputLink",
                                         "href": "postcodeContainer",
                                         "error_alert": "Enter your postcode"})
            return False

        if postcode_validator.normalise_postcode(self.postcode.data) is None:
            self.postcode.errors.append({"message": "Check your postcode",
                                         "id": "postcodeInputLink", "href": "postcodeContainer",
                                         "error_alert": "Check that you've entered your postcode correctly"})
            return False

        return True


class ReviewForm(Form):
    pass


class ChoiceOption(Form):
    radio = RadioField("test", choices=[("Yes", "Yes"), ("No", "No")])

    def validate(self):
        return_value = Form.validate(self)

        if not return_value:
            self.errors.update({
                "preference": [
                    {"message": "Select your choice", "href": "preference",
                     "id": "setPreferencesInputLink" }
                ]
            })
            return False

        return True
