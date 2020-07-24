# coding: utf-8

from flask import Flask
from flaskr import config


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY="production",
            SQLALCHEMY_DATABASE_URI=config.MYSQL_CONFIG_PRODUCTION['DB_CONNECT_STRING']
        )
    else:
        app.config.from_mapping(
            SECRET_KEY="testing",
            SQLALCHEMY_DATABASE_URI=config.MYSQL_CONFIG_TESTING['DB_CONNECT_STRING']
        )
        app.config.update(test_config)

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # register the database commands
    from flaskr import db

    db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth

    app.register_blueprint(auth.bp)
    # app.register_blueprint(blog.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    return app

