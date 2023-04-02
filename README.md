# EventHive

Network PubSub and Async Message Passing for Humans

![logo](https://raw.githubusercontent.com/operatorequals/eventhive/master/assets/logo-white.png#gh-dark-mode-only)
![logo](https://raw.githubusercontent.com/operatorequals/eventhive/master/assets/logo-black.png#gh-light-mode-only)

## What is that thing?

`eventhive` is a Python package that enables Python code to communicate using
Publisher/Subscriber model uniformly, be it in the same process or in different hosts!

Supports external PubSub backends (like Redis), Service Discovery (using [python-zeroconf](https://github.com/python-zeroconf/python-zeroconf/)) and Secure Message Signing.


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

## The CLI Tool

```bash
python -m eventhive.cli --help

```