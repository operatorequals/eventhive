import os
import sys
import subprocess
import logging
import threading
import unittest

import eventhive
import time

from eventhive import logger

logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stderr))


def call_eventhive_cli(network, receiver, event, config, timeout=6, secret=''):
    os.environ['PYTHONPATH'] = "%s/../" % os.path.dirname(
        os.path.abspath(__file__))
    comm = [
        "python", "-m", "eventhive.cli",
        "--config", config,  # "tests/receivers/receiver-fastapi.yaml",
        "--timeout", str(timeout),
        "--network", network,
        "--receiver", receiver,
        "--event", event,
        "--secret", secret,
        "--debug",
    ]
    print()
    print("==> " + " ".join(comm))
    process = subprocess.run(comm, check=False, capture_output=True)
    print(str(process.stderr, 'utf8'))
    print()
    return str(process.stdout, 'utf8').strip()


def fire_later(event, data, timeout=3, expand=False):
    time.sleep(timeout)
    eventhive.EVENTS.call(event, data, expand=expand)
    print("[Sender] Event '%s' sent %s" % (
        event,
        "- with expansion" if expand else "")
    )


def fire_later_thread_start(event, data, timeout=3, expand=False, init=False):
    if not init:
        sender_thr = threading.Thread(
            target=fire_later,
            args=(event, data, timeout, expand)
        )
    else:
        sender_thr = threading.Thread(
            target=lambda: eventhive.init() or fire_later(
                event, data, timeout, expand)
        )

    sender_thr.daemon = True
    sender_thr.start()
    return sender_thr


def get_function_name():
    return sys._getframe(1).f_code.co_name


class TestEventhive(unittest.TestCase):

    def tearDown(self):
        self.sender_thr.join()
        time.sleep(1)
        eventhive.stop()
        # for k in list(sys.modules.keys()):
        #     if k.startswith('eventhive'):
        #         sys.modules.pop(k)
