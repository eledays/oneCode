from dotenv import load_dotenv
load_dotenv()

import os

import eventlet
eventlet.monkey_patch()

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
socket = SocketIO(app, async_mode='eventlet', ping_timeout=240, ping_interval=25, cors_allowed_origins='*')

admin_id = app.config.get('ADMIN_ID')

from app import routes, models, admin_routes