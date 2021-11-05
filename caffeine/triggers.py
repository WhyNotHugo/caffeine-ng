"""Triggers are different events or states that auto-activate caffeine."""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from ewmh import EWMH
from pulsectl import Pulse
from pulsectl.pulsectl import PulseIndexError

from caffeine import utils
from caffeine.procmanager import ProcManager  # noqa: E402

logger = logging.getLogger(__name__)


class DesiredState(Enum):
    UNINHIBITED = 0  # Don't inhibit anything.
    INHIBIT_SLEEP = 5  # Only inhibit sleeping (screen saver can go off).
    INHIBIT_ALL = 10  # Inhibit both screen saver and sleeping.

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented


class ManualTrigger:
    active = False

    def run(self) -> DesiredState:
        if self.active:
            return DesiredState.INHIBIT_ALL
        else:
            return DesiredState.UNINHIBITED


@dataclass
class WhiteListTrigger:
    process_manager: ProcManager

    def run(self) -> DesiredState:
        """Determine if one of the whitelisted processes is running."""

        for proc in self.process_manager.get_process_list():
            if utils.is_process_running(proc):
                logger.info("Process %s detected. Inhibiting.")
                return DesiredState.INHIBIT_ALL

        return DesiredState.UNINHIBITED


class FullscreenTrigger:
    def __init__(self):
        self._ewmh = EWMH()

    def run(self) -> DesiredState:
        """Determine if a fullscreen application is running."""
        inhibit = False

        window = self._ewmh.getActiveWindow()

        # ewmh.getWmState(window) returns None is scenarios where
        # ewmh.getWmState(window, str=True) throws an exception
        # (it's a bug in pyewmh):
        if window and self._ewmh.getWmState(window):
            wm_state = self._ewmh.getWmState(window, True)
            inhibit = "_NET_WM_STATE_FULLSCREEN" in wm_state

        if inhibit:
            logger.info("Fullscreen app detected.")
            return DesiredState.INHIBIT_ALL

        return DesiredState.UNINHIBITED


class PulseAudioTrigger:
    def __init__(
        self,
        process_manager: ProcManager,
        audio_peak_filtering_active_getter: Callable[[], bool],
    ) -> None:
        self.__process_manager = process_manager
        self.__audio_peak_filtering_active_getter = audio_peak_filtering_active_getter

    @property
    def __audio_peak_filtering_active(self) -> bool:
        return self.__audio_peak_filtering_active_getter()

    def run(self) -> DesiredState:
        # Let's look for playing audio:
        # Number of supposed audio only streams.  We can turn the screen off
        # for those:
        music_procs = 0
        # Number of all audio streams including videos. We keep the screen on
        # here:
        screen_relevant_procs = 0
        # Applications currently playing audio.
        active_applications = []
        # Applications whose audio activity is ignored
        ignored_applications = self.__process_manager.get_process_list()

        # Get all audio playback streams
        # Music players seem to use the music role. We can turn the screen
        # off there. Keep the screen on for audio without music role,
        # as they might be videos
        with Pulse() as pulseaudio:
            for application_output in pulseaudio.sink_input_list():
                if (
                    not application_output.mute  # application audio is not muted
                    and not application_output.corked  # application audio is not paused
                    and not pulseaudio.sink_info(
                        application_output.sink
                    ).mute  # system audio is not muted
                ):
                    application_name = application_output.proplist.get(
                        "application.process.binary", "no name"
                    )
                    if application_name in ignored_applications:
                        continue
                    if self.__audio_peak_filtering_active:
                        # ignore silent sinks
                        sink_source = pulseaudio.sink_info(
                            application_output.sink
                        ).monitor_source
                        sink_peak = pulseaudio.get_peak_sample(sink_source, 0.4)
                        if not sink_peak > 0:
                            continue
                    if application_output.proplist.get("media.role") == "music":
                        # seems to be audio only
                        music_procs += 1
                    else:
                        # Video or other audio source
                        screen_relevant_procs += 1
                    # Save the application's process name
                    active_applications.append(application_name)

            # Get all audio recording streams
            for application_input in pulseaudio.source_output_list():
                try:
                    system_input_muted = pulseaudio.source_info(
                        application_input.source
                    ).mute
                except PulseIndexError:
                    system_input_muted = False
                if (
                    not application_input.mute  # application input is not muted
                    and not system_input_muted
                ):
                    application_name = application_input.proplist.get(
                        "application.process.binary", "no name"
                    )
                    if application_name in ignored_applications:
                        continue
                    if self.__audio_peak_filtering_active:
                        # ignore silent sources
                        source_peak = pulseaudio.get_peak_sample(
                            application_input.source, 0.1
                        )
                        if not (source_peak > 0):
                            continue
                    # Treat recordings as video because likely you don't
                    # want to turn the screen of while recording
                    screen_relevant_procs += 1
                    # Save the application's process name
                    active_applications.append(application_name)

        if screen_relevant_procs > 0:
            logger.debug(f"Video playback detected ({', '.join(active_applications)}).")
            return DesiredState.INHIBIT_ALL
        elif music_procs > 0:
            logger.debug(f"Audio playback detected ({', '.join(active_applications)}).")
            return DesiredState.INHIBIT_SLEEP
        else:
            return DesiredState.UNINHIBITED
