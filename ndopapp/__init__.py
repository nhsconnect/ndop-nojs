from flask import Flask
from .logging import install_logger
from ndopapp import routes


def create_app(object_name):
    install_logger()

    app = Flask(__name__)
    app.config.from_object(object_name)

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
