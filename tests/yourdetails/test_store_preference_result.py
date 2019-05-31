import unittest
from flask import Flask
from unittest.mock import patch
from ndopapp.yourdetails.controllers import store_preference_result, routes

class YourDetailsStorePreferenceResultTests(unittest.TestCase):
    
    def setUp(self):
        self.app_patcher = patch('ndopapp.yourdetails.controllers.app')
        self.app_mock = self.app_patcher.start()
        self.addCleanup(self.app_patcher.stop)

        self.session_patcher = patch('ndopapp.yourdetails.controllers.session')
        self.session_mock = self.session_patcher.start()
        self.addCleanup(self.session_patcher.stop)
        self.session_mock.get.return_value = None

    @patch('ndopapp.yourdetails.controllers.get_store_preference_result', return_value='success')
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    def test_preference_result_when_store_preferences_is_succeeded(self, redirect_mock, _):
        with Flask(__name__).app_context():
            store_preference_result.__wrapped__('some session id')

        redirect_mock.assert_called_with('yourdetails.thank_you')

    @patch('ndopapp.yourdetails.controllers.session')
    @patch('ndopapp.yourdetails.controllers.get_store_preference_result', return_value='failure')
    @patch('ndopapp.yourdetails.controllers.redirect_to_route')
    def test_preference_result_when_store_preferences_is_failed(self, redirect_mock, _, session):
        session.get.return_value = 9999999999999999999999999999999999999999999

        with Flask(__name__).app_context():
            store_preference_result.__wrapped__('some session id')

        redirect_mock.assert_called_with('yourdetails.choice_not_saved')
        session.pop.assert_called()

    @patch('ndopapp.yourdetails.controllers.get_store_preference_result', return_value='not_completed')
    @patch('ndopapp.yourdetails.controllers.render_template')
    def test_preference_result_when_store_preferences_is_not_completed_yet(self, render_template_mock, _):
        with Flask(__name__).app_context():
            store_preference_result.__wrapped__('some session id')

        render_template_mock.assert_called_with('waiting-for-results.html', waiting_message='Saving your choice', routes=routes)
