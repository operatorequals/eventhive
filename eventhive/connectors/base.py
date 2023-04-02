import json
import uuid

from ..logger import logger
from ..__meta__ import __version__
import eventhive

import time
import base64

import hmac
import hashlib
from ..crypto import sign, verify, encrypt, decrypt, create_aes_key, create_aes_obj


class BaseConnector(object):

    def __init__(self, connector_id, connector_config, global_config):
        logger.info("Creating Connector: '%s'" % type(self))
        self.conn_id = connector_id
        self.conn_conf = connector_config
        self.global_conf = global_config

        self.input_pattern = "%s%s%s%s" % (
            self.conn_id,
            self.global_conf['channel_separator'],
            self.conn_conf['input_channel'],
            self.global_conf['channel_separator'],
        )

        self.secret = bytes(self.conn_conf.pop('secret', ''), 'utf8')
        if self.secret == b'' or not self.secret:
            self.secret = None
            self._key = None
            self._crypto = None
        else:
            crypto_obj = create_aes_obj(self.secret)
            self._key = crypto_obj['key']
            self._crypto = crypto_obj['obj']

    def create_metadata(self, event_name):
        id_ = str(uuid.uuid4())
        logger.debug("[%s] ID assigned to event '%s'" % (id_, event_name))
        ret = {
            "time": time.time(),
            "version": __version__,
            "event": event_name,
            "id": id_,
        }
        return ret

    def create_message(self, data, event_name):
        assert (isinstance(data, dict))
        message = data
        if not self.global_conf['remove_metadata']:
            message[self.global_conf['metadata_key']
                    ] = self.create_metadata(event_name)
            logger.debug("[%s] Data: %s" % (
                message[self.global_conf['metadata_key']]["id"], message)
            )
        mid = message.get(self.global_conf['metadata_key'], {}).get(
            "id",
            "N/A")
        if self.secret:
            message['__sign__'] = sign(self._key, message)
            message = encrypt(self._key, message, aes_obj=self._crypto)
        return mid, message

    def send_to_pubsub(self, message):
        event_name = eventhive.get_event_name()
        # Avoid running this catchall event
        # for events received by current process
        if self.conn_conf['input_channel'] and \
                event_name.startswith(self.conn_conf['input_channel']):
            logger.debug(
                "Got event from '%s'. Continuing..." %
                self.input_pattern)
            return

        id_, message = self.create_message(message, event_name)

        serialized_message = json.dumps(message)

        self.publish(serialized_message, event_name)

        logger.info("[%s] Published at: '%s'" % (id_, event_name))
        logger.debug("[%s] Content: '%s'" % (id_, serialized_message))

    def read_from_pubsub(self, data, event):
        logger.debug("Received: %s" % data)
        try:
            message = json.loads(data)
            message = decrypt(self._key, message, aes_obj=self._crypto)
        except json.decoder.JSONDecodeError as e:
            logger.warning(
                "[%s] Could not decode JSON from message: '%s'. Dropping..." %
                (e, data))
            return
        except UnicodeDecodeError as ude:
            logger.warning(
                "[%s] Could not decrypt message '%s'. Dropping..." %
                (ude, data))
            return

        if self.secret is not None:
            signature = message.pop('__sign__', None)
            if signature is None:
                logger.warning(
                    "Secret is set but signature not available. Dropping event: %s" %
                    (event))
                return

            valid_signature = verify(self._key, message, signature)
            if not valid_signature:
                logger.warning(
                    "Invalid signature. Dropping event: %s" %
                    (event))
                return

        try:
            metadata = message.get(
                self.global_conf['metadata_key'], {
                    'id': 'N/A'})
            mid = metadata["id"]
            logger.info("[%s] Received Event: '%s'" % (mid, event))
            logger.debug("[%s] Received data '%s'" % (mid, message))

        except KeyError:
            logger.debug("No metadata available: %s" % json.dumps(message))
            return

        # It's impossible to accept an event
        # starting with a pattern that is not subscribed
        assert event.startswith(self.input_pattern)

        # this function runs only for subscribed channel
        # Remove the Connector ID from the event name
        event = event[len(self.conn_id +
                          self.global_conf['channel_separator']):]
        logger.info("[%s] Firing event '%s'" % (mid, event))

        return eventhive.EVENTS.call(event, message)
