import unittest
from ndopapp import routes, create_app
from ndopapp.main.ndop_validator import PostcodeValidator, NumberLengthValidator


class PostcodeValidatorTests(unittest.TestCase):

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.postcode_validator = PostcodeValidator()

    def tearDown(self):
        pass

    def test_normalise_postcode_valid(self):
        test_cases = (
            ('hg1 1rt', 'HG1 1RT'),
            ('sw126ty', 'SW12 6TY'),
            ('l1 2rt', 'L1 2RT'),
            ('bt991ef', 'BT99 1EF'),
            ('bt99 1ef', 'BT99 1EF'),
            ('b11de', 'B1 1DE')
        )

        for i in range(0, len(test_cases)):
            postcode = test_cases[i][0]
            expected_postcode = test_cases[i][1]
            normalised_postcode = self.postcode_validator.normalise_postcode(postcode)

            with self.subTest(i=i):
                assert normalised_postcode == expected_postcode

    def test_normalise_postcode_not_valid(self):
        test_cases = (
            'hg1 1rtrt',
            '321 1RT',
            'smarty',
            'smarty'
        )

        for i in range(0, len(test_cases)):
            postcode = test_cases[i]
            normalised_postcode = self.postcode_validator.normalise_postcode(postcode)

            with self.subTest(i=i):
                assert normalised_postcode is None


class NumberLengthValidatorTests(unittest.TestCase):

    number_LENGTH = 10

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.number_length_validator = NumberLengthValidator()

    def tearDown(self):
        pass

    def test_normalise_number_valid(self):
        test_cases = (
            ('1234567890', '1234567890'),
            ('  0987654321', '0987654321'),
            ('99 999 9999 9', '9999999999')
        )

        for i in range(0, len(test_cases)):
            number, expected_hs_number = test_cases[i]
            normalised_number = self.number_length_validator.\
                    normalise_number(number, self.number_LENGTH)

            with self.subTest(i=i):
                assert normalised_number == expected_hs_number

    def test_normalise_number_not_valid(self):
        test_cases = (
            '123456',
            '1RT$%^)(*&',
            'I2E4S67B9O'
        )

        for i in range(0, len(test_cases)):
            number = test_cases[i]
            normalised_number = self.number_length_validator.\
                    normalise_number(number, self.number_LENGTH)

            with self.subTest(i=i):
                assert normalised_number is None


if __name__ == '__name__':
    unittest.main()
