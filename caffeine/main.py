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


import os, sys
import gtk
import pygtk
import dbus
import threading
try:
    import pynotify
except:
    print _("Please install")+" pynotify"

## local modules
import caffeine
import core

class GUI(object):

    def __init__(self):
        
        self.caffeine = core.Caffeine()

        self.caffeine.connect("activation-toggled",
                self.on_activation_toggled)
        
        ## set the icons for the window border.
        gtk.window_set_default_icon_list(caffeine.get_icon_pixbuf(16),
            caffeine.get_icon_pixbuf(24), caffeine.get_icon_pixbuf(32),
            caffeine.get_icon_pixbuf(48))


        
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(caffeine.GLADE_PATH,
            "GUI.glade"))
        
        # It can be tiresome to have to type builder.get_object
        # again and again
        get = builder.get_object
        
        ## IMPORTANT:
        ## status icon must be a instance variable  (ie self.)or else it 
        ## gets thrown out with the garbage, and won't be seen.
        self.status_icon = get("statusicon")

        self.status_icon.set_from_file(caffeine.EMPTY_ICON_PATH)

        ## popup menu
        self.menu = get("popup_menu")
            
        ## Build the timer submenu
        TIMER_OPTIONS_LIST = [(_("10 seconds (for testing)"), 10.0),
                (_("5 minutes"), 300.0),
                (_("10 minutes"), 600.0),
                (_("15 minutes"), 900.0),
                (_("30 minutes"), 1800.0),
                (_("1 hour"), 3600.0),
                (_("2 hours"), 7200.0),
                (_("3 hours"), 10800.0),
                (_("4 hours"), 14400.0)]


        time_menuitem = get("time_menuitem")
        submenu = gtk.Menu()

        for label, t in TIMER_OPTIONS_LIST:
            menuItem = gtk.MenuItem(label=label)
            menuItem.connect('activate', self.on_time_submenuitem_activate,
                    t)

            submenu.append(menuItem)

        time_menuitem.set_submenu(submenu)
        submenu.show_all()
        

        ## Preferences editor.
        self.window = get("window")

        ## about dialog
        self.about_dialog = get("aboutdialog")

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



    def toggle_activated(self):
        """Toggles whether screen saver prevention
        is active.
        """
        self.caffeine.toggleActivated()
        
    def on_activation_toggled(self, source, active):

        ## toggle the icon, indexing with a bool.
        icon_file = [caffeine.EMPTY_ICON_PATH, caffeine.FULL_ICON_PATH][
                active]

        self.status_icon.set_from_file(icon_file)




    ### Callbacks
    def on_L_click(self, status_icon, data=None):
        self.toggle_activated()
    
    def on_R_click(self, status_icon, mbutton, time, data=None):
        ## popdown menu
        self.menu.popup(None, None,
                gtk.status_icon_position_menu, 3, time, self.status_icon)
        
    
    #### Window callbacks
    def on_window_delete_event(self, window, data=None):

        window.hide_on_delete()
        ## Returning True stops the window from being destroyed.
        return True

    def on_close_button_clicked(self, button, data=None):

        self.window.hide_all()

    #### Menu callbacks
    def on_time_submenuitem_activate(self, menuitem, time):

        self.caffeine.timedActivation(time)

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):

        response = self.about_dialog.run()
        self.about_dialog.hide()

    def on_quit_menuitem_activate(self, menuitem, data=None):

        self.quit()

    
    def quit(self):
        ### Do anything that needs to be done before quitting.
    
        if self.caffeine.timer:
            self.caffeine.timer.cancel()
        
        gtk.main_quit()


def main():

    gtk.gdk.threads_init()
    main = GUI()

    gtk.main()
