import unittest
from ndopapp import routes, create_app
from ndopapp.yourdetails.forms import NameForm, DOBForm, ChoiceOption


class YourDetailsFormsTests(unittest.TestCase):
    """ Tests for forms in the yourdetails module """

    def setUp(self):
        self.app = create_app('ndopapp.config.TestConfig')

    def tearDown(self):
        pass

    # Name Form validation
    def test_name_from_valid(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            form.first_name.data = 'dave'
            form.last_name.data = 'smith'
            self.assertTrue(form.validate())

    def test_name_form_missing_first_name(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            form.last_name.data = 'dave'
            self.assertFalse(form.validate())
            self.assertEqual(form.first_name.errors, [
                             {'message': 'Enter your first name', 'id': 'firstNameInputLink', 'href': 'firstNameContainer', 'error_alert': 'Enter your first name'}])

    def test_name_form_missing_last_name(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            form.first_name.data = 'dave'
            self.assertFalse(form.validate())
            self.assertEqual(form.last_name.errors, [
                             {'message': 'Enter your last name', 'id': 'lastNameInputLink', 'href': 'lastNameContainer', 'error_alert': 'Enter your last name'}])

    def test_name_form_missing_both_names(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            self.assertFalse(form.validate())
            self.assertEqual(form.first_name.errors, [
                             {'message': 'Enter your first name', 'id': 'firstNameInputLink', 'href': 'firstNameContainer', 'error_alert': 'Enter your first name'}])
            self.assertEqual(form.last_name.errors, [
                             {'message': 'Enter your last name', 'id': 'lastNameInputLink', 'href': 'lastNameContainer', 'error_alert': 'Enter your last name'}])

    def test_name_form_last_name_too_long(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            form.first_name.data = 'dave'
            form.last_name.data = 'qwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyu'
            self.assertFalse(form.validate())

    def test_name_form_first_name_too_long(self):
        with self.app.test_request_context('/'):
            form = NameForm()
            form.first_name.data = 'qwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyuiopasdfghjklzxcvbnqwertyu'
            form.last_name.data = 'smith'
            self.assertFalse(form.validate())

    # DOB form validation
    def test_dob_form_valid_date(self):
        test_cases = (
            (22, 8, 2000),
            (1, 1, 1988),
            (29, 2, 2004)
        )

        for i in range(0, len(test_cases)):
            day, month, year = test_cases[i]

            with self.subTest(i=i):
                with self.app.test_request_context('/'):
                    form = DOBForm()
                    form.day.data = day
                    form.month.data = month
                    form.year.data = year
                assert form.validate() is True

    def test_dob_form_invalid_date(self):
        test_cases = (
            (35, 8, 2000),
            (1, 15, 1988),
            (24, 2, 890),
            (99, 99, 9999),
            (None, 1, 2000),
            (None, None, None),
            (31, 9, 2000),
            (29, 2, 2001)
        )

        for i in range(0, len(test_cases)):
            day, month, year = test_cases[i]

            with self.subTest(i=i):
                with self.app.test_request_context('/'):
                    form = DOBForm()
                    form.day.data = day
                    form.month.data = month
                    form.year.data = year
                assert form.validate() is False

    # setyourpreferences
    def test_choices_option_valid(self):
        with self.app.test_request_context('/'):
            form = ChoiceOption()
            form.radio.data = 'Yes'
            self.assertTrue(form.validate())

    def test_choices_option_missing_preference(self):
        with self.app.test_request_context('/'):
            form = ChoiceOption()
            form.radio.data = None
            self.assertFalse(form.validate())
            self.assertEqual(form.errors, {'radio': ['Not a valid choice'], 'preference': [{'message': 'Select your choice', 'href': 'preference', 'id': 'setPreferencesInputLink'}]})


if __name__ == '__main__':
    unittest.main()
