from ..logger import logger
from ..connectors import base
import eventhive

import concurrent.futures
import threading
from fastapi_websocket_pubsub import PubSubClient
import asyncio
import logging
import os
import sys
import json


sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.basename(__file__),
            "..")))


class FastAPIPubSubConnector(base.BaseConnector):

    _publishers = {}

    def __init__(self, connector_id, connector_config, global_config):
        super().__init__(connector_id, connector_config, global_config)
        logger.info(
            "Initializing FastAPI PubSub Connector for '%s'" %
            connector_id)

        host = self.conn_conf['init'].get("host", "127.0.0.1")
        port = self.conn_conf['init'].get("port", 8085)
        endpoint = self.conn_conf['init'].get("endpoint", "/pubsub")
        endpoint = endpoint if endpoint.startswith('/') else '/' + endpoint
        url_scheme = self.conn_conf['init'].get("scheme", "ws")
        self.url = "{}://{}:{}{}".format(
            url_scheme, host, port,
            endpoint,
        )
        logger.info("FastAPI PubSub Connector initialized with: %s" % self.url)

        if self.conn_conf['input_channel']:
            self.subscribe()

    def _get_channels_to_subscribe(self):
        ret = []
        for event in eventhive.EVENTS._events:
            if event.startswith(self.conn_conf['input_channel']):
                ret.append(event)
        return ret

    async def _subscriber_async(self, channels):
        self.SUBSCRIBER = PubSubClient(
            channels,
            callback=lambda data=None,
            topic=None: self.read_from_pubsub(
                '{}' if data is None else data,
                channel=topic))
        self.SUBSCRIBER.start_client(self.url)

    def subscribe(self, channels=[]):
        logger.info("FastAPI PubSub enabled")
        channels = self._get_channels_to_subscribe() if channels == [] else channels
        channels = [
            "%s%s%s" %
            (self.conn_id,
             self.global_conf['channel_separator'],
             c) for c in channels]
        self.SUBSCRIBER_LOOP = asyncio.new_event_loop()
        asyncio.run_coroutine_threadsafe(self._subscriber_async(channels),
                                         self.SUBSCRIBER_LOOP)
        self.SUBSCRIBER_THREAD = threading.Thread(
            target=self.SUBSCRIBER_LOOP.run_forever)
        self.SUBSCRIBER_THREAD.daemon = True
        self.SUBSCRIBER_THREAD.start()
        logger.info("Subscribed to channels: %s" % (channels))

    async def _publish_async(self, data, channel):
        publisher = PubSubClient()
        publisher.start_client(self.url)
        await publisher.wait_until_ready()
        await publisher.publish([channel], data=data, sync=True)
        await publisher.disconnect()

    def publish(self, message, channel):
        loop = asyncio.new_event_loop()
        asyncio.run_coroutine_threadsafe(
            self._publish_async(message, channel), loop)
        publisher_thread = threading.Thread(target=loop.run_forever)
        publisher_thread.daemon = True
        publisher_thread.start()

    async def read_from_pubsub(self, message, channel=None):
        super().read_from_pubsub(message, channel)

    def stop(self):
        pass
