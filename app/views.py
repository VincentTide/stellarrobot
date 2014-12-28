from app import app
from flask import request, session, render_template, redirect, url_for, flash, abort
from forms import *
from stellar_utils import create_stellar_account
from datetime import datetime


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET'])
def index():
    form = RobotForm()
    return render_template('index.html', form=form)


@app.route('/callback', methods=['POST'])
def callback():
    data = request.data
    return render_template('raw.html', data=data)
