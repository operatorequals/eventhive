import json
import logging

import eventhive
from eventhive.logger import logger

import tests

logger.setLevel(logging.DEBUG)  # DEBUG

FASTAPI_ADDRESS = ["127.0.0.1", "8085"]


class TestEvent(tests.TestEventhive):

    def test_subscription(self, event='',
                          receiver="receiver", connector='fastapi',
                          data={'key': 'value'}
                          ):
        eventhive.CONFIG.read_string(
            """
connectors:
  %s:
    pubsub_type: fastapi
    input_channel: ''
    init:
      host: %s
      port: %s
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1]))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, "test subscription")

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/server-fastapi.yaml")
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)

    def test_no_metadata(self, event='',
                         receiver="receiver", connector='fastapi',
                         data={'key': 'value'}
                         ):
        eventhive.CONFIG.read_string(
            """
eventhive:
  remove_metadata: true
connectors:
  %s:
    pubsub_type: fastapi
    input_channel: ''
    init:
      host: %s
      port: %s
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1]))

        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, "test no metadata")

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/server-fastapi.yaml")
        print("OUTPUT: " + output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] not in message)
