from flask import request, has_request_context, g

import itertools
import logging
import json
import collections
import datetime
import os


class PipeFormatter(logging.Formatter):

    converter = datetime.datetime.fromtimestamp

    def __init__(self, fields, datefmt=None):
        self.fields = fields
        self.datefmt = datefmt

    def ipairs(self, record):
        for field in self.fields:
            alias = field
            if not isinstance(field, str):
                field, alias = field
            yield alias, getattr(record, field, "")

        if isinstance(record.args, collections.Mapping):
            yield from record.args.items()

    def formatMessage(self, record):
        return " | ".join(f"{k}={json.dumps(v)}" for k, v in self.ipairs(record))

    def formatTime(self, record, date_format=None):
        created = self.converter(record.created)
        return created.strftime(date_format or "%d-%m-%Y %H:%M:%S.%f %z").strip()

    def usesTime(self):
        return 'asctime' in itertools.chain.from_iterable((field, field[0]) for field in self.fields)


def record_factory(*args, **kwargs):
    record = logging.LogRecord(*args, **kwargs)
    record.environment = os.environ.get('AWS_ENV_NAME')

    if has_request_context():
        # Request attributes
        x_forwarded_for = request.headers.get('X-Forwarded-For', '')
        try:
            # Assume we've got 2 proxies
            record.source_ip_address = x_forwarded_for.split(',')[-3].strip()
        except IndexError:
            record.source_ip_address = request.remote_addr

        # Cookies
        record.session_id = g.get('session_id_override', request.cookies.get('session_id_nojs'))

        # Headers
        record.api_request_id = request.headers.get('X-AMZ-REQUEST-ID')
        record.api_stage = request.headers.get('X-AMZ-STAGE')
        record.user_agent = request.headers.get('User-Agent')

        # Lambda context
        context = request.environ.get('lambda.context')
        record.function_name = context and context.function_name or None
        record.function_version = context and context.function_version or None
        record.invocation_id = context and context.aws_request_id or None

    return record


def install_logger():
    logging.setLogRecordFactory(record_factory)

    formatter = PipeFormatter([
        ('levelname', 'log_level'),
        ('asctime', 'time'),
        'message',
        'environment',
        'api_request_id',
        'api_stage',
        'function_name',
        'function_version',
        'invocation_id',
        'session_id',
        'source_ip_address',
        'user_agent'
    ])

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger("flask.app")
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(os.environ.get('LOG_LEVEL', logging.INFO))
