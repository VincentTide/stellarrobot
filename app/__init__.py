from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.moment import Moment
from flask.ext.script import Manager
from redis import Redis

app = Flask(__name__)
app.config.from_object('config')

# Make sure we declare db first before importing views or models
db = SQLAlchemy(app)

# Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Extensions initialization
moment = Moment(app)
manager = Manager(app)

# Redis
redis = Redis('localhost')

# Import views at the end
from app import views
