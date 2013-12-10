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


import os
import sys
import gi
from gi.repository import Gtk, GObject, AppIndicator3, Notify
import dbus
import ctypes
import optparse

## local modules
import caffeine
import core
import applicationinstance
import utils
import logging

logging.basicConfig(level=logging.INFO)

icon_theme = Gtk.IconTheme.get_default()
try:
    generic = icon_theme.load_icon("application-x-executable", 16, Gtk.IconLookupFlags.NO_SVG)
except GObject.GError, e:
    generic = GdkPixbuf.Pixbuf.new_from_file(caffeine.GENERIC_PROCESS_ICON_PATH)


cached_icons = {"generic":generic}
def get_icon_for_process(proc_name):

    global cached_icons
    global generic

    possible_icon_names = proc_name.split("-")
    possible_icon_names.insert(0, proc_name)

    for icon_name in possible_icon_names:

        icon_name = icon_name.split("/")[-1]

        ### Check to see if we have loaded this already.
        try:
            return cached_icons[icon_name]
        except KeyError:
            pass
        try:
            icon = icon_theme.load_icon(proc_name, 16, Gtk.IconLookupFlags.NO_SVG)
            cached_icons[icon_name] = icon
            return icon

        except GObject.GError, e:
            cached_icons[icon_name] = generic
    
    return cached_icons["generic"]


class ProcAdd(object):

    def __init__(self):
        self.running_id = None
        self.user_set = True

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(caffeine.GLADE_PATH,
            "proc.glade"))

        get = builder.get_object

        self.dialog = get("dialog")
        self.entry = get("entry")
        self.entry.grab_focus()

        builder.connect_signals(self)
    
    def run(self):
        self.entry.set_text("")

        response = self.dialog.run()
        self.hide()
        return response
        

    def get_process_name(self):
        return self.entry.get_text().strip()

    def on_add_button_clicked(self, button, data=None):
        self.dialog.hide()

    def on_cancel_button_clicked(self, button, data=None):
        self.dialog.hide()

    def hide(self):
        self.dialog.hide()

    def on_window_delete_event(self, window, data=None):
        window.hide_on_delete()
        ## Returning True stops the window from being destroyed.
        return True

        
class GUI(object):

    def __init__(self):
        
        self.Core = core.Caffeine()

        self.Core.connect("activation-toggled",
                self.on_activation_toggled)
        
        self.ProcAdd = ProcAdd()

        ## object to manage processes to activate for.
        self.ProcMan = caffeine.get_ProcManager()
            
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
            
        ### configuration window widgets
        proc_treeview = get("treeview")
        self.selection = proc_treeview.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.proc_liststore = get("proc_liststore")
        for line in open(caffeine.WHITELIST):
            name = line.strip()
            self.proc_liststore.append([get_icon_for_process(name), name])

        ## Preferences editor.
        self.window = get("window")
        
        ## set the icons for the window border.
        self.window.set_default_icon_list([caffeine.get_icon_pixbuf(16),
            caffeine.get_icon_pixbuf(24), caffeine.get_icon_pixbuf(32),
            caffeine.get_icon_pixbuf(48)])

        ## about dialog
        self.about_dialog = get("aboutdialog")
        self.about_dialog.set_translator_credits(_("translator-credits"))

        builder.connect_signals(self)

    
    def setActive(self, active):
        self.Core.setActivated(active)

    def timedActivation(self, time):
        self.Core.timedActivation(time)

    def toggleActivated(self):
        """Toggles whether screen saver prevention
        is active.
        """
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
    def on_L_click(self, status_icon, data=None):
        logging.info("User has clicked the Caffeine icon")
        self.toggleActivated()
    
    def on_R_click(self, status_icon, mbutton, time, data=None):
        ## popdown menu
        self.menu.show_all()
        def func(menu, user_data): 
            return status_icon.position_menu(self.menu, status_icon) 
        self.menu.popup(None, None, func, self.status_icon, 3, time)
    
    #### Window callbacks
    def on_add_button_clicked(self, button, data=None):
        response = self.ProcAdd.run()
        if response == 1:
            proc_name = self.ProcAdd.get_process_name()
            if proc_name:
                self.proc_liststore.append([get_icon_for_process(proc_name),
                    proc_name])
                
                self.ProcMan.add_proc(proc_name)
                
    def on_remove_button_clicked(self, button, data=None):
        model, paths = self.selection.get_selected_rows()
        paths.reverse()
        for path in paths:
            self.ProcMan.remove_proc(model[path][1])
            model.remove(model.get_iter(path))

    def on_window_delete_event(self, window, data=None):
        window.hide_on_delete()
        ## Returning True stops the window from being destroyed.
        return True

    def on_close_button_clicked(self, button, data=None):
        self.window.hide()


    #### Menu callbacks
    def on_activate_menuitem_activate (self, menuitem, data=None):
        self.toggleActivated()
        
        label = [_("Disable Screensaver"), _("Enable Screensaver")]
        menuitem.set_label (label[self.Core.getActivated()])

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):
        self.about_dialog.set_position (Gtk.WindowPosition.CENTER_ALWAYS)
        response = self.about_dialog.run()
        self.about_dialog.hide()

    def on_quit_menuitem_activate(self, menuitem, data=None):
        self.quit()
    
    def quit(self):
        ### Do anything that needs to be done before quitting.
        logging.info("Caffeine is preparing to quit")

        ### Make sure PM and SV is uninhibited
        self.Core.setActivated(False)

        self.Core.quit()

        Gtk.main_quit()

options = None

def main():

    GObject.threads_init()

    ## register the process id as 'caffeine'
    libc = ctypes.cdll.LoadLibrary('libc.so.6')
    libc.prctl(15, 'caffeine', 0, 0, 0)
  
    ## handle command line arguments
    parser = optparse.OptionParser()
    parser.add_option("-a", "--activate", action="store_true",
            dest="activated", default=False,
            help="Disables power management and screen saving.")

    parser.add_option("-d", "--deactivate", action="store_false",
            dest="activated", default=False,
            help="Re-enables power management and screen saving.")

    parser.add_option("-t", "--time",
            metavar="HOURS:MINUTES",
            dest="timed",
            help=("If the -a option is given, "+
                "activates Caffeine for HOURS:MINUTES."))

    global options
    options, args = parser.parse_args()
    
    ## Makes sure that only one instance of the Caffeine is run for
    ## each user on the system.
    pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
    appInstance = applicationinstance.ApplicationInstance(pid_name)
    if appInstance.isAnother():
        appInstance.killOther()

    main = GUI()
        
    if options.activated:
        main.setActive(options.activated)

    if options.activated and options.timed:
        parts = options.timed.split(":")
        if len(parts) < 2:
            print "-t argument must be in the hour:minute format."
            sys.exit(2)

        try:
            hours = int(parts[0])
            minutes = int(parts[1])
        except:
            print "Invalid time argument."
            sys.exit(2)

        main.timedActivation((hours * 3600.0)+(minutes * 60.0))
    
    if options.preferences:
        main.window.show_all()

    appInstance.startApplication()
    Gtk.main()
    appInstance.exitApplication()
