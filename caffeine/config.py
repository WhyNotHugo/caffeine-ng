#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2009 The Caffeine Developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import gconf

class Configurator(object):
    """ Class for easier setting and retrieving of
    gconf configurations
    """

    def __init__(self):

        self._client = gconf.client_get_default()

        self._configs = {}

    def register_opt(self, name, key_path, default):

        self._configs[name] = key_path
        
        if not self.get(name):
            self.set(name, default)

    def set(self, name, value):
        
        self._client.set_value(self._configs[name], value)

    def get(self, name):

        return self._client.get(self._configs[name])

