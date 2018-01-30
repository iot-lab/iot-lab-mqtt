# -*- coding: utf-8 -*-

"""IoT-LAB API utils."""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from builtins import *  # pylint:disable=W0401,W0614,W0622

import tempfile

from . import common


def parser_add_iotlabapi_args(parser, group_help='IoT-LAB API configuration'):
    """Add iotlab auth arguments and experiment id to ``parser``."""
    group = parser.add_argument_group(group_help)
    group.add_argument('--iotlab-user', dest='iotlab_username',
                       help='IoT-LAB username')
    group.add_argument('--iotlab-password', dest='iotlab_password',
                       help='IoT-LAB password')
    group.add_argument('--experiment-id', dest='experiment_id', type=int,
                       help='experiment id submission')


class IoTLABAPI(object):
    """IoT-LAB API wrapper.

    Run commands using the REST API wrapped for the need of mqtt agents.
    It only runs commands for nodes on current execution site.
    """
    HOSTNAME = common.hostname()

    AUTH_ERROR = (
        'IoT-LAB API not authorized.\n'
        'Provide ``--iotlab-user`` and ``--iotlab-password`` options.\n'
        'Or register them using ``auth-cli --user USERNAME``'
    )

    A8M3_OPENOCD_TEMPLATE_CMD = """
    /usr/local/bin/openocd
            -f "/etc/iotlab-flash-scripts/iot-lab-a8-m3.cfg"
            -f "target/stm32f1x.cfg"
            -c "init"
            -c "targets"
            {commands}
            -c "shutdown"
    """.replace("\n", "").replace("\r", "").strip()

    A8M3_OPENOCD_RESET_RUN_CMD = A8M3_OPENOCD_TEMPLATE_CMD.format(
        commands=' -c "reset init" -c "reset run"')
    A8M3_OPENOCD_RESET_HALT_CMD = A8M3_OPENOCD_TEMPLATE_CMD.format(
        commands=' -c "reset halt"')

    def __init__(self, user=None, password=None, experiment_id=None):
        import iotlabcli.rest
        # Autoset user, password and experiment if they are None
        user, password = self._user_password(user, password)
        api = iotlabcli.rest.Api(user, password)
        # Get experiment ID and verify the experiment is Running.
        # This tests the user/password provided with the API
        experiment_id = self._experiment_id_and_running(api, experiment_id)

        self.api = api
        self.expid = experiment_id
        self.site = self.HOSTNAME

        # Support for Open-A8
        self.config_ssh = {'user': user,
                           'exp_id': experiment_id}

        assert self.expid is not None

    @staticmethod
    def _user_password(user, password):
        """Load username password from files if not defined."""
        import iotlabcli.auth
        return iotlabcli.auth.get_user_credentials(user, password)

    @classmethod
    def _experiment_id_and_running(cls, api, experiment_id=None):
        """Try getting experiment_id if None and check it is Running.

        System exit on failure.
        """
        import iotlabcli.rest
        try:
            experiment_id = cls._experiment_id(api, experiment_id)
            cls._check_experiment_running(api, experiment_id)
            return experiment_id
        except iotlabcli.rest.HTTPError:
            print(cls.AUTH_ERROR)
            exit(1)
        except (ValueError, RuntimeError) as err:
            print(err)
            exit(1)

    @staticmethod
    def _experiment_id(api, experiment_id):
        """Try getting experiment_id if not provided."""
        import iotlabcli.helpers
        return iotlabcli.helpers.get_current_experiment(api, experiment_id)

    @classmethod
    def _check_experiment_running(cls, api, experiment_id):
        """Check that experiment is Running."""
        ret = cls._get_experiment(api, experiment_id, 'state')
        state = ret['state']
        if state != 'Running':
            raise RuntimeError("Experiment %u not running '%s'" % (
                experiment_id, state))

    # Allow mocking this for tests
    @staticmethod
    def _get_experiment(api, experiment_id, info):
        """Get experiment ``info`` for ``experiment_id``."""
        import iotlabcli.experiment
        return iotlabcli.experiment.get_experiment(api, experiment_id, info)

    @classmethod
    def from_opts_dict(cls, iotlab_username=None, iotlab_password=None,
                       experiment_id=None, **_):
        """Create class from argparse entries."""
        return cls(iotlab_username, iotlab_password, experiment_id)

    def set_sniffer_channel(self, channel, archi, *nums):
        """Set sniffer on ``channel`` for nodes ``archi`` and ``*nums``."""
        return self._update_profile(channel, archi, *nums)

    def reset(self, archi, *nums):
        """Reset nodes ``archi`` and ``*nums``."""
        return self.node_command('reset', None, archi, *nums)

    def update_idle(self, archi, *nums):
        """Update nodes ``archi`` and ``*nums`` with idle firmware."""
        return self.node_command('update-idle', None, archi, *nums)

    def update(self, firmwarepath, archi, *nums):
        """Update nodes ``archi`` and ``*nums`` with ``firmwarepath``."""
        return self.node_command('update', firmwarepath, archi, *nums)

    def poweron(self, archi, *nums):
        """Power ON nodes ``archi`` and ``*nums``."""
        return self.node_command('start', None, archi, *nums)

    def poweroff(self, archi, *nums):
        """Power OFF nodes ``archi`` and ``*nums``."""
        return self.node_command('stop', None, archi, *nums)

    def _update_profile(self, channel, archi, *nums):
        """Update profile for nodes with archi and channel

        If ``archi`` == 'localhost' just ignore as used in tests.
        """
        if archi == 'localhost':
            return self.retval('', *nums)

        try:
            profile_str = self._sniffer_profile_json(archi, channel)
        except (ValueError, RuntimeError) as err:
            return self.retval('Create profile failed: %s' % err, *nums)

        with tempfile.NamedTemporaryFile() as prof:
            prof.write(profile_str.encode('ascii'))
            prof.flush()
            return self.node_command('profile-load', prof.name, archi, *nums)

    @staticmethod
    def retval(message, *nums):
        """Return value for ``message`` and ``*nums``."""
        return {str(num): message for num in nums}

    @staticmethod
    def _sniffer_profile_json(archi, channel):
        """Return sniffer profile json for ``archi`` and ``channel``.

        Raise ValueError or RuntimeError on error.
        """
        import iotlabcli.profile
        import iotlabcli.helpers
        profiles = {
            'm3': iotlabcli.profile.ProfileM3,
            'a8': iotlabcli.profile.ProfileA8,
        }

        name = 'iotlabmqtt_%u_%s' % (channel, archi)

        try:
            profile_class = profiles[archi]
        except KeyError:
            raise ValueError('Archi: %s not currently supported' % archi)

        profile = profile_class(name, 'dc')
        profile.set_radio('sniffer', [channel])

        return iotlabcli.helpers.json_dumps(profile)

    def node_command(self, command, cmd_opt, archi, *nums):
        """Run IoT-LAB node command and handle errors."""
        assert nums
        try:
            if archi == 'a8':
                return self._opena8_command(command, cmd_opt, archi, *nums)
            else:
                return self._node_command(command, cmd_opt, archi, *nums)
        except (IOError, RuntimeError) as err:
            msg = "IoT-LAB Request '%s' error: '%s'" % (command, err)
            return self.retval(msg, *nums)

    def _opena8_command(self, command, cmd_opt, archi, *nums):
        """ opensshcli make use of IoTLAB API in a different approach
        """
        from iotlabsshcli import open_a8
        if command != 'profile-load':
            nodes = self._a8_nodes_for_num(archi, *nums)
        else:
            nodes = self._nodes_for_num(archi, *nums)

        # The M3 nodes have access to the socat tunnel all the time.
        # This tries to mimic the behavior for the A8 nodes.
        # if  command != 'stop' and command != 'profile-load':
        if command == 'start' or command == 'reset':
            _socat = "nohup /etc/init.d/serial_redirection restart"
            open_a8.run_cmd(self.config_ssh, nodes, _socat, False, False)

        if command == 'start':
            _result = self._opena8_command_start(open_a8, nodes)
            result = _result['run-cmd']
        elif command == 'stop':
            _result = self._opena8_command_stop(open_a8, nodes)
            result = _result['run-cmd']
        elif command == 'reset':
            _result = open_a8.reset_m3(self.config_ssh, nodes)
            result = _result['reset-m3']
        elif command == 'update':
            _result = open_a8.flash_m3(self.config_ssh, nodes, cmd_opt)
            result = _result['flash-m3']
        elif command == 'profile-load':
            import iotlabcli.node
            result = iotlabcli.node.node_command(self.api, command, self.expid,
                                                 nodes, cmd_opt)
        else:
            msg = "Open-A8: Command not supported (%s)" % (command)
            return self.retval(msg, *nums)

        return self._command_result_to_retval(result, archi)

    def _opena8_command_stop(self, a8api, nodes):
        """ opensshcli does not have native function for starting the node """

        command = self.A8M3_OPENOCD_RESET_HALT_CMD
        return a8api.run_cmd(self.config_ssh, nodes, command, False, False)

    def _opena8_command_start(self, a8api, nodes):
        """ opensshcli does not have native function for stopping the node"""

        command = self.A8M3_OPENOCD_RESET_RUN_CMD
        return a8api.run_cmd(self.config_ssh, nodes, command, False, False)

    def _node_command(self, command, cmd_opt, archi, *nums):
        import iotlabcli.node
        nodes = self._nodes_for_num(archi, *nums)
        result = iotlabcli.node.node_command(self.api, command, self.expid,
                                             nodes, cmd_opt)
        return self._command_result_to_retval(result, archi)

    def _nodes_for_num(self, archi, *nums):
        """Return nodes address list for `archi` and `*nums`."""
        return [node_from_infos(archi, num, self.site) for num in nums]

    def _a8_nodes_for_num(self, archi, *nums):
        """Return nodes address list for `archi` and `*nums`."""
        return [a8_node_from_infos(archi, num, self.site) for num in nums]

    def _command_result_to_retval(self, ret_dict, archi):
        readable_value = {'0': '', '1': 'Execution failed on node'}
        result = {}
        for value, nodes_list in ret_dict.items():
            value = readable_value.get(value, value)
            for node in nodes_list:
                archi_, num, site_ = infos_from_node(node)
                numstr = str(num)
                assert (archi_, site_) == (archi, self.site)
                assert numstr not in result
                result[str(num)] = value
        return result


def node_from_infos(archi, num, site):  # pylint:disable=unused-argument
    """Node hostname from infos.

    >>> print(node_from_infos('m3', 1, 'grenoble'))
    m3-1.grenoble.iot-lab.info
    """
    # if archi == 'a8':
    #     fmt = 'node-{archi}-{num}.{site}.iot-lab.info'
    # else:
    #     fmt = '{archi}-{num}.{site}.iot-lab.info'
    fmt = '{archi}-{num}.{site}.iot-lab.info'
    return fmt.format(**locals())

def a8_node_from_infos(archi, num, site):  # pylint:disable=unused-argument
    """Node hostname from infos.

    >>> print(node_from_infos('m3', 1, 'grenoble'))
    m3-1.grenoble.iot-lab.info
    """
    fmt = 'node-{archi}-{num}.{site}.iot-lab.info'
    return fmt.format(**locals())

def infos_from_node(node):
    """Infos from node hostname.

    >>> (infos_from_node('m3-1.grenoble.iot-lab.info') ==
    ...  ('m3', '1', 'grenoble'))
    True

    >>> (infos_from_node('node-a8-1.grenoble.iot-lab.info') ==
    ...  ('node-a8', '1', 'grenoble'))
    True
    """
    first, site = node.split('.', 2)[:2]
    if first.find('a8', 5, 8) >= 0:
        archi = 'a8'
        _, _, numstr = first.rsplit('-', 2)
    else:
        archi, numstr = first.rsplit('-', 1)
    return (archi, numstr, site)
