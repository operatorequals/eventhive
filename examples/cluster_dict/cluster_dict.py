import collections.abc
import logging, sys, time

import eventhive

eventhive.logger.addHandler(logging.StreamHandler(sys.stderr))
# eventhive.logger.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.handlers = [logging.NullHandler()]
# logger.addHandler(logging.StreamHandler(sys.stderr))

class ClusterDict(collections.abc.MutableMapping):

	def __init__(self, *args,
				name="eventhive",
				port = 8085,
				store = dict(),
				secret = ''
				):
		logger.info("Initializing ClusterDict: %s" % name)
		self.store = store
		self.created = time.time()
		self.earliest_update = self.created

		self.service_name = ("clusterdict-%s" % name).lower()
		self.eventhive_config = """
connectors:
  {name}:
    pubsub_type: fastapi
    from_broadcast: 10
    input_channel: {receiver}
    secret: '{secret}'
servers:
  {name}:
    pubsub_type: fastapi
    create: needed
    broadcast: true
    init:
      host: '0.0.0.0'
      port: {port}
      endpoint: /pubsub """.format(
			name=self.service_name,
			receiver=name,
			secret=secret,
			port=str(port),
			)
		eventhive.CONFIG.read_string(self.eventhive_config)
		self.setitem_remote = "%s/%s/setitem" % (self.service_name, name)
		self.delitem_remote = "%s/%s/delitem" % (self.service_name, name)
		self.getall_req_remote = "%s/%s/getall-req" % (self.service_name, name)
		self.getall_resp_remote = "%s/%s/getall-resp" % (self.service_name, name)

		self.setitem_local = "%s/setitem" % (name)
		self.delitem_local = "%s/delitem" % (name)
		self.getall_req_local = "%s/getall-req" % (name)
		self.getall_resp_local = "%s/getall-resp" % (name)

		eventhive.EVENTS.append(self.setitem_local)
		eventhive.EVENTS.append(self.delitem_local)
		eventhive.EVENTS.append(self.getall_req_local)
		eventhive.EVENTS.append(self.getall_resp_local)

		eventhive.EVENTS.append(self.setitem_remote)
		eventhive.EVENTS.append(self.delitem_remote)
		eventhive.EVENTS.append(self.getall_req_remote)
		eventhive.EVENTS.append(self.getall_resp_remote)

		@eventhive.hook(self.setitem_local)
		def setitem(kwargs):
			# print("Setting '%s' to '%s" % (kwargs['key'], kwargs['value']))
			self.store[kwargs['key']] = kwargs['value']

		@eventhive.hook(self.delitem_local)
		def delitem(kwargs):
			# print("Deleting '%s'" % (kwargs['key']))
			del self.store[kwargs['key']]

		@eventhive.hook(self.getall_resp_local)
		def getall_resp(kwargs):
			# print("Got full store")
			created = kwargs['created']
			if self.earliest_update > created:
				self.store = kwargs['store']
				self.earliest_update = created

		@eventhive.hook(self.getall_req_local)
		def getall_req(kwargs):
			# print("Asking for full store")
			ret = {"created": self.created, "store": self.store}
			eventhive.EVENTS.call(self.getall_resp_remote, ret)

		eventhive.init()

		# get updated dict
		eventhive.EVENTS.call(self.getall_req_remote, {})

	def __getitem__(self, key):
		return self.store[key]

	def __setitem__(self, key, value):
		eventhive.EVENTS.call(self.setitem_remote, {"key":key, "value":value})

	def __delitem__(self, key):
		eventhive.EVENTS.call(self.delitem_remote, {"key":key})

	def __iter__(self):
		return iter(self.store)

	def __len__(self):
		return len(self.store)

	def __repr__(self):
		return self.store.__repr__()

if __name__ == '__main__':
	cd = ClusterDict()
	print("==> ClusterDict instance: 'cd'")
	import code; code.interact(local=locals())
