import sys
import os
import time
import json
import argparse

import eventhive
from .logger import logger
import logging
logger.addHandler(logging.StreamHandler(sys.stderr))

DEFAULT_OUTPUT = '{"no":"output"}'
RECEIVED = DEFAULT_OUTPUT


def main():
    parser = argparse.ArgumentParser(
        description='The Swiss-Army knife for Eventhive',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        '--network',
        default='eventhive',
        help='The Eventhive Network of Events (<here>/*/*)')
    parser.add_argument(
        '--receiver',
        default='cli',
        help='The Eventhive Channel of Events (*/<here>/*)')
    parser.add_argument(
        '--event',
        default='do',
        help='The Eventhive Event Name (*/*/<here>)')
    parser.add_argument(
        '--json-data',
        default=False,
        help='If set - the JSON will be sent to "<network>/<receiver>/<event>"',
        type=json.loads)
    parser.add_argument(
        '--target-event',
        default=None,
        help='If set - the JSON defined in "--json-data" will be published on it instead of "<network>/<receiver>/<event>"')
    parser.add_argument(
        '--json-fallback',
        default=DEFAULT_OUTPUT,
        help='The JSON to print to STDOUT if no data is received in "<network>/<receiver>/<event>"')
    parser.add_argument(
        '--config',
        default='.eventhive-config.yaml',
        type=argparse.FileType(),
        help='The Configuration file to be used by Eventhive (can include formatting)')
    parser.add_argument(
        '--timeout',
        default=6,
        type=int,
        help='Time to run before exiting and printing to STDOUT')
    parser.add_argument(
        '--secret',
        default=None,
        help='A secret string used for signing and encryption of messages')
    parser.add_argument(
        '--debug',
        '-d',
        default=logging.WARNING,
        help="When set - full DEBUG logs will be printed",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )
    parser.add_argument(
        '--verbose',
        '-v',
        help="When set - INFO logs will be printed",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
    )

    args = parser.parse_args()
    logger.setLevel(args.loglevel)

    try:
        conf_str = args.config.read().format(
            receiver=args.receiver,
            network=args.network,
            secret=args.secret,
        )
        eventhive.CONFIG.read_string(conf_str)
    except KeyError as e:
        print('[CLI] Configuration exception %s' % e)

    event_name = "%s/%s" % (
        args.receiver,
        args.event,)

    eventhive.EVENTS.append(event_name)

    print("[CLI] Waiting for: '%s'" % event_name, file=sys.stderr)

    @eventhive.hook(event_name)
    def output(message):
        global RECEIVED
        RECEIVED = json.dumps(message)
        print("[CLI] Received: '%s'" % RECEIVED, file=sys.stderr)

    if args.json_data:
        target_event = args.target_event
        if target_event is None:
            target_event = "%s/%s/%s" % (
                args.network,
                args.receiver,
                args.event
            )
        eventhive.EVENTS.append(target_event)

    eventhive.init()

    time.sleep(1)  # minimum setup

    time.sleep(args.timeout / 2)

    if args.json_data:
        print("[CLI] Publishing to '%s': '%s'" % (
            target_event, args.json_data), file=sys.stderr)
        eventhive.EVENTS.call(target_event, args.json_data)

    time.sleep(args.timeout / 2)

    eventhive.stop()
    print(RECEIVED)  # This will be captured and decoded in the calling code
    sys.exit(1 if RECEIVED == args.json_fallback else 0)


if __name__ == '__main__':
    main()
