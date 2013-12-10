# -*- coding: utf-8 -*-
#
# Copyright © 2009-2013 The Caffeine Developers
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


from gi.repository import Gtk, GObject, Notify
import os
import os.path
import commands
import sys
import dbus

import applicationinstance
import caffeine
import utils
import procmanager
import logging


os.chdir(os.path.abspath(os.path.dirname(__file__)))


class Caffeine(GObject.GObject):

    def __init__(self):
        
        GObject.GObject.__init__(self)
        
        ## object to manage processes to activate for.
        self.ProcMan = caffeine.get_ProcManager()
        
        ## Status string.
        self.status_string = ""

        ## Makes sure that only one instance of Caffeine is run for
        ## each user on the system.
        self.pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
        self.appInstance = applicationinstance.ApplicationInstance( self.pid_name )

        # Set to True when sleep mode has been successfully inhibited somehow.
        self.sleepIsPrevented = False

        self.preventedForProcess = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.inhibit_id = None

        # prevent trying to check for it before it's created at self._notify
        self.ssProxy = None

        self.note = None
        
        ## check for processes to activate for.
        id = GObject.timeout_add(10000, self._check_for_process)
        
        print self.status_string


    def _check_for_process(self):
        activate = False
        for proc in self.ProcMan.get_process_list():
            if utils.isProcessRunning(proc):

                activate = True

                if self.preventedForProcess or not self.getActivated():
                    
                    logging.info("Caffeine has detected that the process '" + proc + "' is running, and will auto-activate")

                    self.setActivated(True)

                    self.preventedForProcess = True
                else:

                    logging.info("Caffeine has detected that the process '"+
                    proc + "' is running, but will NOT auto-activate"+
                    " as Caffeine has already been activated for a different"+
                    " reason.")


        ### No process in the list is running, deactivate.
        if not activate and self.preventedForProcess:
            logging.info("Caffeine had previously auto-activated for a process, but that process is no longer running; deactivating...")
            self.setActivated(False)

        return True

    def _notify(self, message, icon, title="Caffeine"):
        """Easy way to use pynotify"""
        try:

            Notify.init("Caffeine")
            if self.note:
                self.note.update(title, message, icon)
            else:
                self.note = Notify.Notification.new(title, message, icon)
            
            ## Notify OSD doesn't seem to work when sleep is prevented
            if (self.screenSaverCookie != None and self.sleepIsPrevented and
                self.ssProxy is not None):
                self.ssProxy.UnInhibit(self.screenSaverCookie)

            self.note.show()

            if (self.screenSaverCookie != None and self.sleepIsPrevented and
                self.ssProxy is not None):
                self.screenSaverCookie = self.ssProxy.Inhibit("Caffeine",
               "User has requested that Caffeine disable the screen saver")

        except Exception, e:
            logging.error("Exception occurred:\n" + " " + str(e))
            logging.error("Exception occurred attempting to display message:\n" + message)
        finally:
            return False

    def getActivated(self):
        return self.sleepIsPrevented

    def _deactivate(self, note):
        self.timer.name = "Expired"
        self.toggleActivated(note=note)

    
    def setActivated(self, activate, note=True):
        if self.getActivated() != activate:
            self.toggleActivated(note)

    def toggleActivated(self, note=True):
        """This function toggles the inhibition of the screensaver and powersaving
        features of the current computer."""

        self.preventedForProcess = False
        
        if self.sleepIsPrevented:
            ### sleep prevention was on now turn it off

            logging.info("Caffeine is now dormant; powersaving is re-enabled")
            self.status_string = _("Caffeine is dormant; powersaving is enabled")

        self._performTogglingActions()

        if self.status_string == "":
            self.status_string = (_("Caffeine is preventing powersaving modes and screensaver activation"))
        
        self.emit("activation-toggled", self.getActivated(),
                self.status_string)
        self.status_string = ""
        

    def _performTogglingActions(self):
        """This method performs the actions that affect the screensaver and
        powersaving."""

        self._toggle()

        if self.sleepIsPrevented == False:
            logging.info("Caffeine is now preventing powersaving modes"+
                " and screensaver activation")

        self.sleepIsPrevented = not self.sleepIsPrevented

    def _toggle(self):
        """Toggle the screensaver and powersaving with the interfaces used by freedesktop.org."""

        bus = dbus.SessionBus()
        self.susuProxy = bus.get_object('org.freedesktop.ScreenSaver', '/org/freedesktop/ScreenSaver')
        self.iface = dbus.Interface(self.susuProxy, 'org.freedesktop.ScreenSaver')
        if self.sleepIsPrevented:
            if self.screenSaverCookie != None:
                self.iface.UnInhibit(self.screenSaverCookie)
        else:
            self.screenSaverCookie = self.iface.Inhibit('net.launchpad.caffeine', "User has requested that Caffeine disable the screen saver")

## register a signal
GObject.signal_new("activation-toggled", Caffeine,
        GObject.SignalFlags.RUN_FIRST, None, [bool, str])
