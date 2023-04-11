import json
import logging

import eventhive
from eventhive.logger import logger

import tests

logger.setLevel(logging.DEBUG)

FASTAPI_ADDRESS = ["127.0.0.1", "8085"]


class TestEvent(tests.TestEventhive):

    def test_secret(self, event='',
                    receiver="receiver", connector='fastapi',
                    data={'key': 'value'},
                    secret='123'
                    ):
        eventhive.CONFIG.read_string("""
connectors:
  %s:
    pubsub_type: fastapi
    input_channel: ''
    init:
      host: %s
      port: %s
    secret: '%s'
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1], secret))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)

    def test_wrong_secret(self, event='',
                          receiver="receiver", connector='fastapi',
                          data={'key': 'value'},
                          secret='123'
                          ):
        eventhive.CONFIG.read_string("""
connectors:
  %s:
    pubsub_type: fastapi
    input_channel: ''
    init:
      host: %s
      port: %s
    secret: '%swrongsecret'
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1], secret))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)

        self.assertEqual({"no": "output"}, message)

    def test_no_secret(self, event='',
                       receiver="receiver", connector='fastapi',
                       data={'key': 'value'},
                       secret='123'
                       ):
        eventhive.CONFIG.read_string("""
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
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        self.sender_thr = tests.fire_later_thread_start(event_name, data)

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)

        self.assertEqual({"no": "output"}, message)
