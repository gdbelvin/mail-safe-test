"""
settings.py

Configuration for Flask app

Important: Place your keys in the secret_keys.py module, 
           which should be kept out of version control.

"""

from secret_keys import *

class Config(object):
    # Set secret keys for CSRF protection
    SECRET_KEY = CSRF_SECRET_KEY
    CSRF_SESSION_KEY = SESSION_KEY
    GOOGLE_ID = GOOGLE_ID
    GOOGLE_SECRET = GOOGLE_SECRET
    # Flask-Cache settings
    CACHE_TYPE = 'gaememcached'
    SERVER_EMAIL = 'admin@wisebold.com'

class Development(Config):
    DEBUG = True
    # Flask-DebugToolbar settings
    CSRF_ENABLED = True

class Testing(Config):
    TESTING = True
    DEBUG = True
    CSRF_ENABLED = True

class Production(Config):
    DEBUG = False
    CSRF_ENABLED = True
