import docker
from importlib import reload
import atexit
import unittest
import sys
import os
import time
import threading
import json

import eventhive
from eventhive.logger import logger

import tests

logger.setLevel(0)  # DEBUG

# Setup Docker ==============================

DOCKER = docker.from_env()
REDIS_CONTAINER_NAME = "eventhive-test-redis"
REDIS_ADDRESS = ("127.0.0.1", "6379")

try:
    REDIS_CONTAINER = DOCKER.containers.get(REDIS_CONTAINER_NAME)
except docker.errors.NotFound:
    REDIS_CONTAINER = DOCKER.containers.create(
        "redis",
        name=REDIS_CONTAINER_NAME,
        ports={"6379/tcp": REDIS_ADDRESS},
    )
atexit.register(REDIS_CONTAINER.remove)
# ===========================================


class TestEvent(unittest.TestCase):
    def setUp(self):
        REDIS_CONTAINER.start()

    def tearDown(self):
        time.sleep(1)
        eventhive.stop()
        for k in list(sys.modules.keys()):
            if k.startswith('eventhive'):
                sys.modules.pop(k)
        REDIS_CONTAINER.stop()

    def test_subscription(self, event='',
                          receiver="receiver", connector='redis',
                          data={'key': 'value'}
                          ):
        eventhive.CONFIG.read_string(
            """
connectors:
  %s:
    pubsub_type: redis
    input_channel: ''
    init:
      host: %s
      port: %s
      db: 0
""" % (connector, REDIS_ADDRESS[0], REDIS_ADDRESS[1]))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, "test subscription")

        eventhive.init()

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()
        # sender_thr.join()

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/receiver-redis.yaml")
        output = str(output, 'utf8')
        print("OUTPUT: " + output)
        message = json.loads(output)
        # sender_thr.join()

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)

    def test_no_metadata(self, event='',
                         receiver="receiver", connector='redis',
                         data={'key': 'value'}
                         ):
        eventhive.CONFIG.read_string(
            """
eventhive:
  remove_metadata: true
connectors:
  %s:
    pubsub_type: redis
    input_channel: ''
    init:
      host: %s
      port: %s
      db: 0
""" % (connector, REDIS_ADDRESS[0], REDIS_ADDRESS[1]))

        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, "test no metadata")

        eventhive.init()

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()
        # sender_thr.join()

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/receiver-redis.yaml")
        output = str(output, 'utf8')
        print("OUTPUT: " + output)
        message = json.loads(output)
        # sender_thr.join()

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] not in message)
