from __future__ import absolute_import

from proj.celery import celery
from datetime import datetime
import json
from stellar_utils import verify_txn, calculate_fee, send_payment_site_account
from app.models import *
from config import STELLAR_URL, STELLAR_ADDRESS, LOCK_EXPIRE
from app import redis


@celery.task
def add(x, y):
    result = x + y
    return result


@celery.task
def writing(x, y):
    now = datetime.utcnow()
    writer = open("/tmp/tester_celery.txt", "a")
    writer.write(str(x) + " " + str(y))
    writer.write("\n")
    writer.close()


@celery.task
def do_payable(payable_id):
    # Create locked celery job (using redis) to send payment
    k = "payable:%s" % payable_id
    if redis.setnx(k, 1):
        redis.expire(k, LOCK_EXPIRE)
        # Send the payment
        payable = Payable.query.get(payable_id)
        # Only do the payment if the payable has not been paid out already
        if payable.fulfilled is False:
            r = send_payment_site_account(payable.destination, payable.amount)
            # Check if response was success or failure
            if r['result']['status'] == 'success':
                if r['result']['engine_result_code'] == 0:
                    # payment was successful
                    tx = r['result']['tx_json']
                    payable.fulfilled = True
                    payable.account_fulfilled = tx['Account']
                    payable.amount_fulfilled = tx['Amount']
                    payable.destination_fulfilled = tx['Destination']
                    payable.fee_fulfilled = tx['Fee']
                    payable.flags_fulfilled = tx['Flags']
                    payable.sequence_fulfilled = tx['Sequence']
                    payable.signing_pub_key_fulfilled = tx['SigningPubKey']
                    payable.transaction_type_fulfilled = tx['TransactionType']
                    payable.txn_signature_fulfilled = tx['TxnSignature']
                    payable.txn_hash_fulfilled = tx['hash']
                    db.session.add(payable)
                    db.session.commit()
            else:
                # Some error happened, email admin
                pass

        # Release the redis lock after we're done
        redis.delete(k)
    else:
        # The payable is redis locked
        print "Aborting: the payable is currently locked."


@celery.task
def handle_stellar_message(message):
    # What to do when we receive a message
    # Check it is of transaction type
    m = json.loads(message)
    if m['type'] == 'transaction':
        if m['transaction']['Destination'] == STELLAR_ADDRESS and m['transaction']['TransactionType'] == 'Payment' and m['validated'] is True and m['engine_result_code'] == 0:
            # Check with stellar to make sure txn is legit
            txn_hash = m['transaction']['hash']
            ledger_index = m['ledger_index']
            r = verify_txn(txn_hash, ledger_index)
            if r['result']['status'] == 'success':
                # Check txn type and destination address
                tx = r['result']['tx_json']
                if tx['TransactionType'] == 'Payment' and tx['Destination'] == STELLAR_ADDRESS:
                    # txn has been verified, add to database
                    sender_address = tx['Account']
                    sender = SendbackAccount.query.filter_by(stellar_address=sender_address).first()
                    if sender is None:
                        sender_id = None
                    else:
                        sender_id = sender.id
                    sendback = SendbackTransaction(
                        created_time=datetime.utcnow(),
                        sendback_account=sender_id,
                        account_sender=sender_address,
                        amount_sender=tx['Amount'],
                        destination_sender=tx['Destination'],
                        destination_tag_sender=tx['DestinationTag'],
                        fee_sender=tx['Fee'],
                        flags_sender=tx['Flags'],
                        sequence_sender=tx['Sequence'],
                        signing_pub_key_sender=tx['SigningPubKey'],
                        txn_signature_sender=tx['TxnSignature'],
                        txn_hash_sender=tx['hash'],
                        ledger_index_sender=tx['ledger_index']
                    )
                    db.session.add(sendback)
                    db.session.commit()
                    # Create new Payable
                    amount_owed = sendback.amount_sender - calculate_fee(sendback.amount_sender)
                    payable = Payable(
                        created_time=datetime.utcnow(),
                        destination=sendback.account_sender,
                        amount=amount_owed,
                        fulfilled=False,
                        sendback_transaction=sendback.id
                    )
                    db.session.add(payable)
                    db.session.commit()

                    do_payable.delay(payable.id)











