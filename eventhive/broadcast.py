from zeroconf import (
    IPVersion,
    ServiceBrowser,
    ServiceInfo,
    ServiceStateChange,
    Zeroconf,
    ZeroconfServiceTypes,
)

import socket
import threading
import json
import time

from .logger import logger
from .crypto import sign, verify

MDNS_TYPE = "_eventhive._tcp.local."


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 80))
    try:
        return s.getsockname()[0]
    finally:
        s.close()


CURRENT_IP = get_ip()


class ZeroconfPropertiesEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return str(o, 'utf8')

# Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, o)


class Broadcast:

    def __init__(self, connector_id, server_config, global_config):
        self.conn_id = connector_id
        self.server_conf = server_config
        self.global_conf = global_config
        self.created = time.time()

        self.broadcast = Zeroconf()
        self.service_name = "%s.%s" % (self.conn_id, MDNS_TYPE)

        if self.server_conf['init']['host'] == '0.0.0.0':
            # Thread-safe deep copy
            init_dict = json.loads(json.dumps(self.server_conf['init']))
            init_dict['host'] = CURRENT_IP

        init_dict['created'] = self.created

        if 'secret' in self.server_conf:
            init_dict['__sign__'] = sign(self.server_conf['secret'], init_dict)
            logger.debug("Signed server properties for '%s'." % (
                self.conn_id)
            )
        logger.debug("Server properties for '%s': '%s'" % (
            self.conn_id, init_dict)
        )

        self.info = ServiceInfo(
            MDNS_TYPE,
            self.service_name,
            addresses=[socket.inet_aton(self.server_conf['init']['host'])],
            port=self.server_conf['init']['port'],
            properties=init_dict
        )

    def run(self):
        logger.info("Broadcasting server '%s'" % self.service_name)
        self.broadcast.register_service(self.info)

    def run_in_thread(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.broadcast.unregister_service(self.info)
        self.broadcast.close()


def init_from_broadcast(connector_id, timeout=5, secret=None):
    timeout = timeout * 1000  # Zeroconf expects millis
    zc = Zeroconf()
    # print(ZeroconfServiceTypes.find())
    info = zc.get_service_info(
        MDNS_TYPE,
        connector_id +
        '.' +
        MDNS_TYPE,
        timeout=timeout)
    zc.close()
    if info is None:
        return None

    logger.debug(
        "Found network properties '%s' for '%s'" %
        (info.properties, connector_id))
    temp_init = {}
    init = info.properties
    # Properties come as <bytes,bytes> dict
    for k, v in init.items():
        k = str(k, 'utf8')
        v = str(v, 'utf8')
        if k == 'created': v = float(v)
        if k == 'port': v = int(v)
        temp_init[k] = v

    init = temp_init
    created = init.get('created', None)
    signature = init.pop('__sign__', 'N/A')

    if secret is not None:
        if signature == 'N/A':
            logger.warning(
                "Network '%s' found, but properties not signed. Aborting..." %
                (connector_id))
            return None

        logger.debug(
            "Verifying properties '%s' for network '%s'" % (init, connector_id))
        if not verify(secret, init, signature):
            logger.warning(
                "Network '%s' found, but signature cannot be verified. Aborting..." %
                (connector_id))
            return None

    init.pop('created', None)

    logger.info("Network '%s' found: %s" % (connector_id, init))
    return init
