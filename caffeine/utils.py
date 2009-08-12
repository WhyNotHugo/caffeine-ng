#!/usr/bin/env python

import os, sys

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
