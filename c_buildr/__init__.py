from flask import Flask

from .config import (
    CLOUD_SQL_CONNECTION_NAME,
    CLOUD_SQL_DATABASE_NAME,
    CLOUD_SQL_PASSWORD,
    CLOUD_SQL_USERNAME,
    SQLALCHEMY_DATABASE_URI,
)

# import flask_login
from flask_login import LoginManager
# from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# app.config["SECRET_KEY"] = SECRET_KEY
app = Flask(__name__)
CORS(app)
# Enter your database connection details below
# app.config['MYSQL_HOST'] = CLOUD_SQL_HOST
app.config["MYSQL_USER"] = CLOUD_SQL_USERNAME
app.config["MYSQL_PASSWORD"] = CLOUD_SQL_PASSWORD
app.config["MYSQL_DB"] = CLOUD_SQL_DATABASE_NAME
app.config["MYSQL_CONNECTION_NAME"] = CLOUD_SQL_CONNECTION_NAME
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# db migrations
# db.init_app(app)
migrate = Migrate(app,db)

# db = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI)
login_manager = LoginManager()
login_manager.init_app(app)
