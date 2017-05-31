Introduction
============

IoT-LAB MQTT provides access to an IoT-LAB experiment through an MQTT interface.

A main manager script will run agents to provide these services through MQTT:

* Nodes serial ports
* Nodes update/reset/power on-off
* Radio Sniffer
* Process execution

Architecture
------------

The IoT-LAB MQTT service is spread accross different agents and
accessed by the client through the MQTT broker.

.. graphviz:: architecture.dot

MQTT
^^^^

MQTT is a bus protocol organized around a central server (broker) where all
clients connect, publish messages, and the broker takes care of forwarding
messages to subscribed clients.

Topics
^^^^^^

Clients publish and subscribe messages to ``topics``, which are defined by
there name: ``an/example/of/topic``. Published message are transmitted to all
subscribed clients.

It is possible to subscribe to topics with wildcards:

* single-level: ``an/example/+/topic``
* multi-level: ``an/example/#``

This allows subscribing to many similar topics in a single request.

Client side
^^^^^^^^^^^

With this architecture, applications that want to access IoT-LAB resources
will interact through MQTT topics with the testbed agents to configure the
resources, control and command them.
The configuration application can even be different from the application using
the resources.

Thanks to the centralized broker, they can be run on any computer that has
access to the MQTT broker.
