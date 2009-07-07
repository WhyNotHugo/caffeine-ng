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
from applicationinstance import *
try:
    import pynotify
except:
    print "Please install pynotify"

VERSION_STRING = "0.2"
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

class DurationSettings:
    def ok_cb(self,widget,data=None):
        self.hour=int(self.spinner_hour.get_value())
        self.minute=int(self.spinner_minute.get_value())
        self.second=int(self.spinner_second.get_value())
        self.window.hide()
        self.report_cb(self)

    def report_cb(self,widget,data=None):
        self.time = self.hour*60*60 + self.minute*60 + self.second
        timedActivation(widget, self.time)

    def initialize(self):
        self.hour=0
        self.minute=0
        self.second=0

    def cancel_cb(self,widget,data=None):
        self.initialize()
        self.window.hide()

    def show(self):
        self.window.show_all()

    def on_delete_event(self, widget, data = None):
        self.cancel_cb(self)
        return True

    def __init__(self, data = None):
        self.initialize()
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("delete_event", self.on_delete_event)
        self.window.set_title("Caffeine")
        self.window.set_icon_from_file(FULL_ICON_PATH)

        main_vbox = gtk.VBox(False, 5)
        main_vbox.set_border_width(10)
        self.window.add(main_vbox)

        frame = gtk.Frame("Duration")
        main_vbox.pack_start(frame, True, True, 0)

        vbox = gtk.VBox(False, 0)
        vbox.set_border_width(5)
        frame.add(vbox)
        hbox = gtk.HBox(False, 0)
        vbox.pack_start(hbox, True, True, 5)

        vbox2 = gtk.VBox(False, 0)
        hbox.pack_start(vbox2, True, True, 5)

        label = gtk.Label("Hours:")
        label.set_alignment(0, 0.5)
        vbox2.pack_start(label, False, True, 0)

        adj = gtk.Adjustment(0.0, 0.0, 99.0, 1.0, 5.0, 0.0)
        self.spinner_hour = gtk.SpinButton(adj, 0, 0)
        self.spinner_hour.set_wrap(True)
        vbox2.pack_start(self.spinner_hour, False, True, 0)

        vbox2 = gtk.VBox(False, 0)
        hbox.pack_start(vbox2, True, True, 5)

        label = gtk.Label("Minutes:")
        label.set_alignment(0, 0.5)
        vbox2.pack_start(label, False, True, 0)

        adj = gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 5.0, 0.0)
        self.spinner_minute = gtk.SpinButton(adj, 0, 0)
        self.spinner_minute.set_wrap(True)
        vbox2.pack_start(self.spinner_minute, False, True, 0)

        vbox2 = gtk.VBox(False, 0)
        hbox.pack_start(vbox2, True, True, 5)

        label = gtk.Label("Seconds:")
        label.set_alignment(0, 0.5)
        vbox2.pack_start(label, False, True, 0)

        adj = gtk.Adjustment(0.0, 0.0, 59.0, 1.0, 100.0, 0.0)
        self.spinner_second = gtk.SpinButton(adj, 0, 0)
        self.spinner_second.set_wrap(True)
        self.spinner_second.set_size_request(55, -1)
        vbox2.pack_start(self.spinner_second, False, True, 0)

        hbox = gtk.HBox(False, 0)
        main_vbox.pack_start(hbox, False, True, 0)

        button = gtk.Button(stock="OK")
        button.connect("clicked", self.ok_cb)
        hbox.pack_start(button, True, True, 5)
        button = gtk.Button(stock="Cancel")
        button.connect("clicked", self.cancel_cb)
        hbox.pack_start(button, True, True, 5)

def setDuration(widget):
    global durationSettings
    durationSettings.show()

def setOtherDuration(widget):
    time = hours*60*60 + minutes*60 + seconds
    timedActivation(widget, time)
    
def notify(message, icon, title="Caffeine"):
    """Easy way to use pynotify"""
    try:
        pynotify.init("Caffeine")
        n = pynotify.Notification(title, message, icon)
        n.show()
    except:
        print message

def mconcat(base, sep, app):
    return (base + sep + app if base else app) if app else base
        
def spokenConcat(ls):
    txt, n = '', len(ls)
    for w in ls[0:n-1]:
        txt = mconcat(txt, ', ', w)
    return mconcat(txt, ' and ', ls[n-1])

def decline(name, nb):
    plural = ('s' if nb > 1 and nb != 0 else '')
    return ('%d %s%s' % (nb, name, plural) if nb >= 1 else '')

def timeDisplay(sec):
    names = ['hour', 'minute', 'second']
    tvalues = sec/3600, sec/60 % 60, sec % 60
    ls = list(decline(name, n) for name, n in zip(names, tvalues))
    return spokenConcat(ls)
    
def getProcessName(pid):
    """Gets process name from process id"""
    processName = file("/proc/%s/status" % pid).readline()[6:-1]
    return processName
    
def processList():
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

def quitButtonPressed(widget, data = None):
    gtk.main_quit()
    quitCaffeine()

# Other procedures
def quitCaffeine():
    """Perform final operations before program termination."""
    global sleepPrevented, appInstance
    if sleepPrevented:
        toggleSleepPrevention()
    appInstance.exitApplication()
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
            message = "Cancelling timer (was set for " + timeDisplay(timer.interval) + ")"
            notify(message, EMPTY_ICON_PATH)
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
    message = "Timed activation set; powersaving will revert to normal after " + timeDisplay(seconds)
    notify(message, FULL_ICON_PATH)
    if sleepPrevented == False:
        sleepPreventionPressed(statusIcon)
    if timer != None:
        print "Cancelling the previous 'timed activation' timer (was set for " + timeDisplay(timer.interval) + ")"
        timer.cancel()
    timer = threading.Timer(seconds, activation)
    timer.start()

def activation():
    global sleepPrevented, statusIcon, timer
    message = "Timed activation period has expired (" + timeDisplay(timer.interval) + ")"
    notify(message, EMPTY_ICON_PATH)
    timer.cancel()
    if sleepPrevented == True:
        sleepPreventionPressed(statusIcon)

def main():
    global statusIcon, durationSettings, appInstance
    appInstance = ApplicationInstance( '/tmp/caffeine.pid' )
    statusIcon = gtk.StatusIcon()
    durationSettings = DurationSettings()
    # Creating submenu
    submenu = gtk.Menu()
    for (l, t) in TIMER_OPTIONS_LIST:
        menuItem = gtk.MenuItem(label=l)
        menuItem.connect('activate', timedActivation, t)
        submenu.append(menuItem)
    menuItem = gtk.MenuItem(label="Other...")
    menuItem.connect('activate', setDuration)
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
