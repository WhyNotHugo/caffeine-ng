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
import os.path


class ApplicationInstance:
    """Class used to handle one application instance mechanism."""

    def __init__(self, pid_file):
        self.pid_file = pid_file

    @property
    def pid(self):
        if os.path.isfile(self.pid_file):
            with open(self.pid_file) as f:
                try:
                    pid = int(f.read())
                except ValueError:
                    pid = None
            return pid
        else:
            return None

    def is_running(self):
        if self.pid:
            try:
                os.kill(self.pid, 0)
                return True
            except OSError:
                return False
        else:
            return False

    def kill(self):
        os.kill(self.pid, 9)

    def write_pid_file(self):
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))

    def remove_pid_file(self):
        try:
            os.remove(self.pid_file)
        except FileNotFoundError:
            pass
