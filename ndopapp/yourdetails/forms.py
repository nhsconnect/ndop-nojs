import datetime
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

    def validate(self):
        return_value = Form.validate(self)
        if not return_value:
            return False

        if not self.first_name.data or not self.last_name.data:
            if not self.first_name.data:
                self.first_name.errors.append({
                    "id": "firstNameInputLink",
                    "message": "First name is missing",
                    "href": "firstNameContainer",
                    "error_alert": "Enter your first name"
                })

            if not self.last_name.data:
                self.last_name.errors.append({
                    "id": "lastNameInputLink",
                    "message": "Last name is missing",
                    "href": "lastNameContainer",
                    "error_alert": "Enter your last name"
                })

            return False

        return True


class DOBForm(Form):
    day = IntegerField(
        "Day", validators=[NumberRange(min=1, max=31)], widget=NumberInput()
    )
    month = IntegerField(
        "Month", validators=[NumberRange(min=1, max=12)], widget=NumberInput()
    )
    year = IntegerField(
        "Year", validators=[NumberRange(min=1900, max=3000)], widget=NumberInput()
    )

    def validate(self):
        return_value = Form.validate(self)

        if not return_value:
            entries_to_check = ["day", "month", "year"]

            if any(key in self.errors.keys() for key in entries_to_check):
                for entry in entries_to_check:
                    self.errors.pop(entry, None)

                new_message = {
                    "dob": [
                        {'message': "Date of birth is missing or invalid", "href": "dateOfBirthDayContainer", "id": "dateOfBirthInputLink"},
                        {'message': "Not a valid Date value", "href": "dateOfBirthDayContainer", "id": "dateOfBirthInputLink"},
                    ]
                }
                self.errors.update(new_message)
            return False

        try:
            datetime.date(self.year.data, self.month.data, self.day.data)
        except ValueError:
            new_message = {
                "dob": ["Date of birth is missing or invalid", "Not a valid Date value"]
            }
            self.errors.update(new_message)
            return False

        return True


class AuthOption(Form):
    radio = RadioField("test", choices=[("Yes", "Yes"), ("No", "No")])

    def validate(self):
        return_value = Form.validate(self)

        if not return_value:
            self.errors.update({
                "nhs_number": [
                    {"message": "Select an option", "href": "radioFormLegend", "id": "authOptionErrorLink"}
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
            self.nhs_number.errors.append({"message": "NHS number is missing or invalid", "href": "nhsNumberContainer", "id": "nhsNumberInputLink", "error_alert": "Please enter your NHS Number" })
            return False

        if number_length_validator.normalise_number(self.nhs_number.data, self.NHS_NUMBER_LENGTH) is None:
            self.nhs_number.errors.append({"message": "NHS number is missing or invalid", "href": "nhsNumberContainer", "id": "nhsNumberInputLink", "error_alert": "Please enter your NHS Number"})

            return False

        return True


class PostcodeForm(Form):
    postcode = StringField("postcode")

    def validate(self):
        return_value = Form.validate(self)
        if not return_value:
            pass

        if not self.postcode.data:
            self.postcode.errors.append({"message": "Postcode is missing or invalid", "id": "postcodeInputLink", "href": "postcodeContainer", "error_alert": "Please enter your postcode"})
            return False

        if postcode_validator.normalise_postcode(self.postcode.data) is None:
            self.postcode.errors.append({"message": "Postcode is missing or invalid", "id": "postcodeInputLink", "href": "postcodeContainer", "error_alert": "Please enter your postcode"})
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
                    {"message": "No choice selected", "href": "preference", "id": "setPreferencesInputLink" }
                ]
            })
            return False

        return True
