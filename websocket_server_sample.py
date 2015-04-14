#!/usr/bin/env python
# -*- coding: utf-8 -*-

# python libraries
import sys
import logging
import threading

# pypi libraries
from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File
from autobahn.util import newid
from autobahn.twisted.websocket import (
    WebSocketServerFactory,
    WebSocketServerProtocol
)
from autobahn.twisted.resource import (
    WebSocketResource,
    HTTPChannelHixie76Aware
)

# create logger
logger = logging.getLogger(__file__)


class MyWebSocketServerProtocol(WebSocketServerProtocol):
    """ MyWebSocketServerProtoco class """
    def onConnect(self, request):
        logger.info('connected')
        self.session_id = newid()

    def onOpen(self):
        logger.info('open websocket')
        self.factory.register_session(self)

    def onClose(self, wasClean, code, reason):
        logger.info('close websocket. code:%d reason:%s', code, reason)
        self.factory.unregister_session(self)

    def connectionLost(self, reason):
        logger.debug('connection lost')
        self.factory.unregister_session(self)

    def onMessage(self, payload, isBinary):
        logger.debug('receive message')
        self.factory.add_recv_packet(payload, isBinary, self.session_id)


class MyWebSocketServerFactory(WebSocketServerFactory):
    """ MyWebSocketServerFactory class """

    def __init__(self, uri, debug):
        WebSocketServerFactory.__init__(self, uri, debug=debug)
        self._session_id_list = []
        self._clients = {}

    def add_recv_packet(self, packet, is_binary, session_id):
        """ add data to data que

        :param packet:
        :param is_binary:
        :param session_id:
        """
        if session_id in self._session_id_list:
            # check primary session
            pass
        else:
            logger.debug('target session [%s] is not found.', session_id)

    def register_session(self, session):
        """ register new session

        :param session_id:
        """
        session_id = session.session_id
        logger.info('add session [%s]', session_id)

        # add data que for this session
        self._session_id_list.append(session_id)
        self._clients[session_id] = session

    def unregister_session(self, session):
        """ delete session id

        :session_id:
        """
        session_id = session.session_id
        logger.info('delete session [%s]', session_id)
        self._session_id_list = [id for id in self._session_id_list if id != session_id]
        del self._clients[session_id]

    def send_packet(self, packet):
        """ add send packet by protocol class

        :packet:
        """
        for client in self._clients.values():
            client.sendMessage(packet, isBinary=True)


class MyWebSocketServer(object):
    """ MyWebSocketServer class """
    def __init__(self, host, port, debug=False):
        """ init function """
        self._thread = None
        self._factory = None
        self._resource = None
        self._host = host
        self._port = port
        self._url = 'ws://{host}:{port}'.format(
            host=host,
            port=port
        )
        self._debug = debug

    def start(self):
        """ start websocket server """
        logger.info('start websocket server at %s', self._url)
        self._factory = MyWebSocketServerFactory(
            self._url,
            debug=self._debug
        )

        self._factory.protocol = MyWebSocketServerProtocol
        self._factory.setProtocolOptions(allowHixie76=True)

        self._resource = WebSocketResource(self._factory)

        # we server static files under "/" ..
        root = File('.')

        # and our WebSocket server under "/websocket"
        root.putChild('websocket', self._resource)

        # both under one Twisted Web Site
        site = Site(root)
        site.protocol = HTTPChannelHixie76Aware
        reactor.listenTCP(self._port, site)
        self._thread = threading.Thread(target=reactor.run, args=(False,))
        self._thread.start()

    def stop(self):
        """ stop websocket server
        """
        reactor.stop()
        self._thread.join(0.1)

    def send_packet(self, packet):
        """ notify connected
        """
        self._factory.send_packet(packet)


def main():
    server = MyWebSocketServer(
        host='127.0.0.1',
        port=9000,
        debug=True
    )
    server.start()

    try:
        while True:
            time.sleep(1)
    except:
        pass
    finally:
        server.stop()
    return 1

if __name__ == '__main__':
    sys.exit(main())

