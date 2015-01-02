import requests
import json

URL = 'https://live.stellar.org:9002'
# URL = 'https://test.stellar.org:9002'
live_url = 'https://live.stellar.org:9002'
test_url = 'https://test.stellar.org:9002'


def create_stellar_account():
    payload = '{ "method" : "create_keys" }'
    r = requests.post(URL, payload)
    result = json.loads(r.text)
    return result


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


