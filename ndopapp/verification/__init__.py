def create_module(app, **kwargs):
    from .controllers import verification_blueprint

    app.register_blueprint(verification_blueprint, url_prefix=app.config.get("URL_PREFIX"))
