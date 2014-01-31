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


import os
from gi.repository import Gtk, GdkPixbuf, GObject, AppIndicator3
import ctypes
import argparse
import signal

## local modules
import caffeine
import core
import applicationinstance
import logging

logging.basicConfig(level=logging.INFO)

icon_theme = Gtk.IconTheme.get_default()
try:
    generic = icon_theme.load_icon("application-x-executable", 16, Gtk.IconLookupFlags.NO_SVG)
except GObject.GError, e:
    generic = GdkPixbuf.Pixbuf.new_from_file(caffeine.GENERIC_PROCESS_ICON_PATH)


class GUI(object):

    def __init__(self):
        
        self.Core = core.Caffeine()
        self.Core.connect("activation-toggled", self.on_activation_toggled)
        
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(caffeine.GLADE_PATH,
            "GUI.glade"))
        
        # It can be tiresome to have to type builder.get_object
        # again and again
        get = builder.get_object
        
        self.AppInd = AppIndicator3.Indicator.new("caffeine-cup-empty",
                                                  "caffeine",
                                                  AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.AppInd.set_status (AppIndicator3.IndicatorStatus.ACTIVE)

        self.activate_menuitem = get("activate_menuitem")
        self.set_icon_is_activated(self.Core.getActivated())

        ## popup menu
        self.menu = get("popup_menu")
        self.menu.show()
        self.AppInd.set_menu (self.menu)
            
        ## about dialog
        self.about_dialog = get("aboutdialog")
        self.about_dialog.set_translator_credits(_("translator-credits"))

        builder.connect_signals(self)

    
    def setActive(self, active):
        self.Core.setActivated(active)

    def toggleActivated(self):
        """Toggles whether screen saver prevention is active."""
        self.Core.toggleActivated()
        
    def on_activation_toggled(self, source, active, tooltip):
        self.set_icon_is_activated(active)

    def set_icon_is_activated(self, activated):
        ## toggle the icon, indexing with a bool.
        icon_name = ["caffeine-cup-empty", "caffeine-cup-full"][activated]

        self.AppInd.set_icon (icon_name)

        label = [_("Disable Screensaver"), _("Enable Screensaver")]
        self.activate_menuitem.set_label (label[self.Core.getActivated()])

    ### Callbacks
    def on_R_click(self, status_icon, mbutton, time, data=None):
        ## popdown menu
        self.menu.show_all()
        def func(menu, user_data): 
            return status_icon.position_menu(self.menu, status_icon) 
        self.menu.popup(None, None, func, self.status_icon, 3, time)
    
    #### Menu callbacks
    def on_activate_menuitem_activate (self, menuitem, data=None):
        self.toggleActivated()
        
        label = [_("Disable Screensaver"), _("Enable Screensaver")]
        menuitem.set_label (label[self.Core.getActivated()])

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):
        self.about_dialog.set_position (Gtk.WindowPosition.CENTER_ALWAYS)
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_quit_menuitem_activate(self, menuitem, data=None):
        self.quit()
    
    def quit(self):
        ### Do anything that needs to be done before quitting.
        logging.info("Caffeine is preparing to quit")

        ### Make sure PM and SV is uninhibited
        self.Core.setActivated(False)

        Gtk.main_quit()

options = None

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    GObject.threads_init()

    ## register the process id as 'caffeine'
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl(15, 'caffeine', 0, 0, 0)
  
    ## handle command line arguments
    parser = argparse.ArgumentParser(prog='caffeine', description='Manually and automatically prevent desktop idleness')
    parser.add_argument('-V', '--version', action='version', version='caffeine ' + VERSION)
    parser.parse_args()
    
    ## Makes sure that only one instance of the Caffeine is run for
    ## each user on the system.
    pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
    appInstance = applicationinstance.ApplicationInstance(pid_name)
    if appInstance.isAnother():
        appInstance.killOther()

    GUI()
    appInstance.startApplication()
    Gtk.main()
    appInstance.exitApplication()
