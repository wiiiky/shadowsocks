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

import re
import socket
import ipaddress
from miserable.exception import *


def ip_address(addr):
    """
    convert a ip address string to
    ipaddress.IPv4Address or ipaddress.IPv6Address
    """
    try:
        ipaddr = ipaddress.ip_address(addr)
        if ipaddr.version == 4:
            ipaddr.family = socket.AF_INET
        else:
            ipaddr.family = socket.AF_INET6
        return ipaddr
    except Exception as e:
        return None


def ipv6_address(ipaddr):
    if ipaddr.version == 4:
        ipaddr = ip_address('::ffff:' + ipaddr.compressed)
    return ipaddr


class Address(object):

    def __init__(self, name, port):
        self._ipaddr = ip_address(name)
        self._hostname = name
        self._port = port

    def __eq__(self, other):
        return self._port == other._port and self._ipaddr == other._ipaddr

    @property
    def display(self):
        return '%s:%s' % (tostr(self._hostname), self._port)

    @property
    def family(self):
        return self._ipaddr.family

    @property
    def compressed(self):
        return self._ipaddr.compressed

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port

    @property
    def ipaddr(self):
        return self._ipaddr

    @ipaddr.setter
    def ipaddr(self, ipaddr):
        self._ipaddr = ipaddr

    @property
    def hostname(self):
        return self._hostname


def tostr(data):
    """convert bytes to str"""
    if type(data) is bytes and bytes is not str:
        data = data.decode('utf8')
    return data


def tobytes(data):
    """convert str or int to bytes"""
    if type(data) is int:
        data = chr(data)
    if type(data) is str and str is not bytes:
        data = data.encode('utf8')
    return data


def check_ip(address):
    """
    check to see if the address is a valid IP address
    """
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            address = tostr(address)
            socket.inet_pton(family, address)
            return family
        except (TypeError, ValueError, OSError, IOError):
            pass
    return False


VALID_HOSTNAME = re.compile(br'(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)


def check_hostname(hostname):
    """
    check to see if the hostname is legal
    """
    if len(hostname) > 255:
        return False
    hostname = tobytes(hostname)
    if hostname[-1] == b'.':
        hostname = hostname[:-1]
    return all(VALID_HOSTNAME.match(x) for x in hostname.split(b'.'))


def addr2bytes(ip):
    """convert dotted ip address to bytes"""
    try:
        return socket.AF_INET, socket.inet_pton(socket.AF_INET, ip)
    except OSError:
        return socket.AF_INET6, socket.inet_pton(socket.AF_INET6, ip)


class return_val_if_wouldblock(object):

    def __init__(self, value):
        self._value = value

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (OSError, IOError) as e:
                if exception_wouldblock(e):
                    return self._value
                raise e
        return wrapper


def ignore_inprogress_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (OSError, IOError) as e:
            if not exception_inprogress(e):
                raise e
    return wrapper


class Singleton(type):
    """copy from http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

    usage:

    #Python2
    class MyClass(BaseClass):
        __metaclass__ = Singleton

    #Python3
    class MyClass(BaseClass, metaclass=Singleton):
        pass
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
