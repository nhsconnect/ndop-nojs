from flask import Flask, template_rendered, request_started, request, current_app
from .logging import install_logger
from ndopapp import routes
from ndopapp.csrf import csrf


def log_request(sender, **extra):
    current_app.logger.info("starting controller", {
        'controller': request.url_rule and request.url_rule.endpoint
    })


def log_template(sender, template, **extra):
    current_app.logger.info('rendering page', {
        'page': request.url_rule and request.url_rule.endpoint,
        'template': template.name or 'string template'
    })


def create_app(object_name):
    install_logger()

    app = Flask(__name__)
    app.config.from_object(object_name)

    # Per request logging
    request_started.connect(log_request, app)
    template_rendered.connect(log_template, app)

    # CSRF protection
    csrf.init_app(app)

    routes.prefix = app.config.get('URL_PREFIX')
    routes.host = app.config.get('CLIENT_FACING_URL').strip('/')
    app.routes = routes

    from .main import create_module as main_create_module
    from .yourdetails import create_module as yourdetails_create_module
    from .verification import create_module as verification_create_module

    main_create_module(app)
    yourdetails_create_module(app)
    verification_create_module(app)

    return app
