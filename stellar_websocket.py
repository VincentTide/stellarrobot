import websocket
import json
from proj.tasks import handle_stellar_message
from config import STELLAR_WS, STELLAR_ADDRESS


def on_message(ws, message):
    print message
    handle_stellar_message.delay(message)


def on_error(ws, error):
    print error


def on_close(ws):
    print "WebSocket closed."


def on_open(ws):
    payload = """
{
  "command": "subscribe",
  "id": "1",
  "accounts": [
    "%s"
  ]
}
""" % STELLAR_ADDRESS
    ws.send(payload)
    print "WebSocket connected."


if __name__ == "__main__":
    ws = websocket.WebSocketApp(STELLAR_WS,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever(ping_interval=180)
