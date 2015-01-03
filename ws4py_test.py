from ws4py.client.threadedclient import WebSocketClient
import json


class DummyClient(WebSocketClient):
    def opened(self):
        print "WebSocket Opened."
        self.send("TESTING123")
#         payload = """
# {
#   "command": "subscribe",
#   "id": 101,
#   "accounts": [
#     "g9cjuzVu98ktpjuaNo8VsbZpPB1ATUuyJv"
#   ]
# }
# """
#         self.send(payload)


    def closed(self, code, reason=None):
        print "Closed down", code, reason

    def received_message(self, m):
        # prettyprint = json.dumps(str(m), indent=4)
        # print prettyprint
        print m


if __name__ == '__main__':
    try:
        ws = DummyClient('ws://echo.websocket.org/')
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()