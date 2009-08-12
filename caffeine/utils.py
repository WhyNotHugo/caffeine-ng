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

import os
import sys

def getProcessName(pid):
    """Gets process name from process id"""

    processName = file("/proc/%s/status" % pid).readline()[6:-1]

    return processName



def getProcesses():

    processDict = {}

    for pid in os.listdir("/proc/"):

        try:

            pid = int(pid)

        except:

            continue

        try:

            processName = getProcessName(pid)

        except:

            continue

        processDict[processName] = pid

    return processDict
