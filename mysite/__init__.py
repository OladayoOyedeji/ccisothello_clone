# File: mysite/__init__.py

# import os, sys
# sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from flask import Flask
app = Flask(__name__, static_url_path='')

try:
    if running_locally:
        from mysite import localconfig as config
    else:
        from mysite import config
except NameError:
    from mysite import config

app.config.from_object(config.__name__)

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

from flask import session

# imports here to avoid circular reference
from mysite import models
from mysite import views

#==================================================================
# Session
#==================================================================
from config import SESSION_SECRET_KEY
app.secret_key = SESSION_SECRET_KEY # Check
