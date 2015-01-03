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

                    # Create locked celery job (using redis) to send payment
                    k = "payable:%s" % payable.id
                    redis.setex(k, 1, LOCK_EXPIRE)
                    # Send the payment
                    response = send_payment_site_account(payable.destination, payable.amount)
                    print response
                    # Check if response was success or failure








