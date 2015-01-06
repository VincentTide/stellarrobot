from app import app
from flask import request, session, render_template, redirect, url_for, flash, abort
from forms import *
from models import *
from stellar_utils import *
from datetime import datetime
from sqlalchemy import desc, asc


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
                dt = generate_random_destination_tag()
                account = SendbackAccount(stellar_name=response['destination'],
                                          stellar_address=response['destination_address'],
                                          destination_tag=dt
                                          )
                db.session.add(account)
                db.session.commit()
                session['user_id'] = account.id
                return redirect(url_for('robot'))
        # Code to handle found user here
        session['user_id'] = account.id
        return redirect(url_for('robot'))
    return render_template('index.html', form=form)


@app.route('/robot', methods=['GET'])
def robot():
    if 'user_id' not in session:
        flash("Please enter a stellar username or address.")
        return redirect(url_for('index'))
    form = None
    account = SendbackAccount.query.get_or_404(session['user_id'])
    send_to = "%s&dt=%s" % (app.config['STELLAR_ADDRESS'], account.destination_tag)

    # Convert micro stellar to stellar
    received = account.transactions.order_by(desc(SendbackTransaction.created_time))
    for item in received:
        item.amount_sender = convert_stellar_for_display(item.amount_sender)
    payments = account.payables.order_by(desc(Payable.created_time))
    for item in payments:
        item.amount_fulfilled = convert_stellar_for_display(item.amount_fulfilled)

    return render_template('robot.html',
                           form=form,
                           account=account,
                           send_to=send_to,
                           received=received,
                           payments=payments)

