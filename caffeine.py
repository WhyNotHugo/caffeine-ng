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

VERSION_STRING = "0.1"
EMPTY_ICON_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], "Empty_Cup.svg"))
FULL_ICON_PATH = os.path.abspath(os.path.join(os.path.split(__file__)[0], "Full_Cup.svg"))

sleepPrevented = False
screenSaverCookie = None

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
	global sleepPrevented, screenSaverCookie
	bus = dbus.SessionBus()
	if sleepPrevented:
		ssProxy = None
		if 'org.gnome.ScreenSaver' in bus.list_names(): # For Gnome
			ssProxy = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
		elif 'org.freedesktop.ScreenSaver' in bus.list_names(): # For KDE and others
			ssProxy = bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
		else:
			errMsg = "Error: couldn't find bus to allow re-enabling of the screen saver.\n\n" \
				"Please visit the web-site listed in the 'About' dialog of this application " \
				"and check for a newer version of the software."
			errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=errMsg)
			errDlg.run()
			errDlg.destroy()
			sys.exit(1)

		if screenSaverCookie != None:
			ssProxy.UnInhibit(screenSaverCookie)
		sleepPrevented = False
		print "Caffiene is now dormant; powersaving is re-enabled"
	else:
		ssProxy = None
		if 'org.gnome.ScreenSaver' in bus.list_names(): # For Gnome
			ssProxy = bus.get_object('org.gnome.ScreenSaver', '/org/gnome/ScreenSaver')
		elif 'org.freedesktop.ScreenSaver' in bus.list_names(): # For KDE and others
			ssProxy = bus.get_object('org.freedesktop.ScreenSaver', '/ScreenSaver')
		else:
			errMsg = "Error: couldn't find bus to allow inhibiting of the screen saver.\n\n" \
				"Please visit the web-site listed in the 'About' dialog of this application " \
				"and check for a newer version of the software."
			errDlg = gtk.MessageDialog(type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=errMsg)
			errDlg.run()
			errDlg.destroy()
			sys.exit(2)

		screenSaverCookie = ssProxy.Inhibit("Caffeine", "User has requested that Caffeine disable the screen saver")
		sleepPrevented = True
		print "Caffiene is now preventing powersaving modes and screensaver activation"

def main():
	statusIcon = gtk.StatusIcon()

	menu = gtk.Menu()
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
	try:
		gtk.main()
	except KeyboardInterrupt:
		quitCaffeine()

if __name__ == "__main__":
	main()
