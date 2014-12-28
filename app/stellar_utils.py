import requests
import json

#URL = 'https://live.stellar.org:9002'
URL = 'https://test.stellar.org:9002'


def create_stellar_account():
    payload = '{ "method" : "create_keys" }'
    r = requests.post(URL, payload)
    result = json.loads(r.text)
    return result