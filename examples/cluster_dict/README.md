# `cluster-dict`

A Python `dict` that gets replicated through the network!

[An old idea](https://github.com/operatorequals/cluster-dict) re-implemented with `eventhive` in ~100 lines of code!

## Usage

#### Process #1 (somewhere in the network)
```python
import cluster_dict

cd = cluster_dict.ClusterDict()
cd["hello"] = "world"
```

#### Process #2 (somewhere *else* in the network - also a bit later)
```python
import cluster_dict

cd = cluster_dict.ClusterDict()
print(cd)
{'hello': 'world'}
```

## What's happening?

The `dict` `__setitem__` and `__delitem__` methods are hooked by `eventhive` and propagated through PubSub, updating all data structures at the same time.
Additionally, when a new `ClusterDict` is created it automatically joins the Hive and asks for the current state of the data structure. The existing `ClusterDict` instances respond and the new `ClusterDict` gets initialized with the provided data.
