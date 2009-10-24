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
import struct

class FLVParsingError(Exception):
    def __init__(self, txt):
        Exception.__init__(self, txt)

def readMetadataArray(f):
    """Pass in a file handle to read an array of mixed types from the FLV file. Most
    data types are ignored, as we are only interested in 'duration' related metadata."""
    arraySize = struct.unpack('>I', f.read(4))[0]
    metadata = {}
    for i in range(0, arraySize):
        metadataNameLen = struct.unpack('>H', f.read(2))[0]
        metadataName = f.read(metadataNameLen)
        metadataValueType = struct.unpack('B', f.read(1))[0]
        if metadataValueType == 0:
            double = struct.unpack('>d', f.read(8))[0]
            metadata[metadataName] = double
        elif metadataValueType == 1:
            f.read(1)
            metadata[metadataName] = "BooleanValueIgnored"
        elif metadataValueType == 2:
            valueStrLen = struct.unpack('>H', f.read(2))[0]
            f.read(valueStrLen)
            metadata[metadataName] = "StringValueIgnored"
        elif metadataValueType == 8:
            ignore = readMetadataArray(f)
            metadata[metadataName] = "MixedArrayIgnored"
        elif metadataValueType == 11:
            ignore = f.read(8)
            metadata[metadataName] = "DateIgnored"
        else:
            raise FLVParsingError("This rudimentary parser can't handle this data type: " + str(metadataValueType))
    return metadata

def getFLVLength(flvFilePath):
    """Returns an integer, the number of seconds that the specified FLV video
    file will play for."""
    with open(flvFilePath, 'rb') as f:
        # Get the first three bytes, and ensure that they are as expected
        sig = f.read(3)
        if sig != 'FLV':
            raise FLVParsingError("'FLV' signature not found at the beginning of the file")

        # Read past some other junk we don't care about
        ignore = f.read(2)
        offset = struct.unpack('>I', f.read(4))[0]
        ignore = f.read(offset - f.tell())

        # Find the metadata tag that we want
        ignore = f.read(4)
        if struct.unpack('B', f.read(1))[0] != 18:
            raise FLVParsingError("Non-metadata tags found; cannot read")
        b1, b2, b3 = struct.unpack('3B', f.read(3))
        tagSize = (b1 << 16) + (b2 << 8) + b3
        ignore = f.read(7)
        namedatatype = struct.unpack('B', f.read(1))[0]
        if namedatatype != 2:
            raise FLVParsingError("Was expecting to find the tag name string; datatype was incorrect")
        len = struct.unpack('>H', f.read(2))[0]
        tagName = f.read(len)
        if tagName != "onMetaData":
            raise FLVParsingError("Did not find expected tag 'onMetaData'")
        valuedatatype = struct.unpack('B', f.read(1))[0]
        if valuedatatype != 8:
            raise FLVParsingError("The onMetaData tag was expected to be type 8 (an array)")

        # Read the array of metadata
        metadata = readMetadataArray(f)
        if metadata.has_key("totalduration"):
            return int(metadata["totalduration"])
        elif metadata.has_key("duration"):
            return int(metadata["duration"])
        else:
            raise FLVParsingError("No duration-related info was found in the file's metadata")

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

