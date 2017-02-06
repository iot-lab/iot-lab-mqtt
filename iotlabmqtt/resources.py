# -*- coding: utf-8 -*-

r"""IoT-LAB MQTT Resources agent
================================

.. |set|            replace::  ``{resourcesagenttopic}/ctl/set``
.. |reset|          replace::  ``{resourcesagenttopic}/ctl/reset``

.. |get|            replace::  ``{resourcesagenttopic}/ctl/get``
.. |archiget|       replace::  ``{resourcesagenttopic}/{archi}/ctl/get``
.. |nodeget|        replace::  ``{resourcesagenttopic}/{archi}/{num}/ctl/get``

.. |request|        replace::  :ref:`Request <RequestTopic>`
.. |request_topic|  replace::  *{topic}*/**request/{clientid}/{requestid}**
.. |reply_topic|    replace::  *{topic}*/**reply/{clientid}/{requestid}**

.. |jsonerr|        replace::  ``{"error": "msg"}``

Resources agent provide access to the list of nodes with attributes.
New attributes can be set.

Resources agent base topic: ::

   {prefix}/iot-lab/resources/{site}

Every topics from resources agent topics start by this topic prefix

:param prefix: configured prefix
:param site: site where the agent is run


Each nodes attributes are in the form: ``key:value``

:param key: an utf-8 string
:param value: JSON number, boolean, null


Topics Sumarry
==============

+-+----------------------------------------+----------+
| |Topic                                   | Type     |
+=+========================================+==========+
|  **Resources agent**                                |
+-+----------------------------------------+----------+
| ``{prefix}/iot-lab/resources/{site}``               |
+-+----------------------------------------+----------+
| ||reset|                                 ||request| |
+-+----------------------------------------+----------+
| ||set|                                   ||request| |
+-+----------------------------------------+----------+
|  **Get**                                            |
+-+----------------------------------------+----------+
| ||get|                                   ||request| |
+-+----------------------------------------+----------+
| ||archiget|                              ||request| |
+-+----------------------------------------+----------+
| ||nodeget|                               ||request| |
+-+----------------------------------------+----------+

Resources Agent global topics
=============================

Error Topic
-----------

No error topic, as all operations happen on requests.

Reset attributes
----------------

Reset all nodes attributes to their default/startup value.

+-----------------------------------------------------------------------------+
| ``reset`` request:                                                          |
|                                                                             |
+============+================================================================+
| Topic:     |    |reset|                                                     |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *empty*              |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or error_msg |
+------------+-----------------------------------------+----------------------+


Set attributes
--------------

Update given nodes with attributes.

Set payload is a JSON dict in the format::

   {
       "m3": {
           "1": {"new_attribute": 1, "role": "br"},
           "2": {"ipaddr": "aaaa::1234", "role": "client"},
           "3": {"role": null},
       },
       "a8": {
           "5": {"pi": 3.141592654, "used": false},
       }
   }

+-----------------------------------------------------------------------------+
| ``set`` request:                                                            |
|                                                                             |
+============+================================================================+
| Topic:     |    |set|                                                       |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *SET JSON payload*   |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *empty* or *JSON*    |
|            |                                         | |jsonerr|            |
+------------+-----------------------------------------+----------------------+

Get Topics
==========

Get topics allow querying nodes that match attributes.
When requested without payload it returns all nodes with their attributes.

Request payload can be a dict of attributes ``key:value`` and only nodes with
common attributes are returned.

If selection gives no nodes, an empty payload is returned.

Attributes query format
-----------------------

Get all nodes::

    Empty payload

Example of selection attributes::

    {"status": "OK", "mobile": 0}

    {"role": "client"}


Get nodes
---------

Get nodes that match attributes selection.
Return format is the same as ``get`` query format.

Example::

   {
       "m3": {
           "1": {
               "status": "OK",
               "network_address": "m3-1.grenoble.iot-lab.info"
           },
           "2": {
               "status": "OK",
               "network_address": "m3-2.grenoble.iot-lab.info"
           },
           "3": {
               "status": "DEPLOYFAILED",
               "network_address": "m3-3.grenoble.iot-lab.info"
           }
       },
       "a8": {
           "5": {
               "status": "OK",
               "network_address": "m3-3.grenoble.iot-lab.info"
           }
       }
   }

+-----------------------------------------------------------------------------+
| ``get`` request:                                                            |
|                                                                             |
+============+================================================================+
| Topic:     |    |get|                                                       |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *GET JSON payload*   |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *JSON reply*,        |
|            |                                         | *empty* or |jsonerr| |
+------------+-----------------------------------------+----------------------+


If payload is a JSON with attributes, only return nodes matching.

Get nodes with ``archi``
------------------------

Same as simple get, but only retuns the given ``archi`` sub-dict.

Example for ``archi == m3``::

   {
       "1": {
           "status": "OK",
           "network_address": "m3-1.grenoble.iot-lab.info"
       },
       "2": {
           "status": "OK",
            "network_address": "m3-2.grenoble.iot-lab.info"
       },
       "3": {
           "status": "DEPLOYFAILED",
           "network_address": "m3-3.grenoble.iot-lab.info"
       }
   }

+-----------------------------------------------------------------------------+
| ``archiget`` request:                                                       |
|                                                                             |
+============+================================================================+
| Topic:     |    |archiget|                                                  |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *GET JSON payload*   |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *JSON reply*,        |
|            |                                         | *empty* or |jsonerr| |
+------------+-----------------------------------------+----------------------+


Get node ``archi``-``num``
--------------------------

Same as simple get, but only returns given ``archi``-``num`` node attributes.

Example for ``archi == m3`` and ``num == 1``::

   {
       "status": "OK",
       "network_address": "m3-1.grenoble.iot-lab.info"
   }


+-----------------------------------------------------------------------------+
| ``nodeget`` request:                                                        |
|                                                                             |
+============+================================================================+
| Topic:     |    |nodeget|                                                   |
+------------+-----------------------------------------+----------------------+
|**Message** | **Topic**                               | **Payload**          |
+------------+-----------------------------------------+----------------------+
| Request    | |request_topic|                         | *GET JSON payload*   |
+------------+-----------------------------------------+----------------------+
| Reply      | |reply_topic|                           | *JSON reply*,        |
|            |                                         | *empty* or |jsonerr| |
+------------+-----------------------------------------+----------------------+


"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import os
import json
from copy import deepcopy
from collections import OrderedDict

from future.utils import viewitems

from . import common
from . import mqttcommon

PARSER = common.MQTTAgentArgumentParser()
common.parser_add_iotlab_auth_args(PARSER)
PARSER.add_argument('--experiment-id', dest='experiment_id', type=int,
                    help='experiment id submission')


class AttributesDict(OrderedDict):
    """One deep dict of string -> SimpleJsonItem."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validate()

    def _validate(self):
        """Validate keys and values.

        Only String->SimpleType JSON compatible are allowed.
        """
        for key, value in viewitems(self):
            self._valid_key(key)
            self._valid_key(value)

    @staticmethod
    def _valid_key(key):
        """Validate ``key``, allow string, same as JSON."""
        err = 'Keys should be unicode string: {!r}'
        if not isinstance(key, str):
            raise ValueError(err.format(key))
        return True

    @staticmethod
    def _valid_value(value):
        """Validate ``value``, allow 'simple' types allowed in JSON."""
        err = 'Values should be null/int/float/bool: {!r}'
        valid = (value is None or
                 isinstance(value, str) or
                 isinstance(value, int) or
                 isinstance(value, float) or
                 isinstance(value, bool))
        if not valid:
            raise ValueError(err.format(value))
        return False

    def issubset(self, superset):
        """Check in current AttributesDict is a subset of ``superset``."""
        assert isinstance(superset, AttributesDict)
        return all(item in viewitems(superset) for item in viewitems(self))

    @classmethod
    def from_dict(cls, data=None):
        """Create AttributesDict from ``data`` dict.

        If data is None, return None.
        """
        if not data:
            return None

        try:
            items = viewitems(data)
            return cls(items)
        except AttributeError:
            # TODO error on non dict
            raise
        except ValueError:
            # TODO error on key/values
            raise


class ResourcesAttrsDict(OrderedDict):
    """Resources attributes dictionnary with format:

    {
        'm3': {
            '1': ATTR1_DICT,
            '2': ATTR2_DICT,
        }
    }
    """
    def set_attributes(self, archi, num, attributes, copy=False):
        """Set ``attributes`` for node ``archi-num``.

        :param copy: if set, copy attribute before setting
        """
        # TODO attributes, load as AttributesDict
        attributes = deepcopy(attributes) if copy else attributes
        self.setdefault(archi, OrderedDict())[num] = attributes

    def archi_num_attrs_iter(self):
        """Generator that iters with tuples ``(archi, num, attributes)``."""
        for archi, num_dict in self.items():
            for num, attrs in num_dict.items():
                yield archi, num, attrs

    def updated(self, attributes_dict):
        """Return a new ResourcesAttrsDict updated with ``attributes_dict``.

        :raises: ValuError if ``attributes_dict`` has non managed node
        """
        res = deepcopy(self)

        for archi, num, attrs in attributes_dict.archi_num_attrs_iter():
            # TODO load attrs
            try:
                res[archi][num].update(attrs)
            except KeyError:
                raise ValueError('Node %s-%s not managed' % (archi, num))

        return res

    def filter(self, attrs=None):
        """"Return a ResourcesAttrsDict for resources matching ``attrs``."""
        if attrs is None:
            return deepcopy(self)

        ana_iter = [(a, n, nodeattrs) for a, n, nodeattrs in
                    self.archi_num_attrs_iter() if
                    attrs.issubset(nodeattrs)]

        return self.from_archi_num_attrs_iterable(ana_iter)

    def select(self, archi=None, num=None):
        """Return only ``archi`` or ``archi``,``num`` subset of resources."""
        res = self
        if archi:
            res = res.get(archi, {})
            if num:
                res = res.get(num, None)
        return res

    @classmethod
    def from_archi_num_attrs_iterable(cls, iterable):
        """Create ResourcesAttrsDict from iterable.

        :type iterable: iterable of ```(archi, num, attrs) tuples```
        """

        nodes_dict = cls()
        for archi, num, attrs in iterable:
            nodes_dict.set_attributes(archi, num, attrs, copy=True)

        return nodes_dict

    @classmethod
    def from_experiment(cls, site, username=None, password=None, expid=None):
        """Create ResourcesAttrsDict from experiment.

        :param username: IoT-LAB username
        :param password: IoT-LAB password
        :param expid: Experiment id

        If username/password are None, read them from .iotlabrc.
        If expid is None, try using current experiment.
        """

        # Lazy import `iotlabcli` to let clients work without dependency
        import iotlabcli.auth
        import iotlabcli.rest
        import iotlabcli.experiment

        usr, passwd = iotlabcli.auth.get_user_credentials(username, password)
        api = iotlabcli.rest.Api(usr, passwd)

        experiment = iotlabcli.experiment.get_experiment(api, expid, '')
        depl = experiment['deploymentresults']
        deploy_attrs = cls.from_deployment(depl, site)

        # TODO check 'state' running
        # if experiment['state']:
        #     raise ValueError('Experiment %s not running %s' %
        #                      (expid, experiment['state']))

        res = iotlabcli.experiment.get_experiment(api, expid, 'resources')
        res = res['items']
        resources = cls.from_resources(res, site)

        return resources.updated(deploy_attrs)

    @classmethod
    def from_resources(cls, resources, site):
        """Create ResourcesAttrsDict from ``resources`` for ``site``.

        >>> resources = [
        ...     {"network_address": "m3-1.grenoble.iot-lab.info"},
        ...     {"network_address": "m3-2.grenoble.iot-lab.info"},
        ...     {"network_address": "a8-3.grenoble.iot-lab.info"},
        ...     {"network_address": "a8-4.grenoble.iot-lab.info"},
        ...     {"network_address": "m3-10.lille.iot-lab.info"},
        ...     {"network_address": "a8-20.lille.iot-lab.info"},
        ... ]

        >>> ret_dict = {
        ...     "m3": {
        ...         "1": {"network_address": "m3-1.grenoble.iot-lab.info"},
        ...         "2": {"network_address": "m3-2.grenoble.iot-lab.info"},
        ...     },
        ...     "a8": {
        ...         "3": {"network_address": "a8-3.grenoble.iot-lab.info"},
        ...         "4": {"network_address": "a8-4.grenoble.iot-lab.info"},
        ...     },
        ... }

        >>> (ResourcesAttrsDict.from_resources(resources, 'grenoble') ==
        ...  ret_dict)
        True
        """
        nodes_iter = _site_nodes_iter(resources, site,
                                      (lambda x: x['network_address']))
        return cls.from_archi_num_attrs_iterable(nodes_iter)

    @classmethod
    def from_deployment(cls, deploymentresults, site):
        """Create ResourcesAttrsDict from ``deploymentresults`` for ``site``.

        >>> deploymentresults = {
        ...     "0": [
        ...         "m3-1.grenoble.iot-lab.info",
        ...         "a8-3.grenoble.iot-lab.info",
        ...         "m3-10.lille.iot-lab.info",
        ...     ],
        ...     "1": [
        ...         "m3-2.grenoble.iot-lab.info",
        ...         "a8-4.grenoble.iot-lab.info",
        ...         "a8-20.lille.iot-lab.info",
        ...     ],
        ... }

        >>> ret_dict = {
        ...     "m3": {
        ...         "1": {"deploymentresult": "0", "state": "OK"},
        ...         "2": {"deploymentresult": "1", "state": "DEPLOYFAILED"},
        ...     },
        ...     "a8": {
        ...         "3": {"deploymentresult": "0", "state": "OK"},
        ...         "4": {"deploymentresult": "1", "state": "DEPLOYFAILED"},
        ...     },
        ... }

        >>> ResourcesAttrsDict.from_deployment(deploymentresults,
        ...                                    'grenoble') == ret_dict
        True
        """
        attrs_dict = cls()

        for result, nodes_hostnames in deploymentresults.items():
            result_attrs = cls._deploymentresult_attrs(result)

            for archi, num, _ in _site_nodes_iter(nodes_hostnames, site):
                attrs_dict.set_attributes(archi, num, result_attrs, copy=True)

        return attrs_dict

    @staticmethod
    def _deploymentresult_attrs(result):
        """Attributes for deployment result.

        Return a dict with attributes with 'state', and 'deploymentresult'

        >>> (ResourcesAttrsDict._deploymentresult_attrs('0') ==
        ...  {'deploymentresult': '0', 'state': 'OK'})
        True

        >>> (ResourcesAttrsDict._deploymentresult_attrs('1') ==
        ...  {'deploymentresult': '1', 'state': 'DEPLOYFAILED'})
        True
        """

        state = 'OK' if int(result) == 0 else 'DEPLOYFAILED'
        return {'deploymentresult': result, 'state': state}


class MQTTResourcesManager(object):
    """Resources manager for MQTT."""

    PREFIX = 'iot-lab/resources/{site}'
    TOPICS = {
        'prefix': PREFIX,
        'archi': os.path.join(PREFIX, '{archi}'),
        'node': os.path.join(PREFIX, '{archi}/{num}')
    }

    HOSTNAME = os.uname()[1]

    def __init__(self,  # pylint:disable=too-many-arguments
                 host, port=None, prefix='', resources=None):
        assert resources

        staticfmt = {'site': self.HOSTNAME}
        _topics = mqttcommon.format_topics_dict(self.TOPICS, prefix, staticfmt)

        self.saved_resources = resources
        self.resources = None
        self._reset()

        self.topics = {
            'reset': mqttcommon.RequestServer(_topics['prefix'], 'reset',
                                              callback=self.cb_reset),

            'set': mqttcommon.JsonRequestServer(_topics['prefix'], 'set',
                                                callback=self.cb_set),

            'get': mqttcommon.JsonRequestServer(_topics['prefix'], 'get',
                                                callback=self.cb_get),
            'archiget': mqttcommon.JsonRequestServer(_topics['archi'], 'get',
                                                     callback=self.cb_get),
            'nodeget': mqttcommon.JsonRequestServer(_topics['node'], 'get',
                                                    callback=self.cb_get),
        }

        self.client = mqttcommon.MQTTClient(host, port=port,
                                            topics=self.topics)

    def _reset(self):
        """Reset resources values."""
        self.resources = deepcopy(self.saved_resources)

    def error(self, topic, message):
        """Publish error that happend on topic."""
        self.topics['error'].publish_error(self.client, topic,
                                           message.encode('utf-8'))

    def cb_get(self, message, archi=None, num=None):
        """Get resources infos.

        :param message: mqtt message, payload is attributes selection JSON
        :param archi: only returns infos for ``archi``
        :param num: requires ``archi``, only returns infos for ``num``
        """

        # infos/ctl/get   -> { 'm3': {'1': {'archi': '...', 'status': 0, ...},
        #                             '2': {'archi': '....', 'status': 1, ...},
        #                     ...}}
        # infos/m3/ctl/get -> {'1': {}, ...}
        # infos/m3/1/ctl/get -> {'archi': '...'}

        try:
            attrs_select = AttributesDict.from_dict(message.json)
        except ValueError:
            raise

        resources = self.resources.filter(attrs_select)
        resources = resources.select(archi, num)
        # TODO resources empty ?

        # None on empty
        resources = resources or None

        return json.dumps(resources, encoding='utf-8')

    def cb_set(self, message):
        """Update attributes for resouces. Payload is the same format as 'get'.

        :param message: mqtt message, payload is resources attributes JSON
        """
        # infos/ctl/set   -> { 'm3': {'1': {'archi': '...', 'status': 0, ...},
        #                             '2': {'archi': '....', 'status': 1, ...},
        #                      ...}}
        if message.json is None:
            raise ValueError("Missing 'set' payload")

        self.resources = self.resources.updated(message.json)

        return ''

    def cb_reset(self, message):
        """Reset resources attributes to their original value."""
        self._reset()
        return b''

    # Agent running

    def run(self):
        """Run agent."""
        try:
            self.start()
            common.wait_sigint()
        finally:
            self.stop()

    def start(self):
        """Start Agent."""
        self.client.start()

    def stop(self):
        """Stop agent."""
        self.client.stop()


def _site_nodes_iter(nodes, site, hostname_getter=(lambda x: x)):
    """Iterator on ``nodes`` for ``site``.

    :param nodes: nodes iterable
    :param site: site selection
    :param hostname_getter: function to get hostname from node
    :returns: generator or tuples (archi, num, node)
    """

    from iotlabcli.helpers import node_url_sort_key
    for node in nodes:
        node_site, archi, num = node_url_sort_key(hostname_getter(node))
        if node_site != site:
            continue
        yield archi, str(num), node


def main():
    """Run resources agent."""

    opts = PARSER.parse_args()

    # TODO handle exception here
    site = MQTTResourcesManager.HOSTNAME
    resources = ResourcesAttrsDict.from_experiment(site,
                                                   opts.iotlab_username,
                                                   opts.iotlab_password,
                                                   opts.experiment_id)

    res = MQTTResourcesManager(opts.broker, port=opts.broker_port,
                               prefix=opts.prefix, resources=resources)

    res.run()


if __name__ == '__main__':
    main()
