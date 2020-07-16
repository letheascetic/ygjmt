# coding: utf-8

import click
import logging
from server import config
from flask.cli import with_appcontext
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)

engine = create_engine(config.MYSQL_CONFIG_TESTING['DB_CONNECT_STRING'], echo=False)
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    from server.models import UserInfo, HndfStaticInfo
    Base.metadata.create_all(bind=engine)


def shutdown_session(exception=None):
    db_session.remove()


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(shutdown_session)       # 告诉 Flask 在返回响应后进行清理的时候调用此函数
    app.cli.add_command(init_db_command)            # 添加一个新的 可以与 flask 一起工作的命令


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


