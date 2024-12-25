import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    DEFAULT_SYMBOLS_COUNT = 20
    SYMBOLS_UPDATING_TIME = 5#3 * 60
    USER_CODE_PATH = os.path.join(basedir, 'user_code.txt')
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH')