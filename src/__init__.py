from flask import Flask
from flask_socketio import SocketIO
import os
from src.config.config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

CORS(app)

if os.environ.get("APP_ENV") == 'development':
    config = Config().dev_config
else:
    config = Config().production_config

app.env = config.ENV

app.secret_key = os.environ.get("SECRET_KEY")
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("MYSQL_DB_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = os.environ.get("SQLALCHEMY_TRACK_MODIFICATIONS")

app.config['PUBLIC_FOLDER'] = os.path.join(os.getcwd(), 'public')

db = SQLAlchemy(app)

from src.routes import api
app.register_blueprint(api, url_prefix="/api/v1")