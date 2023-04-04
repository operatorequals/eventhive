# EventHive

Network PubSub and Async Message Passing for Humans

![logo](https://raw.githubusercontent.com/operatorequals/eventhive/master/assets/logo-white.png#gh-dark-mode-only)
![logo](https://raw.githubusercontent.com/operatorequals/eventhive/master/assets/logo-black.png#gh-light-mode-only)

## What is that thing?

`eventhive` is a Python package that enables Python code to communicate using
Publisher/Subscriber model uniformly, be it in the same process or in different hosts!

Supports external PubSub backends (like Redis), Service Discovery (using [python-zeroconf](https://github.com/python-zeroconf/python-zeroconf/)) and application level Message Signing and Encryption (using [Python Native AES](https://github.com/boppreh/aes)).


## What does it do?

Leverages Python reflection magic and the excelent API created by [@dzervas](https://github.com/dzervas) in [`hooker`](https://github.com/satori-ng/hooker) for event-based programming and expands it to network level event-passing, effectively creating a PubSub-based RPC (Remote Procedure Calling) framework.

It can be used in IoT Development, to Games, to Kubernetes and microservices!

## How to Use

### Worker

* Create a minimal `eventhive` YAML configuration for the Worker:
  ```yaml
  connectors:
    my-hive:
      pubsub_type: fastapi
      input_channel: 'worker'
      init:
        host: 127.0.0.1
        port: 8085
        endpoint: /pubsub
  ```

* Register an `eventhive` event:
  ```python
  eventhive.EVENTS.append("worker/action")
  ```

* Create a function with a single argument and annotate it with the `eventhive` event:
  ```python
  @eventhive.hook("worker/action")
  def work(arg): print("Working with: %s" arg)
  ```

* Start `eventhive`
  ```python
  eventhive.init()
  ```

### Queen

* Create an `eventhive` YAML configuration for the Queen. Also add a PubSub server in the mix:
  ```yaml
  connectors:
    my-hive:
      pubsub_type: fastapi
      input_channel: 'queen'
      init:
        host: 127.0.0.1
        port: 8085
        endpoint: /pubsub

  servers:
    my-hive:
      pubsub_type: fastapi
      create: always
      broadcast: false
      init:
        host: 0.0.0.0
        port: 8085
        endpoint: /pubsub
  ```

* Register an `eventhive` event implemented by the worker:
  ```python
  eventhive.EVENTS.append("my-hive/worker/action")
  ```

* Start `eventhive`
  ```python
  eventhive.init()
  ```

* Call the registered event with a `dict`
  ```python
  eventhive.EVENTS.call("my-hive/worker/action", {"param1":1, "param2":2})
  ```

  The Worker will print:
  ```
  Working with: {'param1':1, 'param2':2}
  ```

## What with the `/` in the Event names?

A convention exists in `eventhive` so it can be used as a PubSub for event-based programming
and network message passing engine at the same time. This convention is based on *Event* names.

The *Events* are split in 3 categories following a naming convention:

### Strictly Local Events
Like [`bee_stuff`](https://github.com/operatorequals/eventhive/blob/master/examples/single_process.py#L3) in the single-process example. These Events cannot be called from the network.
They have to be defined (`eventhive.append("bee_stuff")`), implemented (`@eventhive.hook("bee_stuff")`) and
called (`eventhive.EVENTS["bee_stuff"]("arg")`) in the same process.

### Network Accessible Events
Like Worker Bee's [`worker-bee/work`](https://github.com/operatorequals/eventhive/blob/master/examples/different_hosts/worker.py#L40). These Events have to be defined and implemented by the same process,
but they can be called either from the same process (`eventhive.EVENTS["worker-bee/work"]({"random":"dict"})`), or
by any other `eventhive` process in the network as a *Remote Event*.

### Remote Events
Like Queen Bee's [`my-beehive/worker-bee/work`](https://github.com/operatorequals/eventhive/blob/master/examples/different_hosts/boss.py#L33). These Events are not implemented in the process they are
defined (`eventhive.append("my-beehive/worker-bee/work")`). Calling these Events
(`eventhive.EVENTS["my-beehive/worker-bee/work"]({"random":"dict"})`) informs `eventhive` that they
have to travel over `my-beehive` network and get published to the `my-beehive/worker-bee/work` channel.

Other `eventhive` processes that are connected to `my-beehive` and have `input_channel: worker-bee` in their configuration, pick up these Events, ditch the *Network Name* (`my-beehive/worker-bee/work` becomes `worker-bee/work`) and consume them like *Local Events*.


## Message Examples

`eventhive` events are simple JSON messages that can have metadata attached or not.
In the examples below metadata will be available under the key `__eventhive__`. Disabling metadata or changing the key name
can be configured through the [YAML configuration](https://github.com/operatorequals/eventhive/blob/master/eventhive/config.py#L20).

### No `secret` set - plaintext messages

```python
eventhive.EVENTS.call("my-hive/worker/action", {"param1":1, "param2":2})
```

```json
{"param1": 1, "param2": 2, "__eventhive__": {"time": 1680610165.4884348, "version": "0.3.2", "event": "my-hive/worker/action", "id": "d891d47f-64a4-4ecc-88ab-69249da31154"}}
```

`eventhive` metadata can be used from a hooked function for accessing event creation time, version checking and duplicate message checking.
Yet, it is planned to move some of these functionalities to the library.

Turning off metadata (i.e `eventhive.remove_metadata: true`) can save bandwidth, e.g in very limited IoT networks.

### With `secret` set

Setting a [`secret`](https://github.com/operatorequals/eventhive/blob/master/eventhive/config.py#L63) in a `connector` in the YAML configuration automatically enables AES Encryption and Message Signing. *This is totally transparent to the hooked function*, which will continue to accept events like the one described above.
Yet, the messages travelling through the network will look as below:

```json
{"iv": "2SH5S8J75afKxr76osauow==", "ciphertext": "JFJvaixp9/8oiYaxrCS+yA6TkCKlX85g0qG0GlZa8eaQTuXf1Ot33yiIIr7Y+fsFTzL7kzOtFbaq1uO6QH54N9oyeWUi7rDelQi2HNZGYRJCqwtwAbFX4+D8IgBGqYkYGPKuiUZCLRvPArPmaMh8PpMrq4/nEOGf0ivyS9hKEVb9KSrm4+VedAfBMQfpxP3Z/cm/jpj2sKDb9rfcjWATEcQToQ/U4PP40mUGeDpKbmyTAxGLdGAp3jDcghkAM76nDAXmTpuP0PN7YpSp/3cRAiweXxuBszIdeLuoUBOa"}
```

The `ciphertext` encapsulates messages like the one shown above, plus the `__sign__` key, which is used to verify the plaintext content and is stripped from the final message.

In case decryption or signature verification fails, the event gets dropped and does not arrive to the hooked functions.

Finally, if `secret` is set for a connector, it is impossible to accept non-encrypted, non-signed messages.

## The CLI Tool

A CLI tool is part of the `eventhive` package to make it possible to test YAML configurations, without writing application code (and adding moving parts to the test).

The output of the tool is the last `eventhive` message that was received in JSON, or `{"no":"output"}` if no message is received.

It uses YAML configuration and also can template YAML files, using the similar named arguments provided through CLI, as shown below:

```bash
eventhive-cli --network my-hive --receiver worker --secret m1s3cr3t --config fastapi-template.yaml
```

`fastapi-template.yaml`:
```yaml
connectors:
  {network}:
    pubsub_type: fastapi
    input_channel: '{receiver}'
    secret: '{secret}'
    init:
      host: 127.0.0.1
      port: 8085
      endpoint: /pubsub
```


### CLI Usage

```bash
$ eventhive-cli -h
usage: eventhive-cli [-h] [--network NETWORK] [--receiver RECEIVER] [--event EVENT] [--json-data JSON_DATA] [--target-event TARGET_EVENT] [--json-fallback JSON_FALLBACK]
                     [--config CONFIG] [--timeout TIMEOUT] [--secret SECRET] [--debug] [--verbose]

The Swiss-Army knife for Eventhive

optional arguments:
  -h, --help            show this help message and exit
  --network NETWORK     The Eventhive Network of Events (<here>/*/*) (default: eventhive)
  --receiver RECEIVER   The Eventhive Channel of Events (*/<here>/*) (default: cli)
  --event EVENT         The Eventhive Event Name (*/*/<here>) (default: do)
  --json-data JSON_DATA
                        If set - the JSON will be sent to "<network>/<receiver>/<event>" (default: False)
  --target-event TARGET_EVENT
                        If set - the JSON defined in "--json-data" will be published on it instead of "<network>/<receiver>/<event>" (default: None)
  --json-fallback JSON_FALLBACK
                        The JSON to print to STDOUT if no data is received in "<network>/<receiver>/<event>" (default: {"no":"output"})
  --config CONFIG       The Configuration file to be used by Eventhive (can include formatting) (default: .eventhive-config.yaml)
  --timeout TIMEOUT     Time to run before exiting and printing to STDOUT (default: 6)
  --secret SECRET       A secret string used for signing and encryption of messages (default: None)
  --debug, -d           When set - full DEBUG logs will be printed (default: 30)
  --verbose, -v         When set - INFO logs will be printed (default: None)

```
