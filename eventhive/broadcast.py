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

from .logger import logger

MDNS_TYPE = "_eventhive._tcp.local."


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 80))
    try:
        return s.getsockname()[0]
    finally:
        s.close()


class Broadcast:

    def __init__(self, connector_id, connector_config, global_config):
        self.conn_id = connector_id
        self.conn_conf = connector_config
        self.global_conf = global_config

        self.broadcast = Zeroconf()
        self.service_name = "%s.%s" % (self.conn_id, MDNS_TYPE)

        if self.conn_conf['init']['host'] == '0.0.0.0':
            # Thread-safe deep copy
            init_dict = json.loads(json.dumps(self.conn_conf['init']))
            init_dict['host'] = get_ip()

        self.info = ServiceInfo(
            MDNS_TYPE,
            self.service_name,
            addresses=[socket.inet_aton(self.conn_conf['init']['host'])],
            port=self.conn_conf['init']['port'],
            properties=init_dict,
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


def init_from_broadcast(connector_id, timeout=5):
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
    ret = {}
    for k, v in info.properties.items():
        ret[str(k, 'utf8')] = str(v, 'utf8')
    logger.info("Network '%s' found: %s" % (connector_id, ret))
    return ret
