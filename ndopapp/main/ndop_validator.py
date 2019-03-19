import re

NON_ALPHA_RE = re.compile("[^A-Z0-9]+")
POSTCODE_RE = re.compile("^[A-Z]{1,2}[0-9]{1,2}[A-Z]? [0-9][A-Z]{2}$")


class PostcodeValidator:
    @staticmethod
    def normalise_postcode(postcode):
        """ Return a normalised postcode if valid, or None if not."""

        postcode = NON_ALPHA_RE.sub("", postcode.upper())
        postcode = postcode[:-3] + " " + postcode[-3:]
        if POSTCODE_RE.match(postcode):
            return postcode
        return None


class NumberLengthValidator:

    @staticmethod
    def normalise_number(number, number_length):
        """ Return a normalised NHS number if valid, or None if not, """
        number = ''.join(c for c in number if c.isnumeric())
        if len(number) == number_length:
            return number
        return None
