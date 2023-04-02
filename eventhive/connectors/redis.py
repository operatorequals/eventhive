import json
import time
import uuid

from ..logger import logger
from ..connectors import base

import redis

# Taken from:
# https://redis.readthedocs.io/en/latest/advanced_features.html#publish-subscribe
def exception_handler(ex, pubsub, thread):
    logger.warning("[-] Exception in Subscription thread: [%s]" % ex)
    # thread.daemon = True
    thread.stop()
    try:
        thread.join(timeout=1.0)
    except RuntimeError:
        pass
    finally:
        pubsub.close()


class RedisConnector(base.BaseConnector):

    _publishers = {}

    def __init__(self, connector_id, connector_config, global_config):
        super().__init__(connector_id, connector_config, global_config)

        logger.info("Initializing Redis Connector for '%s'" % connector_id)
        self.REDIS = redis.Redis(
            **self.conn_conf['init'],
            decode_responses=True)
        logger.info(
            "Redis Connector connected with: %s" %
            connector_config['init'])

        self.pusbsub_thread = None

        if self.conn_conf['input_channel']:
            self.subscribe()

    def publish(self, message, channel):
        assert (isinstance(message, str))
        self.REDIS.publish(channel, message)

    def subscribe(self):
        self.PUBSUB = self.REDIS.pubsub(ignore_subscribe_messages=True)
        logger.info("Redis PubSub enabled")
        self.PUBSUB.psubscribe(
            **{
                self.input_pattern + "*":
                self.read_from_pubsub
            }
        )
        self.PUBSUB.get_message()  # Defuse the subscribe response
        self.pusbsub_thread = self.PUBSUB.run_in_thread(
            exception_handler=exception_handler)
        logger.info("Subscribed to pattern: '%s'" % (self.input_pattern + "*"))

    def channels(self, pattern='*'):
        return self.REDIS.pubsub_channels(pattern)

    def stop(self):
        if self.pusbsub_thread:
            self.pusbsub_thread.stop()
        self.REDIS.close()

    def read_from_pubsub(self, message, event=None):
        event = message['channel']
        return super().read_from_pubsub(message['data'], event)
