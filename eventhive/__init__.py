# Inherit hooker API
from hooker import EVENTS, get_event_name, hook, reset, events

# Import config APIs
from . import config as CONFIG
from .config import CONFIG as CONFIG_DICT
from .config import PUBSUB_TYPES

from .logger import logger
try:
    from .connectors import redis as redis_class
except ImportError:
    logger.warning("'redis' is not available. If needed, install with 'pip install eventhive[redis]'")
    redis_class = None

from .connectors import fastapi_pubsub as fastapi_class

from .servers import fastapi_srv

from .broadcast import Broadcast, init_from_broadcast

CONNECTORS = {}
SERVERS = {}
BROADCASTERS = {}

CONNECTOR_CLASS = {
    'redis': redis_class.RedisConnector if redis_class != None else None,
    'fastapi': fastapi_class.FastAPIPubSubConnector
}

SERVER_CLASS = {
    'fastapi': fastapi_srv.FastAPIPubSubServer
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

            CONNECTORS[k] = CONNECTOR_CLASS[v['pubsub_type']](
                k, v, CONFIG_DICT['eventhive'])
        except Exception as e:
            logger.error("%s: Could not connect to PubSub '%s'" % (e, k))
            continue

        CONNECTORS[k]._publishers[k] = hook(
            CONFIG_DICT['connectors'][k]['channels'])(
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
