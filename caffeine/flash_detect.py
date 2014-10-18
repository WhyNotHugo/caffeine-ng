#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
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


import kaa.metadata
import subprocess
import sys
import os

if __name__ == "__main__":

    try:
        output = \
            subprocess.getoutput("pgrep -f flashplayer | " +
                                 "xargs -I PID find /proc/PID/fd " +
                                 "-lname '/tmp/Flash*'")
        if not bool(output):
            print(1)
            sys.exit(1)

        for filepath in output.split("\n"):
            if filepath != "":
                meta = kaa.metadata.parse(filepath)
                url = meta.url[7:]
                length = str(meta.length)
                iden = str(os.stat(url).st_ino) + length
                print(iden + " " + length.split(".")[0])

    except Exception as data:
        print(2)
        print(data)
        sys.exit(2)
