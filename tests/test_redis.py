import docker
import atexit
import logging
import json

import eventhive
from eventhive.logger import logger

import tests

logger.setLevel(logging.DEBUG)  # DEBUG

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


class TestEvent(tests.TestEventhive):

    def setUp(self):
        REDIS_CONTAINER.start()

    def tearDown(self):
        super().tearDown()
        REDIS_CONTAINER.stop()

    def test_subscription(self, event='',
                          receiver="receiver", connector='redis',
                          data={'key': 'value'}
                          ):
        eventhive.CONFIG.read_string("""
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
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/receiver-redis.yaml")
        print("OUTPUT: " + output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)

    def test_no_metadata(self, event='',
                         receiver="receiver", connector='redis',
                         data={'key': 'value'}
                         ):
        eventhive.CONFIG.read_string("""
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
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/receiver-redis.yaml")
        print("OUTPUT: " + output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] not in message)
