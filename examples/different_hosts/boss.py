import time
import eventhive

network_name = 'my-beehive'
service_name = 'queen-bee'

# YAML configuration can be automatically loaded
# from 'eventhive.yaml' or programmatically (like below)
eventhive.CONFIG.read_string(
    """
connectors:
  {}:
    pubsub_type: redis
    channels: '*' # Send all events to redis
    init:
      # All keyword arguments named after the Redis Client object __init__
      # are supported (ref: https://redis.readthedocs.io/en/latest/connections.html#generic-client)
      # and directly passed to __init__
      host: 127.0.0.1
      port: 6379
      db: 0

    # If set to non-empty, eventhive will
    # subscribe to events under:
    # '<channel_tag>/<input_channel>/*'
    input_channel: ''
""".format(network_name)
)

# Register remote Events to be handled
# by the network
eventhive.EVENTS.append(
    '{}/worker-bee/work'.format(network_name),
    help="Order all workers to work"
)
eventhive.EVENTS.append(
    '{}/worker-bee/work-harder'.format(network_name),
    help="Order all workers to work"
)

# Initializes connections and all
eventhive.init()

# Order all worker bees in 'my-beehive'
# to work every second
while True:
    time.sleep(1)
    eventhive.EVENTS.call(
        # Check the wildcard
        "{}/worker-bee/work*".format(network_name),
        # Positional Argument for workers
        {'work': 'heavy load'})
