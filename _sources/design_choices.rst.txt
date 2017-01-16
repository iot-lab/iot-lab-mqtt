Agent Design choices
====================

This section describe design choices made for the IoT-LAB MQTT agents.


One agent for all resources
---------------------------

As a consequence of the large scale aspect of IoT-LAB, IoT-LAB tools have been
developed in a way to allow managing many resources from one program.

The same paradigm will be reproduced in the agents. The different resources will
however still be accessed through different topics.


Simple versus multiple resources addressing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Even if managing multiple resources, the agents will require addressing
one resource at a time. The reasons for this include readability, consistency,
implementation simplicity in the agents.

The only agent managing multiple nodes will be the nodes update/reset agent as
the resource it is interacting with is the IoT-LAB REST API which already
adresses multiple nodes.


One agent per use
-----------------

Agents will be separated to manage one task only and implemented as low level as
possible to be independent of the problem.

High level behaviour that require communicating to several agents can also be
implemented as MQTT agents for reuse.


Multi-site management
---------------------

Some agents must be run on the site where resources are, so must be run once per
site of the experiment whereas other must be run only once.

When running, there is one site which must be choosen as *master* and will host
the one instance only agents.


Topic prefix
------------

Agents have an option to set a topic prefix. I recommand to set it to something
starting with ``{user}/{expid}``. This way, agents run for different experiment
and users will be separated from one another.
The ``{user}`` and ``{expid}`` strings will be replaced by their effective
value when executed.
