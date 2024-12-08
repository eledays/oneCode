from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from config import Config

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

valid_fp_users = set()

from app.my_logger import Logger
logger = Logger('user_actions.log')

from app import routes, models