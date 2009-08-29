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
import gtk
import gobject
import pygtk
import dbus
import threading
import ctypes
import optparse

try:
    import pynotify
except:
    print _("Please install")+" pynotify"

## local modules
import caffeine
import core
import applicationinstance
import utils

def get_icon_for_process(proc_name):

    icon_theme = gtk.icon_theme_get_default()
    try:
        pixbuf = icon_theme.load_icon(proc_name, 16, gtk.ICON_LOOKUP_NO_SVG)
    except:
        try:
            possible_icon_name = proc_name.split("-")[0]
            pixbuf = icon_theme.load_icon(possible_icon_name, 16,
                    gtk.ICON_LOOKUP_NO_SVG)
        except:
            pass
        else:
            return pixbuf

        try:
            pixbuf = icon_theme.load_icon("application-x-executable", 
                    16, gtk.ICON_LOOKUP_NO_SVG)
        except:
            return None

    return pixbuf


class ProcAdd(object):

    def __init__(self):
        
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(caffeine.GLADE_PATH,
            "proc.glade"))

        get = builder.get_object

        self.dialog = get("dialog")
        self.entry = get("entry")
        
        ## populate the treemodels
        self.running_treeview = get("running_treeview")

        running_selection = self.running_treeview.get_selection()
        self.running_selection = running_selection

        self.running_liststore = get("running_liststore")
        self.running_liststore.set_sort_func(10, self.sort_proc_func)
        self.running_liststore.set_sort_column_id(10, gtk.SORT_ASCENDING)
        self.running_liststore.set_sort_func(11, self.sort_id_func)
        self.running_liststore.set_sort_column_id(11, gtk.SORT_DESCENDING)

        running_tvc1 = get("running_tvc1")
        running_tvc1.set_sort_column_id(10)

        running_tvc2 = get("running_tvc2")
        running_tvc2.set_sort_column_id(11)

        self.update_running_liststore()
        gobject.timeout_add(5000, self.update_running_liststore)


        ## allow the user to select multiple rows
        running_selection.connect("changed", self.on_running_selection_changed)
        
        builder.connect_signals(self)
    
           
    def sort_proc_func(self, model, iter1, iter2, data=None):
        v1 = model.get_value(iter1, 1)
        v2 = model.get_value(iter2, 1)
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1

        return 0

    def sort_id_func(self, model, iter1, iter2, data=None):
        
        v1 = model.get_value(iter1, 2)
        v2 = model.get_value(iter2, 2)
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1

        return 0


    def update_running_liststore(self):

        sel_id = None
        model, iter = self.running_selection.get_selected()

        if iter != None:
            sel_id = model.get_value(iter, 2)

        self.running_liststore.clear()

        for proc_name, id in self.get_running_processes():
            iter = self.running_liststore.append([
                get_icon_for_process(proc_name), proc_name, id])
            ## keep the same process selected if possible
            if id == sel_id:
                self.running_selection.select_iter(iter)


        return True

    def get_running_processes(self):
        
        return [(name.lower(), pid) for name, pid in utils.getProcesses()]

    def run(self):
        self.entry.set_text("")
        self.running_selection.unselect_all()

        response = self.dialog.run()
        self.dialog.hide()
        return response
        

    def get_process_name(self):
        return self.entry.get_text().strip()

    def on_running_selection_changed(self, treeselection, data=None):

        model, iter = treeselection.get_selected()
        
        if iter != None:
            self.entry.set_text(model.get_value(iter, 1))
            self.entry.select_region(0, -1)

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

        ## set the icons for the window border.
        gtk.window_set_default_icon_list(caffeine.get_icon_pixbuf(16),
            caffeine.get_icon_pixbuf(24), caffeine.get_icon_pixbuf(32),
            caffeine.get_icon_pixbuf(48))

    
        self.Conf = caffeine.get_configurator()
        
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
            
        ####
        ### configuration window widgets
        ####
        proc_treeview = get("treeview")
        self.selection = proc_treeview.get_selection()
        self.selection.set_mode(gtk.SELECTION_MULTIPLE)

        self.proc_liststore = get("proc_liststore")
        for line in open(caffeine.WHITELIST):
            name = line.strip()
            self.proc_liststore.append([get_icon_for_process(name), name])


        ## Build the timer submenu
        TIMER_OPTIONS_LIST = [(_("5 minutes"), 300.0),
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

        separator = gtk.SeparatorMenuItem()
        submenu.append(separator)

        menuItem = gtk.MenuItem(label=_("Other..."))
        menuItem.connect('activate', self.on_other_submenuitem_activate)
        submenu.append(menuItem)

        time_menuitem.set_submenu(submenu)
        submenu.show_all()
        

        ## Preferences editor.
        self.window = get("window")
        self.autostart_cb = get("autostart_cbutton")
        self.Conf.client.notify_add("/apps/caffeine/prefs/autostart",
                self.on_gconf_autostart_changed)

        self.autostart_cb.set_active(self.Conf.get("autostart").get_bool())


        ## about dialog
        self.about_dialog = get("aboutdialog")

        ## other time selector
        self.othertime_dialog = get("othertime_dialog")
        self.othertime_hours = get("hours_spin")
        self.othertime_minutes = get("minutes_spin")

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

    
    def setActive(self, active):

        if active:
            if not self.Core.getActivated():
                self.Core.toggleActivated()
        else:
            if self.Core.getActivated():
                self.Core.toggleActivated()
            
    def timedActivation(self, time):

        self.Core.timedActivation(time)

    def toggle_activated(self):
        """Toggles whether screen saver prevention
        is active.
        """
        self.Core.toggleActivated()
        
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

        self.window.hide_all()

    

    ## configuration callbacks
    def on_gconf_autostart_changed(self, client, cnxn_id, entry, data=None):
        if self.Conf.get("autostart").get_bool() != self.autostart_cb.get_active():
            self.autostart_cb.set_active(
                self.Conf.get("autostart").get_bool())
        
        if self.Conf.get("autostart").get_bool():
            caffeine.add_to_startup()
        else:
            caffeine.remove_from_startup()


    def on_autostart_cbutton_toggled(self, cbutton, data=None):
        self.Conf.set("autostart", cbutton.get_active())

    #### Menu callbacks
    def on_time_submenuitem_activate(self, menuitem, time):

        self.timedActivation(time)

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):

        response = self.about_dialog.run()
        self.about_dialog.hide()

    def on_other_submenuitem_activate(self, menuitem, data=None):

        self.othertime_dialog.show_all()

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
    
        ### Make sure PM and SV is uninhibited
        if self.Core.getActivated():
            self.toggle_activated()

        self.Core.quit()

        gtk.main_quit()


def main():

    gtk.gdk.threads_init()

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
    


    options, args = parser.parse_args()
    
    ## Makes sure that only one instance of the Caffeine is run for
    ## each user on the system.
    pid_name = '/tmp/caffeine' + str(os.getuid()) + '.pid'
    appInstance = applicationinstance.ApplicationInstance(pid_name)
    if appInstance.isAnother():
        appInstance.killOther()

    main = GUI()
        
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


    appInstance.startApplication()
    gtk.main()
    appInstance.exitApplication()
