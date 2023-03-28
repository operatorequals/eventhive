import time
import eventhive

network_name='my-beehive'
service_name='worker-bee'

# YAML configuration can be automatically loaded
# from 'eventhive.yaml' or programmatically (like below)
eventhive.CONFIG.read_string(
"""
connectors:
  {}:
    pubsub_type: redis
    channels: '*' # Send all events to redis
    init:
      host: 127.0.0.1
      port: 6379
      db: 0

    input_channel: '{}'
""".format(network_name, service_name)
)

# Register Events to be handled locally
# (like the Single Process example)
eventhive.EVENTS.append('{}/work'.format(service_name),
	help="""This is what 'worker-bees' do
	for a living""")

eventhive.EVENTS.append('{}/work-harder'.format(service_name),
	help="""And it's never enough""")

eventhive.EVENTS.append('{}/relax'.format(service_name),
  help="""All work and no play...""")

# Initializes connections and all
eventhive.init()

# Register callbacks for Events
@eventhive.hook('{}/work'.format(service_name))
def do_this(message):
	print("Working with {}!".format(
		message['work'])
	)

@eventhive.hook('{}/work-harder'.format(service_name))
def do_that(message):
	print("more work with {}!".format(
		message['work'])
	)

@eventhive.hook('{}/relax'.format(service_name))
def do_nothing(message):
  print("Chilling...")

# Nothing is blocking execution
while True:
  time.sleep(5)
  # Relax every once in a while
  eventhive.EVENTS[
    '{}/relax'.format(service_name)
    ](None)