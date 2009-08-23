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
import commands

import dbus
import threading

import applicationinstance

import caffeine
import utils

class Caffeine(gobject.GObject):

    def __init__(self):
        
        gobject.GObject.__init__(self)
        
        ## convience class for managing configurations
        self.Conf = caffeine.get_configurator()

        #print self.Conf.get("test_option").get_bool()

        ## Makes sure that only one instance of Caffeine is run for
        ## each user on the system.
        self.pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
        self.appInstance = applicationinstance.ApplicationInstance( self.pid_name )

        self.sleepPrevented = False
        self.screenSaverCookie = None
        self.powerManagementCookie = None
        self.timer = None
        self.failTimer = None
        self.source_id = None

        self.note = None
    

    def quit(self):
        """Cancels any timer thread running
        so the program can quit right away.
        """
        if self.failTimer:
            self.failTimer.cancel()

        if self.timer:
            self.timer.cancel()

    ## The following four methods deal with adding the correct syntax
    ## for plural forms of time units. For example, 1 minute and 2
    ## minutes. Will be obsolete once the application is
    ## internationalized, as not all languages use "s" for plural form.
    def _mconcat(self, base, sep, app):
        return (base + sep + app if base else app) if app else base

    def _spokenConcat(self, ls):
        and_str = _(" and ")
        txt, n = '', len(ls)
        for w in ls[0:n-1]:
            txt = self._mconcat(txt, ', ', w)
        return self._mconcat(txt, and_str, ls[n-1])

    def _pluralize(self, name, time):
        names = [_('hour'), _('minute')]
        if time < 1:
            return ""

        if name == "hour":
            if time < 2:
                return "%d %s" % (time, _("hour"))
            if time >= 2:
                return "%d %s" % (time, _("hours"))

        elif name == "minute":
            if time < 2:
                return "%d %s" % (time, _("minute"))
            if time >= 2:
                return "%d %s" % (time, _("minutes"))


        
        plural = ('s' if nb > 1 and nb != 0 else '')
        return ('%d %s%s' % (nb, name, plural) if nb >= 1 else '')

    def _timeDisplay(self, sec):

        hours = sec/3600
        minutes = sec/60 % 60
        ls = []
        ls.append(self._pluralize("hour", hours))
        ls.append(self._pluralize("minute", minutes))

        return self._spokenConcat(ls)


    def _notify(self, message, icon, title="Caffeine"):
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
            self._timeDisplay(time))

        if not self.getActivated():
            self.toggleActivated()


        self._notify(message, caffeine.FULL_ICON_PATH)

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


    def toggleActivated(self):
        """This function may fail to peform the toggling,
        if it cannot find the required bus. In this case, it
        will return False."""
        

        bus = dbus.SessionBus()

        ssProxy = None
        pmProxy = None
        bus_names = bus.list_names()

        probableDE = ""

        # For Gnome
        if 'org.gnome.ScreenSaver' in bus_names:
            ssProxy = bus.get_object('org.gnome.ScreenSaver',
                    '/org/gnome/ScreenSaver')

            self.ssProxy = ssProxy
            probableDE = "Gnome"

        # For KDE
        elif ('org.freedesktop.ScreenSaver' in bus_names and
            'org.freedesktop.PowerManagement.Inhibit' in bus_names):

            ssProxy = bus.get_object(
                    'org.freedesktop.ScreenSaver',
                    '/ScreenSaver')

            pmProxy = bus.get_object(
                    'org.freedesktop.PowerManagement.Inhibit',
                    '/org/freedesktop/PowerManagement/Inhibit')

            probableDE = "KDE"
        # For XScreensaver
        elif "xscreensaver" in utils.getProcesses().keys():
            self._toggleXSS()
            return True
            
        if self.sleepPrevented:
            ### sleep prevention was on now turn it off

            ### Toggle DPMS
            commands.getoutput("xset -dpms")
            
            if self.screenSaverCookie != None:
                ssProxy.UnInhibit(self.screenSaverCookie)

            self.sleepPrevented = False
            print "Caffeine is now dormant; powersaving is re-enabled"

            # If the user clicks on the full coffee-cup to disable 
            # sleep prevention, it should also
            # cancel the timer for timed activation.

            if self.timer != None and self.timer.name != "Expired":

                message = (_("Timed activation cancelled (was set for ") +
                        self._timeDisplay(self.timer.interval) + ")")

                self._notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer.cancel()
                self.timer = None

                

            elif self.timer != None and self.timer.name == "Expired":

                message = (self._timeDisplay(self.timer.interval) +
                    _(" have elapsed; powersaving is re-enabled"))


                self._notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer = None

        else:

            ### Toggle DPMS
            commands.getoutput("xset +dpms")

            if pmProxy:
                self.powerManagementCookie = pmProxy.Inhibit("Caffeine",
                    "User has requested that Caffeine disable"+
                    " the powersaving modes")

            if ssProxy:
                self.screenSaverCookie = ssProxy.Inhibit("Caffeine",
                    "User has requested that Caffeine disable the screen saver")

            self.sleepPrevented = True

            print ("Caffeine is now preventing powersaving modes"+
                " and screensaver activation (" +
                probableDE + ")")


        self.emit("activation-toggled", self.getActivated())
        return True


    def _toggleXSS(self):
        """Toggle whether XScreensaver is activated"""
        
        probableDE = "XScreensaver"
        if self.sleepPrevented:
            ### sleep prevention was on now turn it off
            self.sleepPrevented = False
            print "Caffeine is now dormant; powersaving is re-enabled"

            # If the user clicks on the full coffee-cup to disable 
            # sleep prevention, it should also
            # cancel the timer for timed activation.

            if self.source_id != None:
                gobject.source_remove(self.source_id)

            if self.timer != None and self.timer.name != "Expired":

                message = (_("Timed activation cancelled (was set for ") +
                        self._timeDisplay(self.timer.interval) + ")")

                self._notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer.cancel()
                self.timer = None
                

            elif self.timer != None and self.timer.name == "Expired":

                message = (self._timeDisplay(self.timer.interval) +
                    _(" have elapsed; powersaving is re-enabled"))


                self._notify(message, caffeine.EMPTY_ICON_PATH)

                self.timer = None
        else:

            self.sleepPrevented = True

            def deactivate():
                try:
                    output = commands.getoutput(
                            "xscreensaver-command -deactivate")
                except Exception, data:
                    print data

                return True
        
            # reset the idle timer every 50 seconds.
            self.source_id = gobject.timeout_add(50000, deactivate)

            print ("Caffeine is now preventing powersaving modes"+
                " and screensaver activation (" +
                probableDE + ")")


        self.emit("activation-toggled", self.getActivated())



## register a signal
gobject.signal_new("activation-toggled", Caffeine,
        gobject.SIGNAL_RUN_FIRST, None, [bool])


