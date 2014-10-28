# Copyright (c) 2014 Hugo Osvaldo Barrera
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


def getProcessName(pid):
    """Gets process name from process id"""

    truncProcessName = open("/proc/%s/status" % pid).readline()[6:-1]
    processName = truncProcessName

    line = open("/proc/%s/cmdline" % pid).readline()
    parts = line.split("\x00")
    for part in parts:
        cmdName = part.split("/")[-1]

        if cmdName.startswith(truncProcessName):
            processName = cmdName

    return processName


def getProcesses():

    processList = []

    for pid in os.listdir("/proc/"):
        try:
            pid = int(pid)
        except:
            continue

        try:
            processName = getProcessName(pid).lower()
        except:
            continue

        processList.append((processName, pid))

    return processList


def isProcessRunning(name):

    for proc_name, pid in getProcesses():
        if name == proc_name:
            return True

    return False
