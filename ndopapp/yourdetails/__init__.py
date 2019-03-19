def create_module(app, **kwargs):
    from .controllers import yourdetails_blueprint
    from .errors import yourdetails_errors_blueprint

    app.register_blueprint(yourdetails_blueprint, url_prefix=app.config.get("URL_PREFIX"))
    if not app.config.get("DEBUG") and not app.config.get("TESTING"):
        app.register_blueprint(yourdetails_errors_blueprint, url_prefix=app.config.get("URL_PREFIX"))
