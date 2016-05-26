import os

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

DEBUG = False
SECRET_KEY = 'secret-key'
SITE_TITLE = 'Stellar Robot'
DEFAULT_ROLE = 'user'
FEE_PERCENT = 0.12
LOCK_EXPIRE = 60 * 8

from config_prod import *