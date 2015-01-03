from ws4py.client.geventclient import WebSocketClient
import gevent

ws = WebSocketClient('ws://echo.websocket.org/')
ws.connect()


def incoming():
    """
    Greenlet waiting for incoming messages
    until ``None`` is received, indicating we can
    leave the loop.
    """
    while True:
        m = ws.receive()
        if m is not None:
            print str(m)
        else:
            break


def send_a_bunch():
    for i in range(0, 40, 5):
        ws.send("*" * i)

ws.send("TESTING123")
greenlets = [
    gevent.spawn(incoming),
    gevent.spawn(send_a_bunch),
]
gevent.joinall(greenlets)
ws.send("TESTING123")
