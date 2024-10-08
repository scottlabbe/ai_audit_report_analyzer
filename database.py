import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy()

DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db(app):
    db.init_app(app)
    import models
    Base.metadata.create_all(bind=engine)
    return db

def get_db():
    return db_session

def shutdown_session(exception=None):
    db_session.remove()
