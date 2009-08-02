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

class GUI():

    def __init__(self):
        
        self.sleepPrevented = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.timer = None
        self.busFailures = 0

        builder = gtk.Builder()
        builder.add_from_file("GUI.glade")
        
        # It can be tiresome to have to type builder.get_object
        # again and again
        get = builder.get_object
        
        ## IMPORTANT:
        ## status icon must be a instance variable  (ie self.)or else it 
        ## gets thrown out with the garbage, and won't be seen.
        self.status_icon = get("statusicon")

        
        ## popup menu
        self.menu = get("popup_menu")

        ## make the about dialog url clickable
        def url(dialog, link, data=None):
            pass
        gtk.about_dialog_set_url_hook(url, None)


        ## Handle mouse clicks on status_icon
        # left click
        self.status_icon.connect("activate", self.on_L_click)
        # right click
        self.status_icon.connect("popup-menu", self.on_R_click)

        builder.connect_signals(self)

    def on_L_click(self, status_icon, data=None):
        ## toggle whether caffeine is activated
        self.sleepPrevented = not self.sleepPrevented
        ## toggle the icon
        icon_file = ["Empty_Cup.svg", "Full_Cup.svg"][self.sleepPrevented]
        self.status_icon.set_from_file(icon_file)

    def on_R_click(self, status_icon, mbutton, time, data=None):
        ## popdown menu
        self.menu.popup(None, None,
                gtk.status_icon_position_menu, 3, time, self.status_icon)



if __name__ == "__main__":

    main = GUI()
    gtk.main()
