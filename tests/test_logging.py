from unittest import mock
from io import StringIO
from contextlib import contextmanager
from ndopapp.logging import PipeFormatter, record_factory

import unittest
import logging
import json
import os
import copy


class PipeFormatterTest(unittest.TestCase):

    @staticmethod
    def create_logger(*formatter_args, **formatter_kwargs):
        stream = StringIO()

        handler = logging.StreamHandler(stream)
        handler.setFormatter(PipeFormatter(*formatter_args, **formatter_kwargs))

        logger = logging.Logger("test")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger, stream

    @staticmethod
    def fixed_date_record_factory(*args, **kwargs):
        record = logging.LogRecord(*args, **kwargs)
        record.created = 1551104100.43
        return record

    def setUp(self):
        logging.disable(logging.NOTSET)
        self.record_factory = logging.getLogRecordFactory()

    def tearDown(self):
        logging.disable(logging.CRITICAL)
        logging.setLogRecordFactory(self.record_factory)

    def assertOutputIs(self, stream, expected):
        lines = stream.getvalue().splitlines()
        parsed = [[part.strip().split("=", 1) for part in line.split(" | ")] for line in lines]
        self.assertEqual(len(parsed), len(expected), "Unexpected number of log lines")
        for line, expected_line in zip(parsed, expected):
            self.assertEqual(len(line), len(expected_line), "Unexpected number of fields")
            for item, expected_item in zip(line, expected_line):
                self.assertSequenceEqual(item, expected_item, "Field sequence does not match")

    def test_only_specified_fields_output(self):
        """The formatter only outputs fields specified"""
        logger, stream = self.create_logger(['message'])
        logger.info("Hello World")
        self.assertOutputIs(stream, [[
            ('message', '"Hello World"')
        ]])
        logger, stream = self.create_logger(['levelname'])
        logger.info("Hello World")
        self.assertOutputIs(stream, [[
            ('levelname', '"INFO"')
        ]])

    def test_message_always_json_string_formatted(self):
        """"The message is always output as a json string, regardless of data type"""
        test_values = ("hello world", 1, None, {}, [])
        for test_value in test_values:
            logger, stream = self.create_logger(['message'])
            logger.info(test_value)
            self.assertOutputIs(stream, [[
                ('message', json.dumps(str(test_value)))
            ]])

    def test_data_json_formatted(self):
        """Fields other than message are output as a json representation or their type"""
        test_values = ("hello world",  1, None, {}, [])
        for test_value in test_values:
            logger, stream = self.create_logger(['message'])
            logger.info("", {'data': test_value})
            self.assertOutputIs(stream, [[
                ('message', '""'),
                ('data', json.dumps(test_value))
            ]])

    def test_field_order_maintained(self):
        """Fields are output in the order requested"""
        logger, stream = self.create_logger(['message', 'levelname'])
        logger.info("message")
        self.assertOutputIs(stream, [[
            ('message', '"message"'),
            ('levelname', '"INFO"')
        ]])
        logger, stream = self.create_logger(['levelname', 'message'])
        logger.info("message")
        self.assertOutputIs(stream, [[
            ('levelname', '"INFO"'),
            ('message', '"message"')
        ]])

    def test_field_renaming(self):
        """Fields may be renamed"""
        logger, stream = self.create_logger([('message', 'the_messsage'), 'levelname'])
        logger.info("message")
        self.assertOutputIs(stream, [[
            ('the_messsage', '"message"'),
            ('levelname', '"INFO"'),
        ]])

    def test_date_format(self):
        """Dates are outout in the correct default format"""
        logging.setLogRecordFactory(self.fixed_date_record_factory)

        logger, stream = self.create_logger(['asctime'])
        logger.info("message")
        self.assertOutputIs(stream, [[
            ('asctime', '"25-02-2019 14:15:00.430000"'),
        ]])

    def test_custom_date_format(self):
        """Date formats can customized"""
        logging.setLogRecordFactory(self.fixed_date_record_factory)

        logger, stream = self.create_logger(['asctime'], '%d')
        logger.info("message")
        self.assertOutputIs(stream, [[
            ('asctime', '"25"'),
        ]])


class RecordFactoryTest(unittest.TestCase):

    mock_request = type('obj', (object,), {
        'remote_addr': "127.0.0.1",
        'cookies': {
            'session_id_nojs': "sessionID"
        },
        'headers': {
            'X-AMZ-REQUEST-ID': 'requestID',
            'X-AMZ-STAGE': 'stage',
            'User-Agent': "userAgent"
        },
        'environ': {
            'lambda.context': type('obj', (object,), {
                'function_name': 'functionName',
                'function_version': 'functionVersion',
                'aws_request_id': 'awsRequestId'
            })
        }
    })

    mock_g = {'session_id_override': 'sessionID_1'}
    mock_empty_g = {}

    def setUp(self):
        self.record_factory = logging.getLogRecordFactory()
        logging.setLogRecordFactory(record_factory)

    def tearDown(self):
        logging.setLogRecordFactory(self.record_factory)

    @contextmanager
    def env_var(self, key, value):
        original = os.environ.get(key)
        os.environ[key] = value
        yield
        if original is not None:
            os.environ[key] = original
        else:
            del os.environ[key]

    def test_environment_added_to_record(self):
        """The AWS_ENV_NAME environment variable is added to log records as the environment attribute"""
        with self.env_var('AWS_ENV_NAME', 'Hello World'):
            record = logging.makeLogRecord({})
            self.assertEqual('Hello World', record.environment)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.request", mock_request)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_request_attributes(self):
        """The source IP address is added to log records as the source_ip_address attribute"""
        record = logging.makeLogRecord({})
        self.assertEqual("127.0.0.1", record.source_ip_address)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_x_forwarded_for_used_when_available(self):
        """The -3rd x-forwarded-for IP address is used, when available"""
        mock_forwarded_request = copy.deepcopy(self.mock_request)
        mock_forwarded_request.headers['X-Forwarded-For'] = '1.1.1.1,2.2.2.2,3.3.3.3,4.4.4.4,5.5.5.5'
        with mock.patch("ndopapp.logging.request", mock_forwarded_request):
            record = logging.makeLogRecord({})
        self.assertEqual("3.3.3.3", record.source_ip_address)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_spaces_trimmed_from_x_forwarded_for(self):
        """White spaces are stripped from around the relevant x-forwarded-for IP"""
        mock_forwarded_request = copy.deepcopy(self.mock_request)
        mock_forwarded_request.headers['X-Forwarded-For'] = '1.1.1.1,2.2.2.2,    3.3.3.3     ,4.4.4.4,5.5.5.5'
        with mock.patch("ndopapp.logging.request", mock_forwarded_request):
            record = logging.makeLogRecord({})
        self.assertEqual("3.3.3.3", record.source_ip_address)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_unexpected_x_forwarded_for(self):
        """When an x-forwarded-for header with fewer than 3 IPs is passed, the default IP is used instead"""
        mock_forwarded_request = copy.deepcopy(self.mock_request)
        mock_forwarded_request.headers['X-Forwarded-For'] = '1.1.1.1,2.2.2.2'
        with mock.patch("ndopapp.logging.request", mock_forwarded_request):
            record = logging.makeLogRecord({})
        self.assertEqual("127.0.0.1", record.source_ip_address)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.request", mock_request)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_request_headers(self):
        """Specific headers are added to the log record"""
        record = logging.makeLogRecord({})
        self.assertEqual("requestID", record.api_request_id)
        self.assertEqual("stage", record.api_stage)
        self.assertEqual("userAgent", record.user_agent)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.request", mock_request)
    @mock.patch("ndopapp.logging.g", mock_empty_g)
    def test_request_cookies(self):
        """The session id is added to log records as the session_id attribute"""
        record = logging.makeLogRecord({})
        self.assertEqual("sessionID", record.session_id)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.request", mock_request)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_request_global_session_id(self):
        """The session id is added to log records as the session_id attribute"""
        record = logging.makeLogRecord({})
        self.assertEqual("sessionID_1", record.session_id)

    @mock.patch("ndopapp.logging.has_request_context", lambda: True)
    @mock.patch("ndopapp.logging.request", mock_request)
    @mock.patch("ndopapp.logging.g", mock_g)
    def test_lambda_context(self):
        """Specific lambda context variables are added to the log record"""
        record = logging.makeLogRecord({})
        self.assertEqual("functionName", record.function_name)
        self.assertEqual("functionVersion", record.function_version)
        self.assertEqual("awsRequestId", record.invocation_id)
