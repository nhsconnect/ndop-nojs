def create_module(app, **kwargs):
    from .controllers import yourdetails_blueprint

    app.register_blueprint(yourdetails_blueprint, url_prefix=app.config.get("URL_PREFIX"))
    
