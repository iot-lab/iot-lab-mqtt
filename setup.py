#! /usr/bin/env python
# -*- coding:utf-8 -*-

# This file is a part of IoT-LAB iot-lab-mqtt
# Copyright (C) 2017 INRIA (Contact: admin@iot-lab.info)
# Contributor(s) : see AUTHORS file
#
# This software is governed by the CeCILL license under French law
# and abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# http://www.cecill.info.
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

import os
import itertools
from setuptools import setup, find_packages

PACKAGE = 'iotlabmqtt'
# GPL compatible http://www.gnu.org/licenses/license-list.html#CeCILL
LICENSE = 'CeCILL v2.1'


LONG_DESCRIPTION_FILES = ('README.rst', )


def cat(files, join_str=''):
    """Concatenate `files` content with `join_str` between them."""
    files_content = (open(f).read() for f in files)
    return join_str.join(files_content)


def get_version(package):
    """ Extract package version without importing file
    Importing cause issues with coverage,
        (modules can be removed from sys.modules to prevent this)
    Importing __init__.py triggers importing rest and then requests too

    Inspired from pep8 setup.py
    """
    with open(os.path.join(package, '__init__.py')) as init_fd:
        for line in init_fd:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])  # pylint:disable=eval-used


INSTALL_REQUIRES = ['paho-mqtt>=1.2', 'future', 'packaging']

ENTRY_POINTS = {
    'console_scripts': [
        # Server script
        'iotlab-mqtt-serial = iotlabmqtt.serial:main',
        'iotlab-mqtt-node = iotlabmqtt.node:main [node]',
        'iotlab-mqtt-radiosniffer = iotlabmqtt.radiosniffer:main [sniffer]',
        'iotlab-mqtt-process = iotlabmqtt.process:main',

        # Client script
        'iotlab-mqtt-clients = iotlabmqtt.clients:main',
    ],
}

EXTRAS_REQUIRE = {
    'node': ['iotlabcli>=2.1.0'],
    'sniffer': ['iotlabcli>=2.1.0'],
}

# Sum all dependecies in 'server'
ALL_EXTRAS_DEPS = list(itertools.chain.from_iterable(EXTRAS_REQUIRE.values()))
EXTRAS_REQUIRE['server'] = ALL_EXTRAS_DEPS

setup(
    name=PACKAGE,
    version=get_version(PACKAGE),
    description='Provide access to IoT-LAB experiments as MQTT agents',
    long_description=cat(LONG_DESCRIPTION_FILES, '\n\n'),
    author='IoT-LAB Team',
    author_email='admin@iot-lab.info',
    url='http://www.iot-lab.info',
    license=LICENSE,
    download_url='http://github.com/iot-lab/iot-lab-mqtt/',
    packages=find_packages(),
    include_package_data=True,
    classifiers=['Development Status :: 3 - Alpha',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Environment :: Console',
                 'Topic :: Utilities', ],
    install_requires=INSTALL_REQUIRES,
    entry_points=ENTRY_POINTS,
    extras_require=EXTRAS_REQUIRE,
)
