from logging.config import dictConfig
from flask import Flask
from corona.util import clear_cache_thread
from config import Config
import config
import os
from flask_cors import CORS
from threading import Thread
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

# extensions
cors = CORS()
mail = Mail()
db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)

    # Dynamically load config based on the testing argument or FLASK_ENV environment variable
    flask_env = os.getenv("FLASK_ENV", None)
    if flask_env == "testing":
        app.config.from_object(config.TestingConfig)
        dictConfig(config.TestingConfig.LOGGING_BASE)
    elif flask_env == "development":
        app.config.from_object(config.DevelopmentConfig)
        dictConfig(config.DevelopmentConfig.DEVELOPMENT_LOGGING)
    else:
        app.config.from_object(config.ProductionConfig)
        dictConfig(config.ProductionConfig.PRODUCTION_LOGGING)

    # Init extensions here
    # db.init_app(app)a
    cors.init_app(app)
    mail.init_app(app)
    db.init_app(app)

    # Add blueprints here
    from corona.routes import corona
    app.register_blueprint(corona)

    # THREADS HERE
    # cache_thread = Thread(target=clear_cache_thread, daemon=True)
    # cache_thread.start()

    # inorder to use this app at different places, use current app
    # from flask import current_app
    return app
