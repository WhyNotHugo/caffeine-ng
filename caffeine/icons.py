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
from os.path import join

from gi.repository import Gtk

from .paths import ICON_PATH
from .paths import IMAGE_PATH


def get_icon_pixbuf(size):
    """
    Returns the icon as a pixbuf.

    Returns caffeine's icon as a pixbuf. We wrap around GTK here, so the
    default theme's icon will be used, if any, or caffeine's own as a fallback.
    """
    icon_name = "caffeine"
    icon_theme = Gtk.IconTheme.get_default()

    icon_info = icon_theme.lookup_icon(icon_name, size, Gtk.IconLookupFlags.NO_SVG)

    if icon_info:
        # icon is found
        base_size = icon_info.get_base_size()
        if base_size != size:
            # No size x size icon in the users theme so use the default
            icon_theme = Gtk.IconTheme()
            icon_theme.set_search_path((ICON_PATH,))
    else:
        icon_theme.append_search_path(ICON_PATH)
        icon_info = icon_theme.lookup_icon(icon_name, size, Gtk.IconLookupFlags.NO_SVG)

    pixbuf = icon_theme.load_icon(icon_name, size, Gtk.IconLookupFlags.NO_SVG)

    return pixbuf


generic_icon = join(IMAGE_PATH, "application-x-executable.png")

full_cup_icon = join(IMAGE_PATH, "Full_Cup.svg")
empty_cup_icon = join(IMAGE_PATH, "Empty_Cup.svg")
