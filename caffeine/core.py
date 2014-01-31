# -*- coding: utf-8 -*-
#
# Copyright © 2009-2014 The Caffeine Developers
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


from gi.repository import GObject
import os
import os.path
import re
import subprocess
import dbus
import logging

import applicationinstance


os.chdir(os.path.abspath(os.path.dirname(__file__)))


class Caffeine(GObject.GObject):

    def __init__(self):
        GObject.GObject.__init__(self)
        
        ## Status string.
        self.status_string = ""

        ## Makes sure that only one instance of Caffeine is run for
        ## each user on the system.
        self.pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
        self.appInstance = applicationinstance.ApplicationInstance( self.pid_name )

        # Set to True when sleep mode has been successfully inhibited somehow.
        self.sleepIsPrevented = False

        self.preventedForFullScreen = False
        self.screenSaverCookie = None

        # Add hook for full-screen check
        GObject.timeout_add(50000, self._check_for_fullscreen) # FIXME: Calculate timeout from power settings (idle timeout minus a few seconds)
        
        print self.status_string


    def _check_for_fullscreen(self):
        # Don't check full-screen if we're manually activated
        if self.getActivated() and not self.preventedForFullScreen:
            return True

        activate = False

        # Enumerate the attached screens
        displays = []

        # xvinfo returns 1 on normal exit: https://bugs.freedesktop.org/show_bug.cgi?id=74227
        p = subprocess.Popen(['xvinfo'], stdout=subprocess.PIPE)
        p.wait()
        if 0 <= p.returncode <= 1:
            # Parse output
            for l in p.stdout.read().splitlines():
                m = re.match('screen #([0-9]+)$', str(l))
                if m:
                    displays.append(m.group(1))

                    # Loop through every display looking for a fullscreen window
                    for d in displays:
                        # get ID of active window (the focussed window)
                        out = subprocess.check_output(['xprop', '-display', ':0.' + d, '-root', '-f', '_NET_ACTIVE_WINDOW', '32x', ' $0', '_NET_ACTIVE_WINDOW'])
                        m = re.match('.* (.*)$', str(out))
                        assert(m)
                        active_win = m.group(1)
                    
                        if active_win != "0x0": # Skip invalid window IDs
                            # Check whether window is fullscreen
                            out = subprocess.check_output(['xprop', '-display' ,':0.' + d, '-id', active_win, '_NET_WM_STATE'])
                            m = re.search('_NET_WM_STATE_FULLSCREEN', str(out))
                            if m:
                                activate = True

        if activate and not self.getActivated():
            logging.info("Caffeine has detected a full-screen window, and will auto-activate")
        elif not activate and self.getActivated():
            logging.info("Caffeine detects no full-screen window and is not otherwise activated; deactivating...")
        self.setActivated(activate)
        self.preventedForFullScreen = activate

        return True


    def getActivated(self):
        return self.sleepIsPrevented

    def _deactivate(self):
        self.toggleActivated()

    
    def setActivated(self, activate):
        if self.getActivated() != activate:
            self.toggleActivated()

    def toggleActivated(self):
        """This function toggles the inhibition of desktop idleness."""

        self.preventedForFullScreen = False

        if self.sleepIsPrevented:
            logging.info("Caffeine is now dormant")
            self.status_string = _("Caffeine is dormant")

        self._performTogglingActions()

        if self.status_string == "":
            self.status_string = _("Caffeine is preventing desktop idleness")
        
        self.emit("activation-toggled", self.getActivated(),
                self.status_string)
        self.status_string = ""
        

    def _performTogglingActions(self):
        """This method performs the actions that affect desktop idleness."""

        self._toggle()

        if self.sleepIsPrevented == False:
            logging.info("Caffeine is now preventing desktop idleness")

        self.sleepIsPrevented = not self.sleepIsPrevented

    def _toggle(self):
        """Toggle inhibition of desktop idleness with the freedesktop.org interface."""

        bus = dbus.SessionBus()
        self.susuProxy = bus.get_object('org.freedesktop.ScreenSaver', '/org/freedesktop/ScreenSaver')
        self.iface = dbus.Interface(self.susuProxy, 'org.freedesktop.ScreenSaver')
        if self.sleepIsPrevented:
            if self.screenSaverCookie != None:
                self.iface.UnInhibit(self.screenSaverCookie)
        else:
            self.screenSaverCookie = self.iface.Inhibit('net.launchpad.caffeine', "Caffeine is inhibiting desktop idleness")

## register a signal
GObject.signal_new("activation-toggled", Caffeine,
        GObject.SignalFlags.RUN_FIRST, None, [bool, str])
