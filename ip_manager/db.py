# coding: utf-8

import util
import click
import config
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


logger = logging.getLogger(__name__)


engine = create_engine(config.MYSQL_CONFIG_TESTING['DB_CONNECT_STRING'], echo=False)
db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    from sql.base import IpPool, Seeker
    Base.metadata.create_all(bind=engine)
    pass


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


if __name__ == "__main__":
    util.config_logger('db')
    init_db()
    pass
