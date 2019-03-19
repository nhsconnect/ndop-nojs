import json
import unittest
from ndopapp import routes, utils, create_app, config
from mock import patch, MagicMock
from tests import common


class TestUtils(unittest.TestCase):

    def setUp(self):
        app = create_app('ndopapp.config.TestConfig')
        self.client = app.test_client()
        self.client.set_cookie("test", common.SESSION_COOKIE_KEY, common.SESSION_ID)
        self.app = app

    def tearDown(self):
        del self.client
        del self.app

    # create_error_messages_dict
    def test_create_error_messages_dict(self):

        messagesDict = utils.create_error_messages_dict("HTTPError", "jim", "jam")

        assert messagesDict == {0: ['HTTPError'], 1: ['jim'], 2: ['jam']}

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.requests')
    def test_is_session_valid_when_session_is_valid(self, requests_mock, _):
        chech_session_response = json.dumps({'valid': True})

        response_object_mock = MagicMock()
        response_object_mock.text = chech_session_response
        requests_mock.get.return_value = response_object_mock

        self.assertTrue(utils.is_session_valid('some session id'))

    @patch('ndopapp.utils.request')
    @patch('ndopapp.utils.is_session_valid', return_value=False)
    @patch('ndopapp.utils.render_template')
    def test_check_session_renders_session_expired(self, render_mock, _, __):

        wrapper = utils.check_session(None)
        wrapper()

        render_mock.assert_called_once()

    def test_is_session_valid_when_session_is_none(self):
        self.assertFalse(utils.is_session_valid(None))

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.redirect')
    def test_catch_unhandled_exception(self, redirect_mock, _):

        def bang():
            raise Exception('bang')
        wrapper = utils.catch_unhandled_exceptions(bang)
        wrapper()
        redirect_mock.assert_called_with(routes.get_absolute('yourdetails.generic_error'))

    @patch('ndopapp.utils.routes')
    def test_ensure_safe_redirect_url_returns_landing_page_for_unknown_urll(self,
            routes_mock):

        utils.ensure_safe_redirect_url('unknown_target')
        routes_mock.get_absolute.assert_called_with('main.landing_page')


    @patch('ndopapp.utils.app')
    def test_aws_lambda_function_name_composing(self, app_mock):

        app_mock.config = {
            'AWS_DEFAULT_REGION': 'eu-west-2',
            'AWS_ACCOUNT_ID': '999999999999',
            'AWS_ENV_NAME': 'ndop-build10',
        }

        func_name = utils.get_full_aws_lambda_function_name('get-state-model')

        self.assertEqual(
            func_name,
            "arn:aws:lambda:eu-west-2:999999999999:function:ndop-build10-get-state-model"
        )

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.json.loads')
    @patch('ndopapp.utils.boto3.client')
    def test_aws_lambda_invoke_return_payload_not_none(self, boto_mock, json_loads_mock, _):

        session_id = '111111'
        data = json.dumps({'session_id' : session_id})

        payload_mock = MagicMock()
        payload_mock.read.return_value = json.dumps(
            {'session_id': session_id, 'contact_centre': True})

        boto_mock('lambda').invoke.return_value = {'StatusCode': 200, 'Payload': payload_mock}

        payload = utils.aws_lambda_invoke('get-state-model', data=data)
        assert payload is not None
        assert payload.get('session_id') is not None

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.boto3.client')
    def test_aws_lambda_invoke_return_payload_is_none(self, boto_mock, _):

        session_id = '111111'
        data = json.dumps({'session_id' : session_id})

        payload_mock = MagicMock()
        payload_mock.read.return_value = json.dumps(
            {'session_id': session_id, 'contact_centre': True})

        boto_mock('lambda').invoke.return_value = {'StatusCode': 401, 'Payload': payload_mock}

        payload = utils.aws_lambda_invoke('get-state-model', data=data)
        assert payload is None

    @patch('ndopapp.utils.request')
    @patch('ndopapp.utils.aws_lambda_invoke')
    def test_aws_get_state_model_invoke_aws_lambda_invoke(self, invoke_mock, request_mock):

        request_mock.cookies.get.return_value = '111111'

        utils.aws_lambda_get_state_model()
        invoke_mock.assert_called()

    @patch('ndopapp.utils.aws_lambda_invoke')
    def test_aws_put_state_model_invoke_aws_lambda_invoke(self, invoke_mock):

        utils.aws_lambda_put_state_model(state_model_json=None)
        invoke_mock.assert_called()

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.request')
    def test_clean_state_model_locally_returns_expected_values(self, request_mock, _):

        request_mock.cookies.get.return_value = '111111'

        state_model_json = json.loads(json.dumps({
            'contact_centre': True,
            'expiry_time_key': 1551374328,
            'flow': 'nhs_number',
            "code": "SMSP-0000",
            "message_id": "6E2DDAE3-00D9-4084-8059-48530D3EAA37",
            "email_address": "greg0003@tbd-test.com",
            "nhs_number": "7777770003",
        }))

        clean_state_model = utils.clean_state_model_locally(state_model_json)
        assert 'contact_centre' in clean_state_model
        assert 'flow' in clean_state_model
        assert 'expiry_time_key' in clean_state_model

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.aws_lambda_get_state_model')
    @patch('ndopapp.utils.aws_lambda_put_state_model')
    def test_aws_lambda_invoke_does_not_call_put_state_model_when_get_state_model_returns_none(self,
        put_state_model_mock, get_state_model_mock, _):

        get_state_model_mock.return_value = None
        utils.clean_state_model()
        put_state_model_mock.assert_not_called()

    @patch('ndopapp.utils.app')
    @patch('ndopapp.utils.aws_lambda_get_state_model')
    @patch('ndopapp.utils.aws_lambda_put_state_model')
    @patch('ndopapp.utils.clean_state_model_locally')
    def test_aws_lambda_invoke_calls_put_state_model_when_get_state_model_returns_not_none(self,
        clean_state_model_mock, put_state_model_mock, get_state_model_mock, _):

        clear_state_model = json.dumps({})
        get_state_model_mock.return_value = json.dumps({})
        clean_state_model_mock.return_value = clear_state_model
        utils.clean_state_model()
        put_state_model_mock.assert_called_with(clear_state_model)


    def test_ensure_leading_slash(self):

        ret = config.ensure_leading_slash('error.html')
        self.assertEqual(ret, '/error.html')

    def test_ensure_leading_slash_inside_if(self):

        ret = config.ensure_leading_slash('/error.html')
        self.assertEqual(ret, '/error.html')

    def test_routes_get_raw_throws_exception(self):

        with self.assertRaises(Exception) as context:
            routes.get_raw('incorrect_route')
        self.assertTrue('Invalid route' in str(context.exception))
