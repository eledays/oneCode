import os
from datetime import timedelta
import secrets
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

dotenv_path = os.path.join(basedir, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    DEFAULT_SYMBOLS_COUNT = 90
    SYMBOLS_UPDATING_TIME = 45
    USER_CODE_PATH = os.path.join(basedir, 'user_code.txt')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')
    COOKIE_UPDATE_TIMEOUT = timedelta(minutes=5)
    ADMIN_ID = os.environ.get('ADMIN_ID')