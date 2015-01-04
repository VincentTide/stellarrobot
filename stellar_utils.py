import requests
import json
from config import STELLAR_URL, FEE_PERCENT, STELLAR_ADDRESS, STELLAR_SECRET_KEY
from app.models import *
import random


def create_stellar_account():
    payload = '{ "method" : "create_keys" }'
    r = requests.post(STELLAR_URL, payload)
    result = json.loads(r.text)
    return result


def generate_random_destination_tag():
    # Generate dest tags with 6 digits
    dt = random.randrange(1, 1000000)
    # Check to make sure its unique among SendbackAccounts
    found = SendbackAccount.query.filter_by(destination_tag=dt).first()
    while found is not None:
        dt = random.randrange(1, 1000000)
        found = SendbackAccount.query.filter_by(destination_tag=dt).first()
    return dt


def stellar_name_lookup(address):
    url = 'https://api.stellar.org/reverseFederation'
    payload = {
        "domain": "stellar.org",
        "destination_address": address
    }
    r = requests.get(url, params=payload)
    response = json.loads(r.text)
    if 'result' in response:
        if response['result'] == 'error':
            return None
    if 'federation_json' in response:
        return response['federation_json']


def stellar_address_lookup(name):
    url = 'https://api.stellar.org/federation'
    payload = {
        "domain": "stellar.org",
        "destination": name
    }
    r = requests.get(url, params=payload)
    response = json.loads(r.text)
    if 'result' in response:
        if response['result'] == 'error':
            return None
    if 'federation_json' in response:
        return response['federation_json']


def verify_txn(txn_hash, ledger_index=None):
    if ledger_index is None:
        payload = """
{
  "method": "tx",
  "params": [
    {
      "transaction": "%s"
    }
  ]
}
""" % txn_hash
    else:
        payload = """
{
  "method": "transaction_entry",
  "params": [
    {
      "tx_hash": "%s",
      "ledger_index": %s
    }
  ]
}
""" % (txn_hash, ledger_index)
    resp = requests.post(STELLAR_URL, payload)
    r = json.loads(resp.text)
    return r


def calculate_fee(amount):
    return amount * float(FEE_PERCENT)


def send_payment(sender, destination, amount, secret, destination_tag=None):
    if destination_tag is None:
        payload = """
{
  "method": "submit",
  "params": [
    {
      "secret": "%s",
      "tx_json": {
        "TransactionType": "Payment",
        "Account": "%s",
        "Destination": "%s",
        "Amount": "%s"
      }
    }
  ]
}
""" % (secret, sender, destination, amount)
    else:
        payload = """
{
  "method": "submit",
  "params": [
    {
      "secret": "%s",
      "tx_json": {
        "TransactionType": "Payment",
        "Account": "%s",
        "Destination": "%s",
        "Amount": "%s",
        "DestinationTag": "%s",
      }
    }
  ]
}
""" % (secret, sender, destination, amount, destination_tag)
    resp = requests.post(STELLAR_URL, payload)
    r = json.loads(resp.text)
    return r


def send_payment_site_account(destination, amount, destination_tag=None):
    if destination_tag is None:
        payload = """
{
  "method": "submit",
  "params": [
    {
      "secret": "%s",
      "tx_json": {
        "TransactionType": "Payment",
        "Account": "%s",
        "Destination": "%s",
        "Amount": "%s"
      }
    }
  ]
}
""" % (STELLAR_SECRET_KEY, STELLAR_ADDRESS, destination, amount)
    else:
        payload = """
{
  "method": "submit",
  "params": [
    {
      "secret": "%s",
      "tx_json": {
        "TransactionType": "Payment",
        "Account": "%s",
        "Destination": "%s",
        "Amount": "%s",
        "DestinationTag": "%s"
      }
    }
  ]
}
""" % (STELLAR_SECRET_KEY, STELLAR_ADDRESS, destination, amount, destination_tag)
    resp = requests.post(STELLAR_URL, payload)
    r = json.loads(resp.text)
    return r
