# Copyright (c) 2014 Hugo Osvaldo Barrera
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
# TODO: add a -v --verbosity flag.
import logging
from gettext import gettext as _

import gi

gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import GdkPixbuf, Gio, GObject, Gtk  # noqa: E402
from gi.repository.Notify import init as notify_init  # noqa: E402
from gi.repository.Notify import Notification  # noqa: E402

from . import __version__  # noqa: E402
from .core import Caffeine  # noqa: E402
from .icons import generic_icon, get_icon_pixbuf  # noqa: E402
from .paths import get_glade_file, get_whitelist_file, get_whitelist_file_audio  # noqa: E402
from .procmanager import ProcManager  # noqa: E402

appindicator_avail = True
try:
    from gi.repository import AppIndicator3
except ImportError:
    appindicator_avail = False

logger = logging.getLogger(__name__)

icon_theme = Gtk.IconTheme.get_default()
try:
    generic = icon_theme.load_icon(
        "application-x-executable", 16, Gtk.IconLookupFlags.NO_SVG
    )
except GObject.GError:
    generic = GdkPixbuf.Pixbuf.new_from_file(generic_icon)

cached_icons = {"generic": generic}


# FIXME: this does not work for any of the cases I tried.
def get_icon_for_process(proc_name):

    global cached_icons
    global generic

    possible_icon_names = proc_name.split("-")
    possible_icon_names.insert(0, proc_name)

    for icon_name in possible_icon_names:

        icon_name = icon_name.split("/")[-1]

        # Check to see if we have loaded this already.
        try:
            return cached_icons[icon_name]
        except KeyError:
            pass
        try:
            icon = icon_theme.load_icon(proc_name, 16, Gtk.IconLookupFlags.NO_SVG)
            cached_icons[icon_name] = icon
            return icon

        except GObject.GError:
            cached_icons[icon_name] = generic

    return cached_icons["generic"]


class ProcAdd:
    def __init__(self):
        self.running_id = None

        self.user_set = True

        builder = Gtk.Builder()
        builder.add_from_file(get_glade_file("proc.glade"))

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
        return self.entry.get_text().lower().strip()

    def on_add_button_clicked(self, button, data=None):
        self.dialog.hide()

    def on_cancel_button_clicked(self, button, data=None):
        self.dialog.hide()

    def hide(self):
        self.dialog.hide()

    def on_window_delete_event(self, window, data=None):
        window.hide_on_delete()
        # Returning True stops the window from being destroyed.
        return True


class GUI:
    def __init__(self, show_preferences=False, **kwargs):
        # object to manage processes to activate for.
        self.__process_manager = ProcManager(persistence_file=get_whitelist_file())
        self.__process_manager_audio = ProcManager(persistence_file=get_whitelist_file_audio())

        self.__core = Caffeine(
            process_manager=self.__process_manager,
            process_manager_audio=self.__process_manager_audio,
            **kwargs
        )

        self.__core.connect("activation-toggled", self.on_activation_toggled)
        self.ProcAdd = ProcAdd()

        # XXX: Do we want to change this to caffeine-ng?
        settings = Gio.Settings.new("net.launchpad.caffeine")

        builder = Gtk.Builder()
        builder.add_from_file(get_glade_file("GUI.glade"))

        # It can be tiresome to have to type builder.get_object
        # again and again
        get = builder.get_object

        about = get("aboutdialog")
        about.set_version(__version__)

        show_tray_icon = settings.get_boolean("show-tray-icon")
        show_notification = settings.get_boolean("show-notification")
        audio_peak_filtering_active = settings.get_boolean("audio-peak-filtering")
        self.__core.set_audio_peak_filtering_active(audio_peak_filtering_active)

        if appindicator_avail:
            self.AppInd = AppIndicator3.Indicator.new(
                "caffeine",
                "caffeine-cup-empty",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )

            self.AppInd.set_status(
                [
                    AppIndicator3.IndicatorStatus.PASSIVE,
                    AppIndicator3.IndicatorStatus.ACTIVE,
                ][show_tray_icon]
            )
        else:
            # IMPORTANT:
            # status icon must be a instance variable  (ie self.)or else it
            # gets thrown out with the garbage, and won't be seen.

            self.status_icon = get("statusicon")
            self.status_icon.set_visible(show_tray_icon)

        if (
            show_tray_icon is False
            and show_notification is True
            and show_preferences is False
        ):
            notify_init("caffeine-ng")
            note = Notification.new(
                _("Caffeine is running"),
                _("To show the tray icon, \nrun ")
                + "'caffeine -p' "
                + _("or open Caffeine Preferences from your system menu."),
                "caffeine",
            )

            note.show()

        self.activate_menuitem = get("activate_menuitem")

        self.set_icon_is_activated(self.__core.get_activated())

        tooltip = self.__core.status_string
        if not tooltip:
            tooltip = _("Caffeine is dormant; powersaving is enabled")
        # self.status_icon.set_tooltip(tooltip)

        # popup menu
        self.menu = get("popup_menu")
        self.menu.show()

        if appindicator_avail:

            self.AppInd.set_menu(self.menu)

        #
        # configuration window widgets
        #
        proc_treeview = get("treeview")
        self.selection = proc_treeview.get_selection()
        self.selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        proc_treeview_audio = get("treeview_audio")
        self.selection_audio = proc_treeview_audio.get_selection()
        self.selection_audio.set_mode(Gtk.SelectionMode.MULTIPLE)

        self.proc_liststore = get("proc_liststore")
        for name in self.__process_manager.get_process_list():
            self.proc_liststore.append([get_icon_for_process(name), name])
        self.proc_liststore_audio = get("proc_liststore_audio")
        for name in self.__process_manager_audio.get_process_list():
            self.proc_liststore_audio.append([get_icon_for_process(name), name])

        # time_menuitem = get("time_menuitem")

        # time_menuitem.set_submenu(submenu)

        # Preferences editor.
        self.window = get("window")

        # set the icons for the window border.
        self.window.set_default_icon_list(
            [
                get_icon_pixbuf(16),
                get_icon_pixbuf(24),
                get_icon_pixbuf(32),
                get_icon_pixbuf(48),
            ]
        )

        self.trayicon_cb = get("trayicon_cbutton")
        self.notification_cb = get("notification_cbutton")
        self.audio_peak_filtering_cb = get("audio_peak_filtering_cbutton")

        self.notification_cb.set_sensitive(not show_tray_icon)

        settings.connect("changed::show-tray-icon", self.on_trayicon_changed)
        settings.connect("changed::show-notification", self.on_notification_changed)
        settings.connect("changed::audio-peak-filtering", self.on_audio_peak_filtering_changed)

        settings.bind(
            "show-tray-icon", self.trayicon_cb, "active", Gio.SettingsBindFlags.DEFAULT
        )
        settings.bind(
            "show-notification",
            self.notification_cb,
            "active",
            Gio.SettingsBindFlags.DEFAULT,
        )
        settings.bind(
            "audio-peak-filtering", self.audio_peak_filtering_cb, "active", Gio.SettingsBindFlags.DEFAULT
        )

        # about dialog
        self.about_dialog = get("aboutdialog")
        self.about_dialog.set_translator_credits(_("translator-credits"))

        # other time selector
        self.othertime_dialog = get("othertime_dialog")
        self.othertime_hours = get("hours_spin")
        self.othertime_minutes = get("minutes_spin")

        if appindicator_avail is False:
            # Handle mouse clicks on status_icon
            # left click
            self.status_icon.connect("activate", self.on_L_click)
            # right click
            self.status_icon.connect("popup-menu", self.on_R_click)

        builder.connect_signals(self)

    def setActive(self, active: bool):
        self.__core.set_activated(active)

    def timed_activation(self, time):
        self.__core.timed_activation(time)

    def toggle_activated(self):
        """Toggles whether screen saver prevention is active."""
        self.__core.toggle_activated()

    def on_activation_toggled(self, source, active, tooltip):
        self.set_icon_is_activated(active)
        # self.status_icon.set_tooltip(tooltip)

    def set_icon_is_activated(self, activated):
        # toggle the icon, indexing with a bool.
        icon_name = ["caffeine-cup-empty", "caffeine-cup-full"][activated]

        if appindicator_avail:
            self.AppInd.set_icon(icon_name)
        else:
            self.status_icon.set_from_icon_name(icon_name)

        label = [_("Enable Caffeine"), _("Disable Caffeine")]
        self.activate_menuitem.set_label(label[self.__core.get_activated()])

    # Callbacks
    def on_L_click(self, status_icon, data=None):
        logger.info("User has clicked the Caffeine icon")
        self.toggle_activated()

    def on_R_click(self, status_icon, mbutton, time, data=None):
        # popdown menu
        self.menu.show_all()

        self.menu.popup(None, None, None, self.status_icon, 3, time)

    # Window callbacks
    def on_add_button_clicked(self, button, data=None):
        response = self.ProcAdd.run()
        if response == 1:
            proc_name = self.ProcAdd.get_process_name()
            if proc_name:
                self.proc_liststore.append([get_icon_for_process(proc_name), proc_name])

                self.__process_manager.add_proc(proc_name)

    def on_remove_button_clicked(self, button, data=None):
        model, paths = self.selection.get_selected_rows()
        paths.reverse()
        for path in paths:
            self.__process_manager.remove_proc(model[path][1])
            model.remove(model.get_iter(path))

    def on_add_button_audio_clicked(self, button, data=None):
        response = self.ProcAdd.run()
        if response == 1:
            proc_name = self.ProcAdd.get_process_name()
            if proc_name:
                self.proc_liststore_audio.append([get_icon_for_process(proc_name), proc_name])

                self.__process_manager_audio.add_proc(proc_name)

    def on_remove_button_audio_clicked(self, button, data=None):
        model, paths = self.selection_audio.get_selected_rows()
        paths.reverse()
        for path in paths:
            self.__process_manager_audio.remove_proc(model[path][1])
            model.remove(model.get_iter(path))

    def on_window_delete_event(self, window, data=None):
        window.hide_on_delete()
        # Returning True stops the window from being destroyed.
        return True

    def on_close_button_clicked(self, button, data=None):
        self.window.hide()

    # Tray icon
    def on_trayicon_changed(self, settings, key, data=None):
        show_tray_icon = settings.get_boolean(key)

        if appindicator_avail:
            self.AppInd.set_status(
                [
                    AppIndicator3.IndicatorStatus.PASSIVE,
                    AppIndicator3.IndicatorStatus.ACTIVE,
                ][show_tray_icon]
            )

        else:
            self.status_icon.set_visible(show_tray_icon)

        self.trayicon_cb.set_active(show_tray_icon)
        self.notification_cb.set_sensitive(not show_tray_icon)

    # Startup Notifications
    def on_notification_changed(self, settings, key, data=None):
        pass

    def on_audio_peak_filtering_changed(self, settings, key, data=None):
        audio_filtering_active = settings.get_boolean(key)
        self.audio_peak_filtering_cb.set_active(audio_filtering_active)
        self.__core.set_audio_peak_filtering_active(audio_filtering_active)

    # Menu callbacks
    def on_activate_menuitem_activate(self, menuitem, data=None):
        self.toggle_activated()

        label = [_("Enable Caffeine"), _("Disable Caffeine")]
        menuitem.set_label(label[self.__core.get_activated()])

    def on_time_menuitem_activate(self, menuitem, data=None):
        self.othertime_dialog.show_all()

    def on_prefs_menuitem_activate(self, menuitem, data=None):
        self.window.show_all()

    def on_about_menuitem_activate(self, menuitem, data=None):
        self.about_dialog.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_othertime_delete_event(self, window, data=None):
        window.hide_on_delete()
        # Returning True stops the window from being destroyed.
        return True

    def on_othertime_cancel(self, widget, data=None):
        self.othertime_dialog.hide()

    def on_othertime_ok(self, widget, data=None):
        hours = int(self.othertime_hours.get_value())
        minutes = int(self.othertime_minutes.get_value())
        self.othertime_dialog.hide()
        time = hours * 60 * 60 + minutes * 60
        if time > 0:
            self.__core.timed_activation(time)

    def on_quit_menuitem_activate(self, menuitem, data=None):
        self.quit()

    def quit(self):
        # Do anything that needs to be done before quitting.
        logger.info("Caffeine is preparing to quit")

        # Make sure PM and SV is uninhibited
        self.__core.set_activated(False)
        self.__core.quit()
        Gtk.main_quit()

    def run(self):
        Gtk.main()
