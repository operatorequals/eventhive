# TODO
## Avoid Split-Brain
- [x] Broadcast `time_created` for servers
- [ ] Create thread that always looks for older server to join

## Remain Connected
- [ ] Create thread that checks if Connector is connected
- [ ] Fire up Connector initialization on Disconnect
- [ ] Fire up Server initialization if server disappeared and `create: needed`

## Eventhive APIs
- [ ] Create a default configuration to launch with Service Discovery
- [ ] Make `init` return what was finally initialized
- [x] Make `init` accept parameters of `required` connectors - failing if they cannot get initialized
- [ ] Make a `run_forever` function, avoid `while True` looping after `eventhive.init`
- [x] Make `hook` also `append` events in case they are not created
- [x] Create a `register(event, function)` function to assign any event to any function
- [ ] Create a response system to `eventhive.EVENTS.call`
- [ ] Create a way to not receive Events sent by the same process

## Backends
- [ ] RabbitMQ PubSub
- [ ] AWS SNS
- [ ] Google PubSub
- [ ] Kafka

## Security
- [ ] Split Signing and Encryption functionality
- [x] Add signing to broadcast - if `secret` is set in server
- [ ] Create a way to reject replayed messages (using the Event UUIDs with an LRU cache?)

## Support Python object passing
- [ ] Use `marshal`/`pickle` to values that are not JSON serializable
- [ ] Only allow the above if `secret` is set, for Security Reasons (RCE if plaintext)

## Documentation
- [ ] Create smaller examples
- [ ] Create RTFD page
- [ ] Create an example using render.com Free plan's Redis

## Reliability
- [ ] Create a threaded producer/consumer model (a queue?) for events going to `publish` (in `send_to_pubsub`),
so they are not lost if Connector doesn't work (`publish` fails)
- [ ] Properly use `async` wherever needed/supported by libraries
