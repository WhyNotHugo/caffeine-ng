#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2009 Brad Smith, Tommy Brunn
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

import os, sys
import gtk
import pygtk
import dbus
import threading
from applicationinstance import *
try:
    import pynotify
except:
    print "Please install pynotify"

class Main():
    def __init__(self):
        sleepPrevented = False
        screenSaverCookie = None
        powerManagementCookie = None
        timer = None
        busFailures = 0
        gui = GUI()
        
class GUI():
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("GUI.xml")
        builder.connect_signals(self)
        #Just to keep it running
        while True:
            pass

if __name__ == "__main__":
    main = Main()
