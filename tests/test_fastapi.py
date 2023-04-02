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
from eventhive.servers.fastapi_srv import FastAPIPubSubServer

import tests

logger.setLevel(0)  # DEBUG

FASTAPI_ADDRESS = ["127.0.0.1", "8085"]


class TestEvent(unittest.TestCase):

    def tearDown(self):
        time.sleep(1)
        eventhive.stop()
        for k in list(sys.modules.keys()):
            if k.startswith('eventhive'):
                sys.modules.pop(k)

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

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/server-fastapi.yaml")
        output = str(output, 'utf8')
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)
        sender_thr.join()

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

        sender_thr = threading.Thread(
            target=tests.fire_later,
            args=(event_name, data)
        )

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector, receiver, event, "tests/configs/server-fastapi.yaml")
        output = str(output, 'utf8')
        print("OUTPUT: " + output)
        message = json.loads(output)
        sender_thr.join()

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] not in message)
