# this file holds the logic to create and configure the flask app 
from flask import Flask
from app.econf.config import Config

# returns configured flask app instance 
def create_app(config_class=Config):
    # create app instance
    app = Flask(__name__)
    # load config from config class
    app.config.from_object(config_class)
    # register api route (/apu is the route and further we'll have request and response endpoints)
    from app.routes.main import bp as main_bp
    # registers the routes with api prefix 
    app.register_blueprint(main_bp, url_prefix='/api')
    return app 
    