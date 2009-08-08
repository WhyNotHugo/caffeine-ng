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


import gtk
import gobject
import os
import pynotify

import dbus
import threading

import applicationinstance

import caffeine

class Caffeine(gobject.GObject):

    def __init__(self):
        
        gobject.GObject.__init__(self)
        
        ## convience class for managing configurations
        self.Conf = caffeine.get_configurator()

        print self.Conf.get("test_option").get_bool()

        ## Makes sure that only one instance of Caffeine is run for
        ## each user on the system.
        self.pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
        self.appInstance = applicationinstance.ApplicationInstance( self.pid_name )

        self.sleepPrevented = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.timer = None

        self.note = None
    
    ## The following four methods deal with adding the corrext syntax 
    ## for plural forms of time units. For example, 1 minute and 2 
    ## minutes. Will be obsolete once the application is 
    ## internationalized, as not all languages use "s" for plural form. 
    def mconcat(self, base, sep, app):
        return (base + sep + app if base else app) if app else base

    def spokenConcat(self, ls):
        txt, n = '', len(ls)
        for w in ls[0:n-1]:
            txt = self.mconcat(txt, ', ', w)
        return self.mconcat(txt, ' and ', ls[n-1])

    def decline(self, name, nb):
        plural = ('s' if nb > 1 and nb != 0 else '')
        return ('%d %s%s' % (nb, name, plural) if nb >= 1 else '')

    def timeDisplay(self, sec):
        names = [_('hour'), _('minute'), _('second')]
        tvalues = sec/3600, sec/60 % 60, sec % 60
        ls = list(self.decline(name, n) for name, n in zip(names, tvalues))
        return self.spokenConcat(ls)


    def notify(self, message, icon, title="Caffeine"):
        """Easy way to use pynotify"""
        try:

            pynotify.init("Caffeine")
            if self.note:
                self.note.update(title, message, icon)
            else:
                self.note = pynotify.Notification(title, message, icon)
            
            ## Notify OSD doesn't seem to work when sleep is prevented
            if self.screenSaverCookie != None and self.sleepPrevented:
                self.ssProxy.UnInhibit(self.screenSaverCookie)

            self.note.show()

            if self.screenSaverCookie != None and self.sleepPrevented:
                self.screenSaverCookie = self.ssProxy.Inhibit("Caffeine",
               "User has requested that Caffeine disable the screen saver")

        except:
            print _("Exception occurred")
            print message
        finally:
            return False


    def getActivated(self):
        return self.sleepPrevented

    def timedActivation(self, time):
        """Calls toggleActivated after the number of seconds
        specified by time has passed.
        """
        message = (_("Timed activation set; ")+
            _("Caffeine will prevent powersaving for the next ") +
            self.timeDisplay(time))

        if not self.getActivated():
            self.toggleActivated()
        

        self.notify(message, caffeine.FULL_ICON_PATH)

        ## and deactivate after time has passed.
        ## Stop already running timer
        if self.timer:
            self.timer.cancel()

        self.timer = threading.Timer(time, self._deactivate)
        self.timer.name = "Active"
        self.timer.start()

    
    def _deactivate(self):
        self.timer.name = "Expired"
        self.toggleActivated()

    def toggleActivated(self, busFailures=0):
        print "toggleActivated"
        attemptResult = self._toggleActivated()
        if attemptResult == False:
            busFailures += 1
            if busFailures < 12:
                print "Failed to establish a connection with a required bus (" + str(busFailures) + " failures so far)"
                print "This may be due to the required subsystem not having completed its initialization. Will try again in 10 seconds."
                failTimer = threading.Timer(10, self.toggleActivated,
                        args=[busFailures])
                failTimer.start()
            else:
                print "Could not connect to the bus, even after repeated attempts. This program will now terminate."
                errMsg = _("Error: couldn't find bus to allow inhibiting"
                        "of the screen saver.\n\n"+
                    "Please visit the web-site listed in the "
                    "'About' dialog of this application "
                    "and check for a newer version of the software.")

                errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=errMsg)
                errDlg.run()
                errDlg.destroy()
                sys.exit(2)
        else:
            self.emit("activation-toggled", self.getActivated())
            if busFailures != 0:
                print "Connection to the bus succeeded; resuming normal operation"


    def _toggleActivated(self):
        """This function may fail to peform the toggling,
        if it cannot find the required bus. In this case, it
        will return False."""

        bus = dbus.SessionBus()

        ssProxy = None
        pmProxy = None
        bus_names = bus.list_names()

        probableWindowManager = ""
        # For Gnome
        if 'org.gnome.ScreenSaver' in bus_names:
            ssProxy = bus.get_object('org.gnome.ScreenSaver',
                    '/org/gnome/ScreenSaver')

            self.ssProxy = ssProxy
            probableWindowManager = "Gnome"

        # For KDE
        elif ('org.freedesktop.ScreenSaver' in bus_names and
            'org.freedesktop.PowerManagement.Inhibit' in bus_names):

            ssProxy = bus.get_object(
                    'org.freedesktop.ScreenSaver',
                    '/ScreenSaver')

            pmProxy = bus.get_object(
                    'org.freedesktop.PowerManagement.Inhibit',
                    '/org/freedesktop/PowerManagement/Inhibit')

            probableWindowManager = "KDE"
        else:
            return False
        
        if self.sleepPrevented:
            
            if self.screenSaverCookie != None:
                ssProxy.UnInhibit(self.screenSaverCookie)

            self.sleepPrevented = False
            print "Caffeine is now dormant; powersaving is re-enabled"

            # If the user clicks on the full coffee-cup to disable 
            # sleep prevention, it should also
            # cancel the timer for timed activation.

            if self.timer != None and self.timer.name != "Expired":

                message = (_("Timed activation cancelled (was set for ") +
                        self.timeDisplay(self.timer.interval) + ")")

                #gobject.idle_add(self.notify, message, caffeine.EMPTY_ICON_PATH)
                self.notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer.cancel()
                self.timer = None
                

            elif self.timer != None and self.timer.name == "Expired":

                message = (self.timeDisplay(self.timer.interval) + 
                    _(" have elapsed; powersaving is re-enabled"))

    
                self.notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer = None
        else:

            if pmProxy:
                self.powerManagementCookie = pmProxy.Inhibit("Caffeine",
                    "User has requested that Caffeine disable"+
                    " the powersaving modes")

            self.screenSaverCookie = ssProxy.Inhibit("Caffeine",
               "User has requested that Caffeine disable the screen saver")

            self.sleepPrevented = True

            print ("Caffeine is now preventing powersaving modes"+
                " and screensaver activation (" +
                probableWindowManager + ")")

        return True


## register a signal
gobject.signal_new("activation-toggled", Caffeine,
        gobject.SIGNAL_RUN_FIRST, None, [bool])


