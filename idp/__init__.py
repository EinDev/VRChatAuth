import os

import flask_cors
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .models import db
from .oauth2 import config_oauth
from .routes import bp, ratelimit
from .tasks import celery_init_app
from idp.celery.vrc_api import vrc_init_app

import logging

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)


def create_vrc_worker(config=None):
    return create_app(None, True)


def create_monitoring_worker(config=None):
    return create_app(None, False)


def create_app(config=None, with_vrc_api=False):
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    # load default configuration
    app.config.from_object('idp.settings')
    app.config.from_prefixed_env()

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load app specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    setup_app(app, with_vrc_api)
    return app


def setup_app(app: Flask, with_vrc_api: bool):
    flask_cors.CORS(app)
    db.init_app(app)
    # Create tables if they do not exist already
    with app.app_context():
        db.create_all()
    config_oauth(app)
    if with_vrc_api:
        vrc_init_app(app)
    celery_init_app(app)
    ratelimit.init_app(app)
    app.register_blueprint(bp, url_prefix='')
