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
import logging
import os
from typing import Generator

logger = logging.getLogger(__name__)


def get_process_name(pid: int) -> str:
    """Gets process name from process id."""

    truncated_process_name = open("/proc/%s/status" % pid).readline()[6:-1]
    process_name = truncated_process_name

    line = open("/proc/%s/cmdline" % pid).readline()
    parts = line.split("\x00")
    for part in parts:
        cmd_name = part.split("/")[-1]

        if cmd_name.startswith(truncated_process_name):
            process_name = cmd_name

    return process_name


def get_processes() -> Generator[str, None, None]:
    """Return a generator of names of running processes."""

    for pid in os.listdir("/proc/"):
        try:
            num_pid = int(pid)
        except ValueError:
            continue

        try:
            process_name = get_process_name(num_pid).lower()
        except Exception:
            logger.exception(f"Failed to get name for process {num_pid}")
            continue

        yield process_name


def is_process_running(name: str) -> bool:
    """Return True is a process with the given name is running."""

    return name in get_processes()
