# Inherit hooker API
from hooker import EVENTS, get_event_name, hook, reset, events

# Import config APIs
from eventhive import config as CONFIG
from eventhive.config import CONFIG as CONFIG_DICT
from eventhive.config import PUBSUB_TYPES

from eventhive.logger import logger
import eventhive.connectors.redis as redis_class
import eventhive.connectors.fastapi_pubsub as fastapi_class

import eventhive.servers.fastapi_srv as fastapi_srv

from eventhive.zeroconf.broadcast import Broadcast, init_from_broadcast

CONNECTORS = {}

SERVERS = {}
BROADCASTERS = {}

CONNECTOR_CLASS = {
	'redis': redis_class.RedisConnector,
	'fastapi' : fastapi_class.FastAPIPubSubConnector
}

SERVER_CLASS = {
	'fastapi' : fastapi_srv.FastAPIPubSubServer
}

def init():
	CONFIG_DICT = CONFIG.CONFIG # renew the config state

	# =========== Servers

	for k, v in CONFIG_DICT['servers'].items():
		if v['broadcast'] == 'true' or v['broadcast']:
			BROADCASTERS[k] = Broadcast(k,
					v,
					CONFIG_DICT['eventhive'])
			BROADCASTERS[k].run_in_thread()


		if v['create'] == 'always':
			SERVERS[k] = SERVER_CLASS[v['pubsub_type']](k,
					v,
					CONFIG_DICT['eventhive'])

			SERVERS[k].run_in_thread()

	# =========== Connectors

	for k, v in CONFIG_DICT['connectors'].items():

		try:
			if 'from_broadcast' in v:
				timeout = 5
				if type(v['from_broadcast']) == int:
					timeout = v['from_broadcast']
				logger.info("Initializing '%s' from Broadcast" % k)
				init_dict = init_from_broadcast(k, timeout=timeout)
				if init_dict is None or init_dict == {}:
					logger.error("Connector '%s' could not be initialized with 'from_broadcast'" % k)
					continue
				v['init'] = init_dict

			CONNECTORS[k] = CONNECTOR_CLASS[v['pubsub_type']](k,
					v,
					CONFIG_DICT['eventhive']
			)
		except Exception as e:
			logger.error("%s: Could not connect to PubSub '%s'" % (e, k))
			continue
			
		CONNECTORS[k]._publishers[k] = hook(CONFIG_DICT['connectors'][k]['channels'])(
			lambda message: CONNECTORS[k].send_to_pubsub(message)
			)

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

