# Inherit hooker API
from hooker import EVENTS, get_event_name, hook, reset, events
from hooker import logger as hooker_logger

import logging
hooker_logger.handlers = [logging.NullHandler()]

# Import config APIs
from . import config as CONFIG
from .config import CONFIG as CONFIG_DICT
from .config import PUBSUB_TYPES

from .logger import logger

from .servers import fastapi_srv
from .broadcast import Broadcast, init_from_broadcast

CONNECTORS = {}
SERVERS = {}
BROADCASTERS = {}

SERVER_CLASS = {
    'fastapi': fastapi_srv.FastAPIPubSubServer,
}


def init():
    CONFIG_DICT = CONFIG.CONFIG  # renew the config state

    # =========== Servers

    for k, v in CONFIG_DICT['servers'].items():

        if v['create'] == 'needed':
            logger.info("Detecting existing server '%s'" % k)
            init_dict = init_from_broadcast(k)
            if init_dict is None or init_dict == {}:
                logger.info("Server '%s' not detected. Creating..." % k)
                v['create'] = 'always'

        if v['create'] == 'always':
            SERVERS[k] = SERVER_CLASS[v['pubsub_type']](
                k, v, CONFIG_DICT['eventhive'])

            SERVERS[k].run_in_thread()

    # =========== Broadcast

            if v['broadcast'] == 'true' or v['broadcast']:
                BROADCASTERS[k] = Broadcast(k,
                                            v,
                                            CONFIG_DICT['eventhive'])
                BROADCASTERS[k].run_in_thread()


    # =========== Connectors

    for k, v in CONFIG_DICT['connectors'].items():

        try:
            if 'from_broadcast' in v:
                timeout = 5
                if isinstance(v['from_broadcast'], int):
                    timeout = v['from_broadcast']
                logger.info("Initializing '%s' from Broadcast" % k)
                init_dict = init_from_broadcast(k, timeout=timeout)
                if init_dict is None or init_dict == {}:
                    logger.error(
                        "Connector '%s' could not be initialized with 'from_broadcast'" %
                        k)
                    continue
                v['init'] = init_dict

            if v['pubsub_type'] == 'redis':
                from .connectors import redis as redis_class
                connector_class = redis_class.RedisConnector
            elif v['pubsub_type'] == 'fastapi':
                from .connectors import fastapi_pubsub as fastapi_class
                connector_class = fastapi_class.FastAPIPubSubConnector
            else:
                logger.error("PubSub backend: '%s' is not recognised in connector '%s'. Moving to next connector." % (
                    v['pubsub_type'], k))
                continue

            CONNECTORS[k] = connector_class(k, v, CONFIG_DICT['eventhive'])

        except Exception as e:
            logger.error("%s: Could not connect to PubSub '%s'" % (e, k))
            continue

        # connector_events = events('*/*')
        # logger.debug("Events that follow pattern '%s/*/*' (%s) will be emitted for connector %s" % (k, connector_events, k))
        # CONNECTORS[k]._publishers[k] = hook(connector_events)(
        #     lambda message: CONNECTORS[k].send_to_pubsub(message))
        CONNECTORS[k]._publishers[k] = hook(['*'])(
            lambda message: CONNECTORS[k].send_to_pubsub(message))

    if CONNECTORS == {}:
        logger.critical(
            "No Connectors could be initialized. Tried: %s. Exiting..." % (
                list(CONFIG_DICT['connectors'].keys()))
        )


def stop():
    for k, v in CONNECTORS.items():
        v.stop()
    for k, v in SERVERS.items():
        v.stop()
    for k, v in BROADCASTERS.items():
        v.stop()
