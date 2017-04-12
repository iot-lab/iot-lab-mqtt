############
IoT-LAB MQTT
############

Provide access to IoT-LAB experiments as MQTT agents.

Protocol documentation
`IoT-LAB-MQTT Documentation <https://iot-lab.github.io/iot-lab-mqtt/>`_

Developped in the context of
`ARMOUR European Union project <http://armour-project.eu/>`_


Installation
============

Install in server mode on IoT-LAB frontend::

   git clone https://github.com/iot-lab/iot-lab-mqtt.git
   cd iot-lab-mqtt
   pip install --user -e .[server]

Install in client mode on your computer::

   git clone https://github.com/iot-lab/iot-lab-mqtt.git
   cd iot-lab-mqtt
   pip install --user .


Add python user install directory to the ``PATH`` by
appending the following line in your ``~/.bashrc``::

   export PATH="${HOME}/.local/bin:${PATH}"

You can do it with::

   echo 'export PATH="${HOME}/.local/bin:${PATH}"' >> ~/.bashrc
   # Reload configuration
   source ~/.bashrc

If you do not have this, you will need to run the scripts from the
repository directory prefixed with ``"./"``, so for example
``./iotlab-mqtt-clients``.


Documentation
=============

The documentation can be generated with::

   pip install --user sphinx
   make -C doc html


Context
=======

Server
------

To use the tools, you should have use a MQTT broker.
For this doc, I will use ``iot.eclipse.org``.
Both server and client agents will communicate through this centralized server.


Topics
------

MQTT is based on publish/subscribe on topics that are URLs.

To prevent collisions, I advise to prefix your URLs with something specific
to your experiment and instance.
I would say something like::

   my/experiment/on/blablabla/IOTLAB_USERNAME/IOTLAB_EXPERIMENT_ID

Providing prefix on the tools uses the ``--prefix`` option.


More advanced
-------------

See the documentation on the implementation


Running
=======


On the server, you should run the ``server`` agents first::

   iotlab-mqtt-serial       [ARGUMENTS]
   iotlab-mqtt-radiosniffer [ARGUMENTS]
   iotlab-mqtt-node         [ARGUMENTS]

And on the client, you should run either your client, or the provided example::

   iotlab-mqtt-clients serial       [ARGUMENTS]
   iotlab-mqtt-clients radiosniffer [ARGUMENTS]
   iotlab-mqtt-clients node         [ARGUMENTS]
   iotlab-mqtt-clients log          [ARGUMENTS]


Arguments
---------

You can get the list of arguments with ``--help`` option.

Global MQTT configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Broker address, url of the MQTT server::

   broker

Broker port, defaults to 1883 (when I wrote it)::

   --broker-port BROKER_PORT

Topics prefix, your topic namespace::

   --prefix PREFIX


Client MQTT configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Server agent site name, IoT-LAB site name::

   --site IOTLAB_SITE


IoT-LAB API usage configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configuration for server that use IoT-LAB API (``radiosniffer``).
When not provided, the tool tries to detect them from ``.iotlabrc`` and current
running experiment.

IoT-LAB API username::

   --iotlab-user IOTLAB_USERNAME

IoT-LAB API password::

   --iotlab-password IOTLAB_PASSWORD


IoT-LAB experiment ID to use::

   --experiment-id EXPERIMENT_ID
