def create_module(app):
    from .controllers import main_blueprint
    from .errors import errors_blueprint

    app.register_blueprint(main_blueprint, url_prefix=app.config.get("URL_PREFIX"))
    if not app.config.get("DEBUG") and not app.config.get("TESTING"):
        app.register_blueprint(errors_blueprint, url_prefix=app.config.get("URL_PREFIX"))
