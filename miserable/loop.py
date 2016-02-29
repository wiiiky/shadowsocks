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


import selectors
import time

from miserable.utils import singleton


class MainLoop(object, metaclass=singleton):

    EVENT_READ = selectors.EVENT_READ
    EVENT_WRITE = selectors.EVENT_WRITE
    EVENT_ERROR = EVENT_WRITE << 1

    def __init__(self):
        self._selector = selectors.DefaultSelector()
        self._timeouts = {}
        self._running = False

    def register(self, fileobj, events, func):
        self._selector.register(fileobj, events, func)

    def unregister(self, fileobj):
        self._selector.unregister(fileobj)

    def modify(self, fileobj, events, func):
        self._selector.modify(fileobj, events, func)

    def add_timeout(self, func, timeout=5):
        self._timeouts[func] = {
            'timeout': int(timeout),
            'updated_at': time.time()
        }

    def remove_timeout(self, func):
        if func in self._timeouts:
            del self._timeouts[func]

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            timeout = None
            now = time.time()
            for func, data in self._timeouts.items():
                if (timeout is None or
                        timeout > (data['updated_at'] + data['timeout'] - now)):
                    timeout = data['timeout']
            events = self._selector.select(timeout=timeout)
            for key, mask in events:
                func = key.data
                func(key.fileobj, mask or self.EVENT_ERROR)
            now = time.time()
            for func, data in list(self._timeouts.items()):
                if now - data['updated_at'] > data['timeout']:
                    data['updated_at'] = now
                    if func():
                        del self._timeouts[func]
