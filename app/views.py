from app import app
from flask import request, session, render_template, redirect, url_for, flash, abort
from forms import *
from models import *
from stellar_utils import create_stellar_account, stellar_name_lookup, stellar_address_lookup
from datetime import datetime


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    form = RobotForm()
    return render_template('index.html', form=form)


@app.route('/', methods=['POST'])
@app.route('/index', methods=['POST'])
def index_post():
    form = RobotForm()
    if form.validate_on_submit():
        # Check if username or address exist
        name_or_address = form.name_or_address.data.strip()
        found = False
        account = SendbackAccount.query.filter_by(stellar_name=name_or_address).first()
        if account is None:
            account = SendbackAccount.query.filter_by(stellar_address=name_or_address).first()
            if account is None:
                # Create new Account
                # Find username and address from stellar.org
                response = stellar_name_lookup(name_or_address)
                if response is None:
                    response = stellar_address_lookup(name_or_address)
                    if response is None:
                        flash("Could not find name or address in stellar.org")
                        return render_template('index.html', form=form)
                account = SendbackAccount(stellar_name=response['destination'],
                                          stellar_address=response['destination_address'],
                                          )
                db.session.add(account)
                db.session.commit()
                account.destination_tag = account.id
                db.session.add(account)
                db.session.commit()
                return redirect(url_for('robot', user_id=account.id))
        # Code to handle found user here
        return redirect(url_for('robot', user_id=account.id))
    return render_template('index.html', form=form)


@app.route('/robot/<user_id>', methods=['GET'])
def robot(user_id):
    form = None
    account = SendbackAccount.query.get_or_404(user_id)
    send_to = "%s&dt=%s" % (app.config['STELLAR_ADDRESS'], account.destination_tag)

    return render_template('robot.html', form=form, account=account, send_to=send_to)

