def create_module(app):
    from .controllers import main_blueprint

    app.register_blueprint(main_blueprint, url_prefix=app.config.get("URL_PREFIX"))
