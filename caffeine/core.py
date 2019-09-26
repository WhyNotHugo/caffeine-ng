# Copyright (c) 2014-2015 Hugo Osvaldo Barrera
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

import logging
import os
import os.path
from gettext import gettext as _
from threading import Timer

from ewmh import EWMH
from gi.repository import GLib, GObject, Notify
from pulsectl import Pulse

from . import utils
from .icons import empty_cup_icon, full_cup_icon
from .inhibitors import DpmsInhibitor, GnomeInhibitor, XautolockInhibitor, \
    XdgPowerManagmentInhibitor, XdgScreenSaverInhibitor, XorgInhibitor, \
    XssInhibitor

# from pympler import tracker
# tr = tracker.SummaryTracker()


logging.basicConfig(level=logging.INFO)
os.chdir(os.path.abspath(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)


class Caffeine(GObject.GObject):

    def __init__(self, process_manager):
        GObject.GObject.__init__(self)

        self.__inhibitors = [
            GnomeInhibitor(),
            XdgPowerManagmentInhibitor(),
            XssInhibitor(),
            XorgInhibitor(),
            XautolockInhibitor(),
            XdgScreenSaverInhibitor(),
            DpmsInhibitor()
        ]

        self.__process_manager = process_manager

        # Status string (XXX: Let's double check how well this is working).
        self.status_string = "Caffeine is starting up..."

        # Inhibition has been requested (though it may not yet be active).
        self.__inhibition_manually_requested = False

        # Number of procs playing audio but nothing visual. This is a special
        # case where we want the screen to turn off while still preventing
        # the computer from suspending
        self.music_procs = 0

        # Inhibition has successfully been activated.
        self.__inhibition_successful = False

        self.__auto_activated = False
        self.timer = None
        self.notification = None

        self._ewmh = EWMH()

        # FIXME: add capability to xdg-screensaver to report timeout.
        GLib.timeout_add(10000, self.__attempt_autoactivation)

        logger.info(self.status_string)

    def __attempt_autoactivation(self):
        """
        Determines if we want to auto-activate inhibition by verifying if any
        of the whitelisted processes is running OR if there's a fullscreen app.
        """
        # tr.print_diff()

        if self.get_activated() and not self.__auto_activated:
            logger.debug("Inhibition manually activated. Won't attempt to " +
                         "auto-activate")
            return True

        process_running = False

        # Determine if one of the whitelisted processes is running.
        for proc in self.__process_manager.get_process_list():
            if utils.isProcessRunning(proc):
                process_running = True

                if self.__auto_activated:
                    logger.info("Process %s detected. No change.", proc)
                elif not self.get_activated():
                    logger.info("Process %s detected. Inhibiting.", proc)

        # If none where running, let's look for fullscreen:
        if not process_running:
            # Determine if a fullscreen application is running
            window = self._ewmh.getActiveWindow()
            # ewmh.getWmState(window) returns None is scenarios where
            # ewmh.getWmState(window, str=True) throws an exception
            # (it's a bug in pyewmh):
            if window and self._ewmh.getWmState(window):
                fullscreen = "_NET_WM_STATE_FULLSCREEN" in \
                    self._ewmh.getWmState(window, True)
            else:
                fullscreen = False

            if fullscreen:
                if self.__auto_activated:
                    logger.debug("Fullscreen app detected. No change.")
                elif not self.get_activated():
                    logger.info("Fullscreen app detected. Inhibiting.")

        # Let's look for playing audio:
        # Number of supposed audio only streams.  We can turn the screen off
        # for those:
        self.music_procs = 0
        # Number of all audio streams including videos. We keep the screen on
        # here:
        screen_relevant_procs = 0

        if not process_running and not fullscreen:
            # Get all audio playback streams
            # Music players seem to use the music role. We can turn the screen
            # off there. Keep the screen on for audio without music role,
            # as they might be videos
            with Pulse() as pulseaudio:
                for sink in pulseaudio.sink_input_list():
                    sink_source = pulseaudio.sink_info(sink.sink).monitor_source
                    sink_peak = pulseaudio.get_peak_sample(sink_source, 0.1)
                    if sink_peak > 0:
                        if sink.proplist.get('media.role') == "music":
                            # Seems to be audio only.
                            self.music_procs += 1
                        else:
                            # Video or other audio source.
                            screen_relevant_procs += 1

            if self.music_procs > 0 or screen_relevant_procs > 0:
                if self.__auto_activated:
                    logger.debug("Audio playback detected. No change.")
                elif not self.get_activated():
                    logger.info("Audio playback detected. Inhibiting.")

        if (
            process_running
            or fullscreen
            or self.music_procs > 0
            or screen_relevant_procs > 0
        ) and not self.__auto_activated:
            self.__auto_activated = True
            # TODO: Check __set_activated
            self.__set_activated(True)
        elif not (
            process_running or
            fullscreen
            or self.music_procs > 0
            or screen_relevant_procs > 0
        ) and self.__auto_activated:
            logger.info(
                "Was auto-inhibited, but there's no fullscreen, whitelisted "
                "process or audio playback now. De-activating."
            )
            # TODO: Check __set_activated
            self.__set_activated(False)
            self.__auto_activated = False

        return True

    def quit(self):
        """
        Cancels any timer thread running so the program can quit right away.
        """
        if self.timer:
            self.timer.cancel()

    def _notify(self, message, icon, title="Caffeine"):
        """Easy way to use pynotify."""

        # try:
        Notify.init("Caffeine")
        if self.notification:
            self.notification.update(title, message, icon)
        else:
            self.notification = Notify.Notification.new(title, message, icon)

        # XXX: Notify OSD doesn't seem to work when sleep is prevented
        # if self.screenSaverCookie is not None and \
        #    self.__inhibition_successful:
        #     self.ssProxy.UnInhibit(self.screenSaverCookie)

        self.notification.show()

        # if self.screenSaverCookie is not None and \
        #    self.__inhibition_successful:
        #     self.screenSaverCookie = \
        #         self.ssProxy.Inhibit("Caffeine",
        #                              "User has requested that Caffeine "+
        #                              "disable the screen saver")

        # except Exception as e:
        #     logger.error("Exception occurred:\n%s", e)
        # finally:
        #     return False

    def timed_activation(self, time, show_notification=True):
        """Calls toggle_activated after the number of seconds
        specified by time has passed.
        """
        message = (_("Timed activation set; ") +
                   _("Caffeine will prevent powersaving for the next ") +
                   str(time))

        logger.info("Timed activation set for " + str(time))

        if self.status_string == "":
            self.status_string = _("Activated for ") + str(time)
            self.emit("activation-toggled", self.get_activated(),
                      self.status_string)

        self.set_activated(True, show_notification)

        if show_notification:
            self._notify(message, full_cup_icon)

        # and deactivate after time has passed.
        # Stop already running timer
        if self.timer:
            logger.info("Previous timed activation cancelled due to a " +
                        "second timed activation request (was set for " +
                        str(self.timer.interval) + " or " +
                        str(time)+" seconds )")
            self.timer.cancel()

        self.timer = Timer(time, self._deactivate, args=[show_notification])
        self.timer.name = "Active"
        self.timer.start()

    def _deactivate(self, show_notification):
        self.timer.name = "Expired"
        self.toggle_activated(show_notification)

    def __set_activated(self, activate):
        """Enables inhibition, but does not mark is as manually enabled.
        """
        if self.get_activated() != activate:
            self.__toggle_activated(activate)

    def get_activated(self):
        """Returns True if inhibition was manually activated.
        """
        return self.__inhibition_manually_requested

    def set_activated(self, activate, show_notification=True):
        """Sets inhibition as manually activated.
        """
        if self.get_activated() != activate:
            self.toggle_activated(show_notification)

    def toggle_activated(self, show_notification=True):
        """ *Manually* toggles inhibition.  """

        self.__auto_activated = False
        self.__toggle_activated(note=show_notification)

    def __toggle_activated(self, note):
        """
        Toggle inhibition.
        """

        if self.__inhibition_manually_requested:
            # sleep prevention was on now turn it off

            self.__inhibition_manually_requested = False
            logger.info("Caffeine is now dormant; powersaving is re-enabled.")
            self.status_string = \
                _("Caffeine is dormant; powersaving is enabled")

            # If the user clicks on the full coffee-cup to disable
            # sleep prevention, it should also
            # cancel the timer for timed activation.

            if self.timer is not None and self.timer.name != "Expired":
                message = (_("Timed activation cancelled (was set for ") +
                           str(self.timer.interval) + ")")

                logger.info("Timed activation cancelled (was set for " +
                            str(self.timer.interval) + ")")

                if note:
                    self._notify(message, empty_cup_icon)

                self.timer.cancel()
                self.timer = None

            elif self.timer is not None and self.timer.name == "Expired":
                message = (str(self.timer.interval) +
                           _(" have elapsed; powersaving is re-enabled"))

                logger.info("Timed activation period (" +
                            str(self.timer.interval) +
                            ") has elapsed")

                if note:
                    self._notify(message, empty_cup_icon)

                self.timer = None

        else:
            self.__inhibition_manually_requested = True

        # decide, if we allow the screen to sleep
        if (self.music_procs > 0 or not self.__inhibition_manually_requested):
            inhibit_screen = False
        else:
            inhibit_screen = True

        self._performTogglingActions(self.__inhibition_manually_requested,
                                     inhibit_screen)
        logger.info("\n\n")
        self.status_string = "Caffeine is preventing powersaving."

        self.emit("activation-toggled", self.get_activated(),
                  self.status_string)
        self.status_string = ""

    def _performTogglingActions(self, suspend, susp_screen):
        """This method performs the actions that affect the screensaver and
        powersaving."""

        for inhibitor in self.__inhibitors:
            if inhibitor.applicable:
                inhibitor.set(susp_screen) if inhibitor.is_screen_inhibitor() \
                                              else inhibitor.set(suspend)
                logger.info("%s is applicable, state: %s"
                            % (inhibitor, inhibitor.running))
        self.__inhibition_successful = not self.__inhibition_successful


# register a signal
GObject.signal_new("activation-toggled", Caffeine,
                   GObject.SignalFlags.RUN_FIRST, None, [bool, str])
