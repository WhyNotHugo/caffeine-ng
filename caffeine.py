#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright © 2009 Brad Smith
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

VERSION_STRING = "0.1"
EMPTY_ICON_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], "Empty_Cup.svg"))
FULL_ICON_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], "Full_Cup.svg"))

TIMER_OPTIONS_LIST = [("5 minutes", 300.0), ("10 minutes", 600.0), ("15 minutes", 900.0), ("30 minutes", 1800.0),
                      ("1 hour", 3600.0), ("2 hours", 7200.0), ("3 hours", 10800.0), ("4 hours", 14400.0)]

sleepPrevented = False
screenSaverCookie = None
powerManagementCookie = None
timer = None
busFailures = 0

# GUI callbacks
def sleepPreventionPressed(widget, data = None):
    global sleepPrevented
    if sleepPrevented:
        widget.set_from_file(EMPTY_ICON_PATH)
    else:
        widget.set_from_file(FULL_ICON_PATH)
    toggleSleepPrevention()

def showMenu(widget, button, time, data = None):
    if button == 3 and data != None:
        data.show_all()
        data.popup(None, None, None, 3, time)

def displayAboutBox(widget, data = None):
    about = gtk.AboutDialog()
    about.set_program_name("Caffeine")
    about.set_version(VERSION_STRING)
    about.set_copyright("Copyright © 2009 Brad Smith")
    about.set_icon(gtk.gdk.pixbuf_new_from_file(FULL_ICON_PATH))

    about.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(FULL_ICON_PATH, 48, 48))
    about.set_comments("""An application to temporarily prevent the activation of both the screen saver and the "sleep" powersaving mode.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
""")
    about.set_website("http://pragmattica.wordpress.com")
    about.run()
    about.destroy()

def quitButtonPressed(widget, data = None):
    gtk.main_quit()
    quitCaffeine()

# Other procedures
def quitCaffeine():
    """Perform final operations before program termination."""
    global sleepPrevented
    if sleepPrevented:
        toggleSleepPrevention()
    print "Caffeine exiting"

def toggleSleepPrevention():
    """This function will call 'attemptToToggleSleepPrevention', repeatedly if necessary. If it doesn't
    succeed in toggling the sleep prevention after a minute or so, it will display an error dialog box
    and kill the program. This is needed because it is possible for the user to click the Caffeine icon
    as soon as they log in, which may be before the required busses/daemons have started up."""
    global busFailures
    attemptResult = attemptToToggleSleepPrevention()
    if attemptResult == False:
        busFailures += 1
        if busFailures <= 9:
            print "Failed to establish a connection with a required bus (" + str(busFailures) + " failures so far)"
            print "This may be due to the required subsystem not having completed its initialization. Will try again in 10 seconds."
            failTimer = threading.Timer(10, toggleSleepPrevention)
            failTimer.start()
        else:
            print "Could not connect to the bus, even after repeated attempts. This program will now terminate."
            errMsg = "Error: couldn't find bus to allow inhibiting of the screen saver.\n\n" \
                "Please visit the web-site listed in the 'About' dialog of this application " \
                "and check for a newer version of the software."
            errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=errMsg)
            errDlg.run()
            errDlg.destroy()
            sys.exit(2)
    else:
        if busFailures != 0:
            print "Connection to the bus succeeded; resuming normal operation"
        busFailures = 0

def attemptToToggleSleepPrevention():
    """This function may fail to peform the toggling, if it cannot find the required bus. In this case, it
    will return False."""
    global sleepPrevented, screenSaverCookie, powerManagementCookie, timer
    bus = dbus.SessionBus()
    if sleepPrevented:
        ssProxy = None
        if 'org.gnome.ScreenSaver' in bus.list_names(): # For Gnome
            ssProxy = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
        elif 'org.freedesktop.ScreenSaver' in bus.list_names() and \
             'org.freedesktop.PowerManagement.Inhibit' in bus.list_names(): # For KDE
            ssProxy = bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
            pmProxy = bus.get_object('org.freedesktop.PowerManagement.Inhibit', '/org/freedesktop/PowerManagement/Inhibit')
            if powerManagementCookie != None:
                pmProxy.UnInhibit(powerManagementCookie)
        else:
            return False

        if screenSaverCookie != None:
            ssProxy.UnInhibit(screenSaverCookie)

        sleepPrevented = False
        print "Caffeine is now dormant; powersaving is re-enabled"

        # If the user clicks on the full coffee-cup to disable sleep prevention, it should also
        # cancel the timer for timed activation.
        if timer != None:
            print "Cancelling the 'timed activation' timer (was set for " + str(timer.interval) + " seconds)"
            timer.cancel()
            timer = None
    else:
        probableWindowManager = ""
        ssProxy = None
        if 'org.gnome.ScreenSaver' in bus.list_names(): # For Gnome
            probableWindowManager = "Gnome"
            ssProxy = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
        elif 'org.freedesktop.ScreenSaver' in bus.list_names() and \
             'org.freedesktop.PowerManagement.Inhibit' in bus.list_names(): # For KDE
            probableWindowManager = "KDE"
            ssProxy = bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
            pmProxy = bus.get_object('org.freedesktop.PowerManagement.Inhibit', '/org/freedesktop/PowerManagement/Inhibit')
            powerManagementCookie = pmProxy.Inhibit("Caffeine", "User has requested that Caffeine disable the powersaving modes")
        else:
            return False

        screenSaverCookie = ssProxy.Inhibit("Caffeine", "User has requested that Caffeine disable the screen saver")

        sleepPrevented = True
        print "Caffeine is now preventing powersaving modes and screensaver activation (" + probableWindowManager + ")"
        return True

# Simulates a click to activate caffeine, then runs activation()
# after enough time has passed. Runs in another thread, so the script
# can continue anyway.
def timedActivation(self, seconds):
    global sleepPrevented, statusIcon, timer
    print "User has requested timed activation; powersaving will revert to normal after " + str(seconds) + " seconds"
    if sleepPrevented == False:
        sleepPreventionPressed(statusIcon)
    if timer != None:
        print "Cancelling the previous 'timed activation' timer (was set for " + str(timer.interval) + " seconds)"
        timer.cancel()
    timer = threading.Timer(seconds, activation)
    timer.start()

def activation():
    global sleepPrevented, statusIcon, timer
    print "Timed activation period has expired (" + str(timer.interval) + " seconds); Caffeine will now deactivate"
    timer = None
    if sleepPrevented == True:
        sleepPreventionPressed(statusIcon)

def main():
    global statusIcon
    statusIcon = gtk.StatusIcon()

    # Creating submenu
    submenu = gtk.Menu()
    for (l, t) in TIMER_OPTIONS_LIST:
        menuItem = gtk.MenuItem(label=l)
        menuItem.connect('activate', timedActivation, t)
        submenu.append(menuItem)

    menu = gtk.Menu()
    menuItem = gtk.MenuItem(label="Activate for")
    menuItem.set_submenu(submenu)
    menu.append(menuItem)
    menuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
    menuItem.connect('activate', displayAboutBox)
    menu.append(menuItem)
    menuItem = gtk.ImageMenuItem(gtk.STOCK_QUIT)
    menuItem.connect('activate', quitButtonPressed)
    menu.append(menuItem)

    statusIcon.set_from_file(EMPTY_ICON_PATH)
    statusIcon.set_tooltip("Click the coffee cup to disable the screen saver and prevent your computer from entering sleep mode")
    statusIcon.connect('activate', sleepPreventionPressed)
    statusIcon.connect('popup-menu', showMenu, menu)
    gtk.gdk.threads_init()
    try:
        gtk.main()
    except KeyboardInterrupt:
        quitCaffeine()

if __name__ == "__main__":
    main()
