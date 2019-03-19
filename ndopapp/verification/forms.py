from flask_wtf import FlaskForm as Form
from wtforms import RadioField, StringField
from ..main.ndop_validator import NumberLengthValidator

number_length_validator = NumberLengthValidator()


class VerificationForm(Form):
    radio = RadioField("test")


class VerificationOption(Form):
    radio = RadioField("VerificationOption", choices=[])

    def __init__(self, *args, user_details, **kwargs):
        super().__init__(*args, **kwargs)

        choices = []
        if user_details.email:
            choices.append(('Email', 'Send an email to ' + user_details.email))
        if user_details.sms:
            choices.append(('SMS', 'Send an sms to ' + user_details.sms))
        choices.append(('Unrecognised', 'I do not recognise this email address or phone number'))
        self.radio.choices = choices


class CodeForm(Form):
    enterOtpInput = StringField("EnterOtpForm")
    CODE_LENGTH = 6

    def validate(self):
        if not Form.validate(self):
            return False

        if not self.enterOtpInput.data:
            self.enterOtpInput.errors.append({
                "message": "Enter your code below",
                "href": "enterOtpInput",
                "id": "enterOtpInputLink"})
            return False

        if number_length_validator.normalise_number(
                self.enterOtpInput.data, self.CODE_LENGTH) is None:
            self.enterOtpInput.errors.append({
                "message": "The code you provided was incorrect",
                "href": "enterOtpInput",
                "id": "enterOtpInputLink"
            })
            return False

        return True

    def add_incorrect_otp_error(self):
        self.enterOtpInput.errors.append({
            "message": "Re-enter your code below",
            "id": "enterOtpInput",
            "href": "enterOtpInputLink"})
