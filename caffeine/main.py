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
import glib
import pygtk
import appindicator

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
import caffeinelogging as logging

icon_theme = gtk.icon_theme_get_default()
generic = icon_theme.load_icon("application-x-executable", 16, gtk.ICON_LOOKUP_NO_SVG)



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
            icon = icon_theme.load_icon(proc_name, 16, gtk.ICON_LOOKUP_NO_SVG)
            cached_icons[icon_name] = icon
            return icon

        except glib.GError, e:
            cached_icons[icon_name] = generic
    
    return cached_icons["generic"]


class ProcAdd(object):

    def __init__(self):
        
        self.recent_processes = []
        self.dead_processes = []

        self.running_id = None

        self.user_set = True

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
        
        running_selection.connect("changed", self.on_running_selection_changed)

        self.update_running_liststore()

        ###
        self.recent_treeview = get("recent_treeview")

        recent_selection = self.recent_treeview.get_selection()
        self.recent_selection = recent_selection

        self.recent_liststore = get("recent_liststore")
        self.recent_liststore.set_sort_func(10, self.sort_proc_func)
        self.recent_liststore.set_sort_column_id(10, gtk.SORT_ASCENDING)
        self.recent_liststore.set_sort_func(11, self.sort_id_func)
        self.recent_liststore.set_sort_column_id(11, gtk.SORT_DESCENDING)

        recent_tvc1 = get("recent_tvc1")
        recent_tvc1.set_sort_column_id(10)

        recent_tvc2 = get("recent_tvc2")
        recent_tvc2.set_sort_column_id(11)

        gobject.timeout_add(5000, self.update_recent_liststore)

        recent_selection.connect("changed", self.on_recent_selection_changed)
                
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
                self.user_set = False
                self.running_selection.select_iter(iter)
                self.user_set = True


        return True
    
    def update_recent_liststore(self):

        sel_id = None
        model, iter = self.recent_selection.get_selected()

        if iter != None:
            sel_id = model.get_value(iter, 2)

        self.recent_liststore.clear()

        seen = []
        
        recent = self.get_recent_processes()
        recent.reverse()
        for proc_name, id in recent:

            if proc_name not in seen:
                iter = self.recent_liststore.append([
                    get_icon_for_process(proc_name), proc_name, id])

            seen.append(proc_name)
            ## keep the same process selected if possible
            if id == sel_id:
                self.user_set = False
                self.recent_selection.select_iter(iter)
                self.user_set = True

        return True

    def get_running_processes(self):
        
        return [(name, pid) for name, pid in utils.getProcesses()]
    
    def get_recent_processes(self):
        
        running_pids = [pid for name, 
                pid in utils.getProcesses()]

        if self.recent_processes:
            ## don't let the list get too long
            if len(self.dead_processes) > 100:
                self.dead_processes = self.dead_processes[25:100]

            self.dead_processes += [(name, pid) for name,
                pid in self.recent_processes if pid not in running_pids]
            
        self.recent_processes = self.get_running_processes()
        return self.dead_processes


    def run(self):

        if self.running_id != None:
            gobject.source_remove(self.running_id)

        self.running_id = gobject.timeout_add(5000,
                self.update_running_liststore)

        self.entry.set_text("")
        self.running_selection.unselect_all()
        self.recent_selection.unselect_all()

        response = self.dialog.run()
        self.hide()
        return response
        

    def get_process_name(self):
        return self.entry.get_text().strip()

    def on_running_selection_changed(self, treeselection, data=None):
        
        if not self.user_set:
            return 

        model, iter = treeselection.get_selected()
        
        if iter != None:
            self.entry.set_text(model.get_value(iter, 1))
            self.entry.select_region(0, -1)

    def on_recent_selection_changed(self, treeselection, data=None):
        
        if not self.user_set:
            return 

        model, iter = treeselection.get_selected()
        
        if iter != None:
            self.entry.set_text(model.get_value(iter, 1))
            self.entry.select_region(0, -1)



    def on_add_button_clicked(self, button, data=None):
        self.dialog.hide()

    def on_cancel_button_clicked(self, button, data=None):
        self.dialog.hide()

    def hide(self):
        
        if self.running_id != None:
            gobject.source_remove(self.running_id)

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
        #self.status_icon = get("statusicon")
        self.AppInd = appindicator.Indicator ("caffeine-cup-empty",
                        "caffeine",
                        appindicator.CATEGORY_APPLICATION_STATUS)
        show_tray_icon = self.Conf.get("show_tray_icon").get_bool()
        
        if show_tray_icon is False:
            note = pynotify.Notification("Caffeine is now running", "To show the tray icon, run 'caffeine -icon'", "caffeine")

            note.show()
        
        
        self.AppInd.set_status ([appindicator.STATUS_PASSIVE, appindicator.STATUS_ACTIVE][show_tray_icon])
        #self.AppInd.set_attention_icon ("caffeine")

        self.set_icon_is_activated(self.Core.getActivated())

        tooltip = self.Core.status_string
        if not tooltip:
            tooltip = _("Caffeine is dormant; powersaving is enabled")
        #self.status_icon.set_tooltip(tooltip)

        ## popup menu
        self.menu = get("popup_menu")
        self.menu.show()

        self.AppInd.set_menu (self.menu)
            
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
        self.ql_cb = get("ql_cbutton")
        self.flash_cb = get("flash_cbutton")
        self.trayicon_cb = get("trayicon_cbutton")

        self.Conf.client.notify_add("/apps/caffeine/prefs/autostart",
                self.on_gconf_autostart_changed)

        self.Conf.client.notify_add("/apps/caffeine/prefs/act_for_ql",
                self.on_gconf_ql_changed)

        self.Conf.client.notify_add("/apps/caffeine/prefs/act_for_flash",
                self.on_gconf_flash_changed)

        self.Conf.client.notify_add("/apps/caffeine/prefs/show_tray_icon",
                self.on_gconf_trayicon_changed)

        self.autostart_cb.set_active(self.Conf.get("autostart").get_bool())
        self.ql_cb.set_active(self.Conf.get("act_for_ql").get_bool())
        self.flash_cb.set_active(self.Conf.get("act_for_flash").get_bool())
        self.trayicon_cb.set_active(self.Conf.get("show_tray_icon").get_bool())

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
        #self.status_icon.connect("activate", self.on_L_click)
        # right click
        #self.status_icon.connect("popup-menu", self.on_R_click)

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


        self.AppInd.set_icon (icon_name)


    ### Callbacks
    def on_L_click(self, status_icon, data=None):
        logging.info("User has clicked the Caffeine icon")
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

    def on_about_button_clicked (self, button, data=None):

        response = self.about_dialog.run()
        self.about_dialog.hide()

    

    ## configuration callbacks
    def on_gconf_autostart_changed(self, client, cnxn_id, entry, data=None):
        autostart = self.Conf.get("autostart").get_bool() 

        if autostart != self.autostart_cb.get_active():
            self.autostart_cb.set_active(autostart)
        
        if autostart:
            caffeine.add_to_startup()
        else:
            caffeine.remove_from_startup()


    def on_autostart_cbutton_toggled(self, cbutton, data=None):
        self.Conf.set("autostart", cbutton.get_active())

    ### Quake Live
    def on_gconf_ql_changed(self, client, cnxn_id, entry, data=None):
        act_for_ql = self.Conf.get("act_for_ql").get_bool()

        self.Core.setActivateForQL(act_for_ql)

        if act_for_ql != self.ql_cb.get_active():
            self.ql_cb.set_active(act_for_ql)

    def on_ql_cbutton_toggled(self, cbutton, data=None):
        self.Conf.set("act_for_ql", cbutton.get_active())
    
    ### Flash
    def on_gconf_flash_changed(self, client, cnxn_id, entry, data=None):
        
        act_for_flash = self.Conf.get("act_for_flash").get_bool()

        self.Core.setActivateForFlash(act_for_flash)

        #if act_for_flash != self.flash_cb.get_active():
        self.flash_cb.set_active(act_for_flash)

    def on_flash_cbutton_toggled(self, cbutton, data=None):

        self.Conf.set("act_for_flash", cbutton.get_active())

    ### Tray icon

    def on_gconf_trayicon_changed(self, client, cnxn_id, entry, data=None):
        show_tray_icon = self.Conf.get("show_tray_icon").get_bool()

        self.AppInd.set_status (
            [appindicator.STATUS_PASSIVE, appindicator.STATUS_ACTIVE][show_tray_icon]
            )
    
        if show_tray_icon != self.trayicon_cb.get_active():
            self.trayicon_cb.set_active(show_tray_icon)
    
        #if show_tray_icon !=  
    def on_trayicon_cbutton_toggled(self, cbutton, data=None):
        state = cbutton.get_active()

        self.Conf.set("show_tray_icon", state)

    #### Menu callbacks
    def on_activate_menuitem_activate (self, menuitem, data=None):

        self.toggleActivated()
        
        label = [_("Disable Screensaver"), _("Enable Screensaver")]
        menuitem.set_label (label[self.Core.getActivated()])


    def on_time_submenuitem_activate(self, menuitem, time):

        self.timedActivation(time)

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def _run_dialog(self):
        print 2
        response = self.about_dialog.run()
        print response
        print 3
        self.about_dialog.destroy()
        print 4
        
        return False

    def on_about_menuitem_activate(self, menuitem, data=None):

        gobject.idle_add(self._run_dialog)
        print 1
        #response = self.about_dialog.run()
        #self.about_dialog.set_position (gtk.WIN_POS_CENTER_ALWAYS)
        #self.about_dialog.show()
        #self.about_dialog.destroy()

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
        logging.info("Caffeine is preparing to quit")

        ### Make sure PM and SV is uninhibited
        self.Core.setActivated(False)

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

    parser.add_option("-p", "--preferences", action="store_true",
            dest="preferences", default=False,
            help="Starts Caffeine with the Preferences dialog open.")




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
    gtk.main()
    appInstance.exitApplication()
