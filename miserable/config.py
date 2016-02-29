# encoding=utf8
#
# Copyright 2015 Wiky L
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import, division, print_function, \
    with_statement


import copy
import json
import argparse
import sys
from miserable.utils import *


class ConfigManager(object):

    def __init__(self):
        self._parser = None
        self._config = None

    @property
    def parser(self):
        if self._parser is None:
            self._parser = self._get_parser()
        return self._parser

    @property
    def config(self):
        if self._config is None:
            self._config = self._get_config()
        return self._config

    @classmethod
    def instance(klass):
        if klass._instance is None:
            klass._instance = klass()
        return klass._instance

    @classmethod
    def get_config(klass):
        return klass.instance().config

    @classmethod
    def get_parser(klass):
        return klass.instance().parser


class Config(dict):
    """always return a copy of config value to make config won't be changed"""

    def __getitem__(self, k):
        return copy.deepcopy(super(Config, self).__getitem__(k))


class LocalConfigManager(ConfigManager):

    _instance = None

    def _get_parser(self):
        description = 'A fast tunnel proxy that helps you bypass firewalls.'
        parser = argparse.ArgumentParser(prog='miserable', add_help=False,
                                         description=description)
        group = parser.add_argument_group('Proxy Options')
        group.add_argument('-c', metavar='CONFIG',
                           type=argparse.FileType('r'),
                           help='path to config file')
        group.add_argument('-s', metavar='SERVER_ADDR', type=str,
                           help='server address, ip or hostname')
        group.add_argument('-p', metavar='SERVER_PORT', type=int,
                           help='server port, default=8388')
        group.add_argument('-b', metavar='LOCAL_ADDR', type=str,
                           help='local binding address, default=127.0.0.1')
        group.add_argument('-l', metavar='LOCAL_PORT', type=int,
                           help='local port, default=1080')
        group.add_argument('-k', metavar='PASSWORD', type=str,
                           help='password')
        group.add_argument('-m', metavar='METHOD', type=str,
                           help='encryption method, default=aes-256-cfb')
        group.add_argument('-t', metavar='TIMEOUT', type=int,
                           help='timeout in seconds, default=300')
        group.add_argument('--fast-open', action='store_true',
                           help='use TCP_FASTOPEN, requires Linux 3.7+',
                           default=None)

        group = parser.add_argument_group('General Options')
        group.add_argument('-h', '--help', action='help',
                           help='show this help message and exit')
        group.add_argument('-v', action='count', help='verbose mode')
        group.add_argument('-d', choices=['start', 'stop', 'restart'],
                           help='daemon mode')
        group.add_argument('--pid-file', metavar='PID_FILE', type=str,
                           help='pid file for daemon mode')
        group.add_argument('--log-file', metavar='LOG_FILE', type=str,
                           help='log file for daemon mode')
        group.add_argument('--user', metavar='USERNAME', type=str,
                           help='username to run as')
        group.add_argument('--version', action='version',
                           help='show version information')
        return parser

    def _get_config(self):
        args = self.parser.parse_args()
        cfg = Config()
        if args.c:
            cfg = json.load(args.c)

        def get_arg(cfg_name, arg_name, default=None):
            """set command line value if specified"""
            if getattr(args, arg_name, None) is not None:
                cfg[cfg_name] = getattr(args, arg_name)
            if cfg_name not in cfg:
                cfg[cfg_name] = default
            if cfg[cfg_name] is None:
                print('you must specify argument -%s' % arg_name)
                self.parser.print_help()
                sys.exit(0)

        cfgarg = (
            ('remote_address', 's', None),
            ('remote_port', 'p', 8388),
            ('local_address', 'b', '127.0.0.1'),
            ('local_port', 'l', 1080),
            ('password', 'k', None),
            ('method', 'm', 'aes-256-cfb'),
            ('timeout', 't', 300),
            ('fast_open', 'fast_open', False),
            ('daemon', 'd', ''),
            ('pid-file', 'pid_file', '/tmp/miserable.pid'),
            ('log-file', 'log_file', '/tmp/miserable.log'),
            ('user', 'user', ''),
            ('verbose', 'v', 0)
        )
        for i in cfgarg:
            get_arg(i[0], i[1], i[2])

        cfg['local_address'] = Address(cfg['local_address'], cfg['local_port'])
        if not cfg['local_address'].ipaddr:
            print('invalid local address!')
            sys.exit(1)
        cfg['remote_address'] = Address(cfg['remote_address'],
                                        cfg['remote_port'])
        return cfg
