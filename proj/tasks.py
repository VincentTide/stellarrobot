from __future__ import absolute_import

from proj.celery import celery
from datetime import datetime
import json
from stellar_utils import *
from app.models import *
from config import STELLAR_URL, STELLAR_ADDRESS, LOCK_EXPIRE
from app import redis
from sqlalchemy import desc, asc


@celery.task
def do_payment(pending_id):
    # Create locked celery job (using redis) to send payment
    k = "do_payment:%s" % pending_id
    if redis.setnx(k, 1):
        redis.expire(k, LOCK_EXPIRE)
        pending = PendingTransaction.query.get(pending_id)
        # Only do the task if signed is not completed already
        if pending.tx_signed is False:
            r = tx_sign(pending.destination, pending.amount, pending.sequence)
            if r['result']['status'] == 'success' and 'tx_blob' in r['result']:
                # Signing was successful
                pending.tx_blob = r['result']['tx_blob']
                pending.tx_hash = r['result']['tx_json']['hash']
                pending.tx_signed = True
                db.session.add(pending)
                db.session.commit()
                # Also save info to Payable
                payable = Payable.query.get(pending.payable)
                payable.tx_blob = pending.tx_blob
                payable.tx_hash = pending.tx_hash
                payable.tx_signed = pending.tx_signed
                db.session.add(payable)
                db.session.commit()
        if pending.tx_signed is True and pending.tx_submitted is False:
            # Check if tx has already been submitted successfully
            verify = verify_tx(pending.tx_hash)
            if verify['result']['status'] == 'success' and 'validated' in r['result']:
                if verify['result']['validated'] is True:
                    pending.tx_submitted = True
                    db.session.add(pending)
                    db.session.commit()
            else:
                r = submit_tx_blob(pending.tx_blob)
                if r['result']['status'] == 'success':
                    if r['result']['engine_result_code'] == 0:
                        # payment was successful
                        tx = r['result']['tx_json']
                        pending.tx_submitted = True
                        db.session.add(pending)
                        db.session.commit()
                        payable = Payable.query.get(pending.payable)
                        payable.tx_submitted = True
                        db.session.add(payable)
                        db.session.commit()
        if pending.tx_signed is True and pending.tx_submitted is True and pending.tx_validated is False:
            # Verify tx was confirmed and validated
            r = verify_tx(pending.tx_hash)
            if r['result']['status'] == 'success' and 'validated' in r['result']:
                if r['result']['validated'] is True:
                    # tx has been confirmed
                    tx = r['result']
                    payable = Payable.query.get(pending.payable)
                    payable.tx_validated = True
                    payable.account_fulfilled = tx['Account']
                    payable.amount_fulfilled = tx['Amount']
                    payable.destination_fulfilled = tx['Destination']
                    payable.fee_fulfilled = tx['Fee']
                    payable.flags_fulfilled = tx['Flags']
                    payable.sequence_fulfilled = tx['Sequence']
                    payable.signing_pub_key_fulfilled = tx['SigningPubKey']
                    payable.transaction_type_fulfilled = tx['TransactionType']
                    payable.tx_signature_fulfilled = tx['TxnSignature']
                    payable.tx_hash_fulfilled = tx['hash']
                    payable.ledger_index_fulfilled = tx['ledger_index']
                    db.session.add(payable)
                    db.session.commit()
                    db.session.delete(pending)
                    db.session.commit()
            else:
                # Validation typically takes 5 seconds to confirm
                # celery retry is bugging out the redis lock release
                pass

        if pending.tx_signed is True and pending.tx_submitted is True and pending.tx_validated is True:
            # If all 3 conditions are true, the pending entry should be deleted
            db.session.delete(pending)
            db.session.commit()

        # Release the redis lock after we're done working on it
        redis.delete(k)
    else:
        # The payment is redis locked
        print "Aborting: the payment is currently locked."


@celery.task
def handle_stellar_message(message):
    # What to do when we receive a message
    # Check it is of transaction type
    m = json.loads(message)
    if m['type'] == 'transaction':
        if m['transaction']['Destination'] == STELLAR_ADDRESS and m['transaction']['TransactionType'] == 'Payment' and m['validated'] is True and m['engine_result_code'] == 0:
            # Check with stellar to make sure tx is legit
            tx_hash = m['transaction']['hash']
            ledger_index = m['ledger_index']
            r = verify_tx(tx_hash, ledger_index)
            if r['result']['status'] == 'success':
                # Check tx type and destination address
                tx = r['result']['tx_json']
                if 'ledger_index' in tx and tx['TransactionType'] == 'Payment' and tx['Destination'] == STELLAR_ADDRESS:
                    # tx has been verified, add to database
                    sender_address = tx['Account']
                    sender = SendbackAccount.query.filter_by(stellar_address=sender_address).first()
                    if sender is None:
                        sender_id = None
                    else:
                        sender_id = sender.id
                    # Handle payments without destination tags
                    if 'DestinationTag' in tx:
                        dt = tx['DestinationTag']
                    else:
                        dt = None
                    sendback = SendbackTransaction(
                        created_time=datetime.utcnow(),
                        sendback_account=sender_id,
                        account_sender=sender_address,
                        amount_sender=tx['Amount'],
                        destination_sender=tx['Destination'],
                        destination_tag_sender=dt,
                        fee_sender=tx['Fee'],
                        flags_sender=tx['Flags'],
                        sequence_sender=tx['Sequence'],
                        signing_pub_key_sender=tx['SigningPubKey'],
                        tx_signature_sender=tx['TxnSignature'],
                        tx_hash_sender=tx['hash'],
                        ledger_index_sender=tx['ledger_index']
                    )
                    db.session.add(sendback)
                    db.session.commit()
                    # Create new Payable
                    amount_owed = sendback.amount_sender - calculate_fee(sendback.amount_sender)
                    dest = sendback.account_sender
                    payable = Payable(
                        created_time=datetime.utcnow(),
                        destination=dest,
                        amount=amount_owed,
                        sendback_transaction=sendback.id,
                        sendback_account=sender_id,
                        tx_signed=False,
                        tx_submitted=False,
                        tx_validated=False
                    )
                    db.session.add(payable)
                    db.session.commit()

                    seq = redis.get('Sequence')
                    redis.incr('Sequence')

                    pending = PendingTransaction(
                        payable=payable.id,
                        destination=payable.destination,
                        amount=payable.amount,
                        created_time=datetime.utcnow(),
                        tx_signed=False,
                        tx_submitted=False,
                        tx_validated=False,
                        sequence=seq
                    )
                    db.session.add(pending)
                    db.session.commit()

                    do_payment.delay(pending.id)


@celery.task
def pending_payments():
    k = "pending_payments"
    if redis.setnx(k, 1):
        pendings = PendingTransaction.query.order_by(asc(PendingTransaction.created_time)).all()
        for pending in pendings:
            do_payment(pending.id)
        # Release the redis lock after we done working
        redis.delete(k)
    else:
        print "pending_payments is redis locked."
