# Copyright (c) 2014-2021 Hugo Osvaldo Barrera
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
import fcntl
import logging
import os
from contextlib import contextmanager
from typing import Optional

from xdg.BaseDirectory import get_runtime_dir

logger = logging.getLogger(__name__)


class AlreadyRunning(Exception):
    """Raised when another instance is already running."""

    def __str__(self):
        return "An instance is already running."


class ApplicationInstance:
    """Class used to handle one application instance mechanism."""

    def __init__(self, name: str):
        self.name = name
        self.pid_path = os.path.join(get_runtime_dir(), name, "pid")

    @property
    def pid(self) -> Optional[int]:
        """Return the PID of an already-running instance, if any."""
        try:
            with open(self.pid_path) as f:
                return int(f.read())
        except (ValueError, FileNotFoundError):
            return None

    def is_running(self) -> bool:
        """Return true if an instance is already running."""
        if self.pid:
            try:
                os.kill(self.pid, 0)
                logger.debug("An instance is already running: %d.", self.pid)
                return True
            except OSError:
                pass

        return False

    def kill(self) -> None:
        """Kill the currently running instance, if any."""
        if self.pid:
            os.kill(self.pid, 9)

    @contextmanager
    def pid_file(self):
        """Context manager to run code keeping a PID file alive."""

        pid_dir = os.path.dirname(self.pid_path)
        os.makedirs(pid_dir, exist_ok=True)

        handle = open(self.pid_path, "w+")

        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise AlreadyRunning()

        handle.seek(0)
        handle.write(str(os.getpid()))
        handle.flush()

        try:
            yield
        finally:
            try:
                os.remove(self.pid_path)
            except FileNotFoundError:
                pass
