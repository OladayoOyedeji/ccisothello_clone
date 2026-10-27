# localconfig.py

import os
import datetime
import string

#==================================================================
# System level constants
#==================================================================
BASEDIR = os.path.abspath(os.path.dirname(__file__))
basedir = BASEDIR

#==================================================================
# App level data
#
# DEBUG == True:
# * Email sent to author (example: registration, reset password,
#   etc.
# * DEBUG section in base.html
#==================================================================
TITLE = 'Othello'
AUTHOR = 'yliow'
COPYRIGHT = '2016'
AUTHOR_EMAIL = 'yliow@ccis.edu'
DEBUG = True
UPLOAD_FOLDER = basedir + "/data"

#==================================================================
# DB server configuration
#==================================================================
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://othello_user:robert1$1$@localhost/othello"
SQLALCHEMY_POOL_RECYCLE = 299

#==================================================================
# DB constants
#==================================================================
USER_LENGTH = 30
USER_MIN_LENGTH = 1
EMAIL_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 50
HASHEDPASSWORD_LENGTH = 65
SESSION_KEY_LENGTH = 65
SALT_LENGTH = 50
RANDOM_LENGTH = 16
HASH_ROUNDS = 100 # 100000
DTIME_FOR_REGISTRATION = datetime.timedelta(minutes=15)
USER_CHARS = "%s%s." % (string.ascii_letters, string.digits)
EMAIL_SUBSTRINGS = []

#==================================================================
# Web server configuration
#==================================================================
BASE_URL = 'http://rbfrappier1.pythonanywhere.com/'

#==================================================================
# Configuration for Flask-WTF forms
#==================================================================
WTF_CSRF_ENABLED = True
SECRET_KEY = 'alhksjhaiufisufkjhldlf'

#==================================================================
# Email configuration
#==================================================================
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'yliow.submit@gmail.com'
MAIL_PASSWORD = 'lsKDjfh*&we^q(*&eHqawdi'

#==================================================================
# Session
#==================================================================
SESSION_SECRET_KEY = "'H\xd1\xa1NVhiO\x9b\xf5zEq\x18\xc2\xcaq\xc9/\xae7|:"
