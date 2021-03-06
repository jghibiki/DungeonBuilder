from autobahn.asyncio.websocket import WebSocketClientProtocol
from autobahn.asyncio.websocket import WebSocketClientFactory

import log
import os
import json
import random
import string

log = log.logger

class BroadcastClientProtocol(WebSocketClientProtocol):

    def __init__(self, *args, **kwargs):
        super(WebSocketClientProtocol, self).__init__(*args, **kwargs)

        self.clients = []
        self.id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))

    def onOpen(self):
        log.info("Server connection open")
        self.factory._registerClient(self)
        for cb in self.factory.connect_hooks:
            cb()

    def onConnect(self, client):
        log.info("Server connecting: {}".format(client.peer))
        self.clients.append(client)


    def onMessage(self, payload, isBinary):

        # deserialize json
        obj = json.loads(payload.decode("utf8"))

        if obj["type"] != "pong":
            log.info(("Incoming Message: ", obj["type"], obj["key"] if "key" in obj else None))

        if(obj["type"] == "pong"):
            log.debug("Pong!");

        elif obj["type"] == "error":
            log.error("Communication Error: {}".format(obj["msg"]))

        elif((obj["type"] == "broadcast_target" or obj["type"] == "broadcast") and obj["key"] != "bulk"):
            log.info("Handling: " + obj["key"])
            for handler in self.factory._get_subscribers(obj["key"]):
                handler(obj)

        elif(obj["type"] == "command" and obj["key"] == "bulk"):
            if "frames" in obj:
                for frame in obj["frames"]:
                    for handler in self.factory._get_subscribers(obj["key"]):
                        handler(frame)

    def connectionLost(self, reason):
        WebSocketClientProtocol.connectionLost(self, reason)
        self.factory._unregisterClient(self)
        log.warn("Connection lost. Reason: {}".format(reason))

    def onClose(self, wasClean, code, reason):
        log.warn("Connection closed. Reason: {}".format(reason))

    def register(self, id):
        self.clients.append(id)

    def broadcast(self, payload):
        self.send(payload, type="broadcast")


    def prepairSend(self, payload, broadcast=False):
        payload["password"] = "1111" #TODO add a better way to set password
        payload["id"] = self.id

        payload["broadcast"] = broadcast

        log.info(("Sending message: ", payload["type"], payload["key"] if "key" in payload else None))
        return payload


    def sendBulk(self, payloads, broadcast=False):
        prepared_payloads = []

        for load in payloads:
            prepared_payloads.append(
                    self.prepairSend(load) )

        payload = {
            "type": "command",
            "key" : "bulk",
            "frames": prepared_payloads
        }
        self.send(payload, broadcast)

    def send(self, payload,broadcast=False):
        payload = self.prepairSend(payload, broadcast)
        payload = json.dumps(payload, ensure_ascii=False).encode("utf8")
        self.sendMessage(payload)


    def ping(self):
        log.debug("Ping!")
        self.send({"type": "ping"})


class MagicBroadcastClientFactory(WebSocketClientFactory):

    protocol = BroadcastClientProtocol

    def __init__(self):
        WebSocketClientFactory.__init__(self)
        self.client = None

        self.subscriptions = {
            "list.maps": [],

            "add.map": [],
            "get.map": [],

            "get.map.fow": [],
            "remove.map.fow": [],
            "add.map.fow": [],

            "get.map.units": [],
            "add.map.unit": [],
            "remove.map.unit": [],
            "modify.map.unit": [],
            "export.map.unit": [],

            "get.chat": [],
            "add.chat.message": [],

            "get.users": [],

            "get.config": []

        }
        self.connect_hooks = []


    def _registerClient(self, client):
        self.client = client

    def _unregisterClient(self, client):
        self.client = None

    def send(self, payload, broadcast=False):
        if self.client:
            self.client.send(payload, broadcast)
        else:
            log.warn("Attempted to send when no client connection has been established.")

    def sendBulk(self, payload, broadcast=False):
        if self.client:
            self.client.sendBulk(payload, broadcast)
        else:
            log.warn("Attempted to send when no client connection has been established.")

    def ping(self):
        if self.client:
            self.client.ping()
        else:
            log.debug("Attempted to send ping when no client connection has been established.")

    def subscribe(self, channel, callback):
        if channel not in self.subscriptions:
            log.warn("Invalid channel name \"{}\". Subscription failed.".format(channel))
        else:
            self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel, callback):
        if channel not in self.subscriptions:
            log.warn("Invalid channel name \"{}\". Unsubscribe failed.".format(channel))
        else:
            for cb in self.subscriptions[channel]:
                if cb == callback:
                    self.subscriptions[channel].remove(cb)

    def register_connect_hook(self, callback):
        self.connect_hooks.append(callback)

    def _get_subscribers(self, channel):
        if channel not in self.subscriptions:
            log.error("Attempted to handle undefined subscription type: {}".format(channel))
            return None
        return self.subscriptions[channel]


def start_client(host, port, viewer):

    try:
       import asyncio
    except ImportError:
       ## Trollius >= 0.3 was renamed
       import trollius as asyncio


    factory = MagicBroadcastClientFactory()

    loop = asyncio.get_event_loop()

    viewer.setLoop(loop)
    viewer.setClient(factory)
    loop.call_soon(viewer.tick)

    coro = loop.create_connection(factory, host, port)
    server = loop.run_until_complete(coro)

    try:
       loop.run_forever()
    except KeyboardInterrupt:
       pass
    finally:
       loop.close()
