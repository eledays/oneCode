from dotenv import load_dotenv
load_dotenv()

import os

from flask import Flask
from config import Config

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

valid_fp_users = set()

from app.my_logger import Logger
logger = Logger('user_actions.log')

if not os.path.exists(app.config.get('USER_CODE_PATH')):
    with open(app.config.get('USER_CODE_PATH'), 'w') as f:
        f.write('')

from flask_socketio import SocketIO
socket = SocketIO(app)

from app import routes, models