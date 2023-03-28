import os
import sys
import subprocess
import logging

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
    process = subprocess.run(comm, check=False, capture_output=True)
    print()
    print("==> " + " ".join(comm))
    print(str(process.stderr, 'utf8'))
    print()
    return process.stdout


def fire_later(event, data, sec=3):
    time.sleep(sec)
    eventhive.EVENTS[event](data)
    print("[Sender] Event '%s' sent" % event)


def get_function_name():
    return sys._getframe(1).f_code.co_name
