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


import os
import sys
from gi.repository import Gtk, GObject, Gio

appindicator_avail = True
try:
    from gi.repository import AppIndicator3
except:
    appindicator_avail = False

import gi
import webbrowser 


import dbus
import ctypes
import optparse

try:
    from gi.repository import Notify
except:

    print _("Please install")+" pynotify"

## local modules
import caffeine
import core
import applicationinstance
import utils
import caffeinelogging as logging

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
        

        ###
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

            
        settings = Gio.Settings.new(caffeine.BASE_KEY)
        
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(caffeine.GLADE_PATH,
            "GUI.glade"))
        
        # It can be tiresome to have to type builder.get_object
        # again and again
        get = builder.get_object
        
        show_tray_icon = settings.get_boolean("show-tray-icon")
        show_notification = settings.get_boolean("show-notification")

        if appindicator_avail:
            self.AppInd = AppIndicator3.Indicator.new("caffeine-cup-empty",
                            "caffeine",
                            AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            #print [AppIndicator3.IndicatorStatus.PASSIVE, AppIndicator3.IndicatorStatus.ACTIVE][show_tray_icon]
            self.AppInd.set_status ([AppIndicator3.IndicatorStatus.PASSIVE, AppIndicator3.IndicatorStatus.ACTIVE][show_tray_icon])

        else:
            ## IMPORTANT:
            ## status icon must be a instance variable  (ie self.)or else it 
            ## gets thrown out with the garbage, and won't be seen.

            self.status_icon = get("statusicon")
            self.status_icon.set_visible(show_tray_icon)
        
        if show_tray_icon is False and show_notification is True and options.preferences is not True:
            note = Notify.Notification(_("Caffeine is running"), _("To show the tray icon, \nrun ") + "'caffeine -p' " + _("or open Caffeine Preferences from your system menu."), "caffeine")

            note.show()
        
        

        self.activate_menuitem = get("activate_menuitem")

        self.set_icon_is_activated(self.Core.getActivated())

        tooltip = self.Core.status_string
        if not tooltip:
            tooltip = _("Caffeine is dormant; powersaving is enabled")
        #self.status_icon.set_tooltip(tooltip)

        ## popup menu
        self.menu = get("popup_menu")
        self.menu.show()


        if appindicator_avail:

            self.AppInd.set_menu (self.menu)
            
        ####
        ### configuration window widgets
        ####
        proc_treeview = get("treeview")
        self.selection = proc_treeview.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.proc_liststore = get("proc_liststore")
        for line in open(caffeine.WHITELIST):
            name = line.strip()
            self.proc_liststore.append([get_icon_for_process(name), name])



        #time_menuitem = get("time_menuitem")

        #time_menuitem.set_submenu(submenu)
        

        ## Preferences editor.
        self.window = get("window")
        
        ## set the icons for the window border.
        self.window.set_default_icon_list([caffeine.get_icon_pixbuf(16),
            caffeine.get_icon_pixbuf(24), caffeine.get_icon_pixbuf(32),
            caffeine.get_icon_pixbuf(48)])



        self.autostart_cb = get("autostart_cbutton")
        self.ql_cb = get("ql_cbutton")
        self.flash_cb = get("flash_cbutton")
        self.trayicon_cb = get("trayicon_cbutton")
        self.notification_cb = get("notification_cbutton")

        self.notification_cb.set_sensitive(not show_tray_icon)

        settings.connect("changed::autostart", self.on_autostart_changed)
        settings.connect("changed::act-for-quake", self.on_ql_changed)
        settings.connect("changed::act-for-flash", self.on_flash_changed)
        settings.connect("changed::show-tray-icon", self.on_trayicon_changed)
        settings.connect("changed::show-notification", self.on_notification_changed)


        settings.bind("autostart", self.autostart_cb, "active", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("act-for-quake", self.ql_cb, "active", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("act-for-flash", self.flash_cb, "active", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("show-tray-icon", self.trayicon_cb, "active", Gio.SettingsBindFlags.DEFAULT)
        settings.bind("show-notification", self.notification_cb, "active", Gio.SettingsBindFlags.DEFAULT)


        ## about dialog
        self.about_dialog = get("aboutdialog")
        self.about_dialog.set_translator_credits(_("translator-credits"))

        ## other time selector
        self.othertime_dialog = get("othertime_dialog")
        self.othertime_hours = get("hours_spin")
        self.othertime_minutes = get("minutes_spin")


        if appindicator_avail is False:
            ## Handle mouse clicks on status_icon
            # left click
            self.status_icon.connect("activate", self.on_L_click)
            # right click
            self.status_icon.connect("popup-menu", self.on_R_click)

            
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


        #self.status_icon.set_tooltip(tooltip)

    def set_icon_is_activated(self, activated):
        
        ## toggle the icon, indexing with a bool.
        icon_name = ["caffeine-cup-empty", "caffeine-cup-full"][activated]

        if appindicator_avail:
            self.AppInd.set_icon (icon_name)
        else:
            self.status_icon.set_from_icon_name(icon_name)

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


    ## configuration callbacks
    def on_autostart_changed(self, settings, key, data=None):
        autostart = settings.get_boolean(key)
        
        if autostart:
            caffeine.add_to_startup()
        else:
            caffeine.remove_from_startup()


    ### Quake Live
    def on_ql_changed(self, settings, key, data=None):
        act_for_ql = settings.get_boolean(key)

        self.Core.setActivateForQL(act_for_ql)

        if act_for_ql != self.ql_cb.get_active():
            self.ql_cb.set_active(act_for_ql)

    
    ### Flash
    def on_flash_changed(self, settings, key, data=None):
        
        act_for_flash = settings.get_boolean(key)

        self.Core.setActivateForFlash(act_for_flash)

        #self.flash_cb.set_active(act_for_flash)

    #def on_flash_cbutton_toggled(self, cbutton, data=None):

    #    self.Conf.set("act_for_flash", cbutton.get_active())

    ### Tray icon

    def on_trayicon_changed(self, settings, key, data=None):
        show_tray_icon = settings.get_boolean(key)

        if appindicator_avail:

            self.AppInd.set_status ([AppIndicator3.IndicatorStatus.PASSIVE, AppIndicator3.IndicatorStatus.ACTIVE][show_tray_icon])
    
        else:
            self.status_icon.set_visible(show_tray_icon)

        self.trayicon_cb.set_active(show_tray_icon)

        self.notification_cb.set_sensitive(not show_tray_icon)
    
   # def on_trayicon_cbutton_toggled(self, cbutton, data=None):

   #     self.Conf.set("show_tray_icon", cbutton.get_active())

    # Startup Notifications
    def on_notification_changed(self, settings, key, data=None):
        pass
        
    #def on_notification_cbutton_toggled(self, cbutton, data=None):
            
    #    self.Conf.set("show_notification", cbutton.get_active())





    #### Menu callbacks
    def on_activate_menuitem_activate (self, menuitem, data=None):

        self.toggleActivated()
        
        label = [_("Disable Screensaver"), _("Enable Screensaver")]
        menuitem.set_label (label[self.Core.getActivated()])


    def on_time_menuitem_activate(self, menuitem, data=None):

        self.othertime_dialog.show_all()

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):


        self.about_dialog.set_position (Gtk.WindowPosition.CENTER_ALWAYS)
        response = self.about_dialog.run()
        self.about_dialog.hide()


    def on_othertime_delete_event(self, window, data=None):

        window.hide_on_delete()
        ## Returning True stops the window from being destroyed.
        return True

    def on_othertime_cancel(self, widget, data=None):

        self.othertime_dialog.hide()

    def on_othertime_ok(self, widget, data=None):

        hours = int(self.othertime_hours.get_value())
        minutes = int(self.othertime_minutes.get_value())
        self.othertime_dialog.hide()
        time = hours*60*60 + minutes*60
        if time > 0:
            self.Core.timedActivation(time)


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
                "activates caffeine for HOURS:MINUTES."))

    parser.add_option("-p", "--preferences", action="store_true",
            dest="preferences", default=False,
            help="Starts Caffeine with the Preferences dialog open.")




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
