import atexit
import unittest
import sys
import os
import time
import threading
import json
import logging

import eventhive
from eventhive.logger import logger
from eventhive.servers.fastapi_srv import FastAPIPubSubServer

import tests

logger.setLevel(logging.DEBUG)

FASTAPI_ADDRESS = ["127.0.0.1", "8085"]


class TestEvent(unittest.TestCase):

    def tearDown(self):
        time.sleep(1)
        eventhive.stop()
        for k in list(sys.modules.keys()):
            if k.startswith('eventhive'):
                sys.modules.pop(k)

    def test_secret(self, event='',
                    receiver="receiver", connector='fastapi',
                    data={'key': 'value'},
                    secret='123'
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
    secret: '%s'
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1], secret))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        output = str(output, 'utf8')
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)
        sender_thr.join()

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)

    def test_wrong_secret(self, event='',
                          receiver="receiver", connector='fastapi',
                          data={'key': 'value'},
                          secret='123'
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
    secret: '%swrongsecret'
""" % (connector, FASTAPI_ADDRESS[0], FASTAPI_ADDRESS[1], secret))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        output = str(output, 'utf8')
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)
        sender_thr.join()

        self.assertEqual({"no": "output"}, message)

    def test_no_secret(self, event='',
                       receiver="receiver", connector='fastapi',
                       data={'key': 'value'},
                       secret='123'
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
        eventhive.EVENTS.append(event_name, event)

        eventhive.init()

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-secret.yaml",
            secret=secret)
        output = str(output, 'utf8')
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)
        sender_thr.join()

        self.assertEqual({"no": "output"}, message)
