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

from .paths import get_whitelist_file


class ProcManager:

    def __init__(self):
        self.whitelist_file = get_whitelist_file()
        self.proc_list = []

        if os.path.exists(self.whitelist_file):
            self.import_proc(self.whitelist_file)

    def get_process_list(self):
        return self.proc_list[:]

    def add_proc(self, name):
        if name not in self.proc_list:
            self.proc_list.append(name)
        self.save()

    def remove_proc(self, name):
        self.proc_list.remove(name)
        self.save()

    def import_proc(self, filename):
        for line in open(filename):
            line = line.strip()
            if line not in self.proc_list:
                self.proc_list.append(line)
        self.save()

    def save(self):
        self.proc_list.sort()
        with open(self.whitelist_file, "w") as f:
            f.write("\n".join(self.proc_list))
