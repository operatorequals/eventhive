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
    from_broadcast: true # <---
""" % (connector))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, "test subscription")

        sender_thr = threading.Thread(
            target=lambda: eventhive.init() or tests.fire_later(
                event_name, data))

        sender_thr.daemon = True
        sender_thr.start()

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-broadcast.yaml",
            timeout=6)

        output = str(output, 'utf8')
        print("OUTPUT: '%s'" % output)
        message = json.loads(output)
        sender_thr.join()

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)
