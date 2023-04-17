import json
import logging
import tracemalloc

import eventhive
from eventhive.logger import logger

import tests

logger.setLevel(logging.DEBUG)  # DEBUG


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
    from_broadcast: true # <---
""" % (connector))
        event = tests.get_function_name()
        event_name = "%s/%s/%s" % (connector, receiver, event)
        eventhive.EVENTS.append(event_name, event)

        self.sender_thr = tests.fire_later_thread_start(
            event_name, data, init=True)

        output = tests.call_eventhive_cli(
            connector,
            receiver,
            event,
            "tests/configs/server-fastapi-broadcast.yaml",
            timeout=6)

        print("OUTPUT: '%s'" % output)
        message = json.loads(output)

        self.assertTrue(
            eventhive.CONFIG_DICT['eventhive']['metadata_key'] in message)
