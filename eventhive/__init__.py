from .broadcast import Broadcast, init_from_broadcast
from .servers import fastapi_srv
from .logger import logger
from .exceptions import ConnectorInitializationException
from .config import PUBSUB_TYPES
# Import config APIs
from .config import CONFIG as CONFIG_DICT
from . import config as CONFIG
# Inherit hooker API
from hooker import EVENTS, get_event_name, reset, events
from hooker import logger as hooker_logger
from hooker import hook as hooker_hook

import logging
hooker_logger.handlers = [logging.NullHandler()]

CONNECTORS = {}
SERVERS = {}
BROADCASTERS = {}

SERVER_CLASS = {
    'fastapi': fastapi_srv.FastAPIPubSubServer,
}

def register(event, function, dependencies=None, expand=True):
    return hook(event)(function, expand=expand)

def hook(event, dependencies=None, expand=True):
    # Test if event (can be 'str' or 'iterable')
    # is totally included in created events)
    if set(event) == set(events("**")) & set(event):
        EVENTS.append(event)
    return hooker_hook(event, dependencies=dependencies, expand=expand)

def init(required=[]):
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
                logger.error("PubSub backend: '%s' is not recognised in connector '%s'." % (
                    v['pubsub_type'], k))
                raise KeyError("%s not in %s" % (v['pubsub_type'], PUBSUB_TYPES))

            CONNECTORS[k] = connector_class(k, v, CONFIG_DICT['eventhive'])

        except Exception as e:
            logger.error("%s: Could not connect to PubSub '%s'" % (e, k))
            if k in required:
                raise ConnectorInitializationException("Connector '%s' is required." % k)
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
