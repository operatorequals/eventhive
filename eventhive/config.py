import yaml
import os


from mergedeep import merge, Strategy

from .logger import logger

EVENTHIVE_CONFIG_ENV = "EVENTHIVE_CONFIG"
EVENTHIVE_SECRET_ENV = "EVENTHIVE_SECRET"
# EVENTHIVE_SECRET="eventhive-redis:m1s3cr3tp@s50rd eventhive-fastapi:an0th3rp@55"
EVENTHIVE_CONFIG_FILENAME = "eventhive.yaml"

PUBSUB_TYPES = [
    'redis',
    'fastapi',
]

CONFIG_DEFAULTS = """
eventhive:

  metadata_key: '__eventhive__'
  remove_metadata: false
  channel_separator: '/'

connectors: {}

  # The key is used as 'channel_tag'
  # All events to be sent through this PubSub
  # connection will look like:
  # 'eventhive-redis/*'
  # eventhive-redis:

    # Selector for PubSub client to use:
    # redis, fastapi, rabbitmq, sns
    # pubsub_type: redis

    # # If set to 'true' it uses zeroconf
    # # to look for a 'eventhive-redis' eventhive
    # # network - ignoring 'init' key
    # from_broadcast: false

    # init:

      # All keyword arguments named after the Redis Client object __init__
      # are supported (ref: https://redis.readthedocs.io/en/latest/connections.html#generic-client)
      # and directly passed to __init__
      # host: 127.0.0.1
      # port: 6379
      # db: 0

    # If set to non-empty, eventhive will
    # subscribe to events under:
    # '<channel_tag>/<input_channel>/*'

    # input_channel: ''

    # # If set to non-empty, eventhive will
    # # use the key to sign messages sent.
    # # Additionally, all unsigned messages
    # # will be dropped.
    # # Cannot work with 'from_broadcast' option
    # secret: ''

servers: {}
  # # Connectors with this 'network-name'
  # # can receive configuration for this server
  # # through 'init.from_broadcast'
  # eventhive-fastapi:
  #   pubsub_type: fastapi
  #   init:
  #     host: 0.0.0.0
  #     port: 8085
  #     endpoint: /pubsub
  #     scheme: ws

  #   # never - this server will never run
  #   # needed - if there is no similar named zeroconf
  #   # always - always run this server
  #   create: never

  #   # use zeroconf protocol to
  #   # broadcast this server
  #   broadcast: false
"""

CONFIG = yaml.safe_load(CONFIG_DEFAULTS)


def read_string(yaml_str):
    global CONFIG
    new = yaml.safe_load(yaml_str)
    old = yaml.safe_load(CONFIG_DEFAULTS)
    # Deep merge giving priority to new settings
    merge(CONFIG, old, new, strategy=Strategy.REPLACE)
    # print(CONFIG)


def read_file(filename):
    with open(filename) as f:
        read_string(f.read())


config_filename = os.environ.get(
    EVENTHIVE_CONFIG_ENV,
    EVENTHIVE_CONFIG_FILENAME)

if os.path.exists(config_filename):

    logger.info("Configuration file found: '%s'. Loading..." % config_filename)
    read_file(config_filename)

# Might contain secrets
# logger.debug("[*] Configuration dict: %s" % CONFIG)

secret_env = os.environ.get(EVENTHIVE_SECRET_ENV, None)
if secret_env is not None:
    secrets = secret_env.split()
    for secrets_tuple in secrets:
        connector, secret = secrets_tuple.split(':')
        if connector in CONFIG['connectors']:
            CONFIG['connectors']['secret'] = secret
        else:
            logger.warning(
                "Secret provided for connector '%s' but connector not defined..." %
                connector)
