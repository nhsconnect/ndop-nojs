import unittest

from ndopapp import routes, create_app
from unittest.mock import patch
from http import HTTPStatus


class TestURLs(unittest.TestCase):

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.app = app

    def tearDown(self):
        self.client = None
        self.app = None

    # Home route
    def test_root_redirect(self):
        """ Test root URL gives a 302 """
        result = self.client.get('/')

        assert HTTPStatus(result.status_code) == HTTPStatus.FOUND
        assert routes.get_absolute("main.landing_page") in result.headers['Location']

    # Landing Page Route
    def test_landingpage_get(self):
        """ Test landing page URL returns 200 """

        result = self.client.get('/landingpage')

        assert HTTPStatus(result.status_code) == HTTPStatus.OK
        assert 'ndop_seen_cookie_message' in result.headers['Set-Cookie']

    @patch('ndopapp.main.controllers.redirect_to_route', return_value="_")
    def test_landingpage_post(self, make_response_mock):
        """ Test landing page posts to your_details page """
        self.client.post('/landingpage')

        make_response_mock.assert_called_with('yourdetails.your_details')


if __name__ == '__main__':
    unittest.main()
