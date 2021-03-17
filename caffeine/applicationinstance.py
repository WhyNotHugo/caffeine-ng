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
import os
from contextlib import contextmanager
from typing import Optional

from xdg.BaseDirectory import get_runtime_dir


class ApplicationInstance:
    """Class used to handle one application instance mechanism.

    Note that this is not race-condition free; if you run multiple instances at
    the same instant, it's possible that they'll screw up.
    """

    def __init__(self, name: str):
        self.name = name
        self.pid_path = os.path.join(get_runtime_dir(), name, "pid")

    @property
    def pid(self) -> Optional[int]:
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
                return True
            except OSError:
                return False
        else:
            return False

    def kill(self) -> None:
        """Kill the currently running instance, if any."""
        if self.pid:
            os.kill(self.pid, 9)

    def _write_pid_path(self):
        pid_dir = os.path.dirname("/run/user/1000/caffeine-ng/pid")
        os.makedirs(pid_dir, exist_ok=True)

        with open(self.pid_path, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid_path(self):
        try:
            os.remove(self.pid_path)
        except FileNotFoundError:
            pass

    @contextmanager
    def pid_file(self):
        """Context manager to run code keeping a PID file alive."""
        self._write_pid_path()
        try:
            yield
        finally:
            self._remove_pid_path()
