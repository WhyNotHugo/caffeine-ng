
Changelog
=========

v4.0.0
------

Command line usage changes
..........................

This release rewrites the CLI portion of caffeine-ng into ``click``. ``click``
is the standard library in python for writing CLI apps, and is better
maintained. This is part of an initiative to bring caffeine to a more modern
stack and facilitate future development on it.

This rewrite also allowed for cleaning up some skeletons in the closet.

``caffeine-ng`` now depends on ``click``, and no longer depends on ``docopt``.

The CLI interface has changed slightly, but should now be more easy to
navigate. See ``caffeine --help``, ``caffeine start --help``, etc.

The way the PID file is handled has been hardened and simplified, but this will
result in caffeine 4.0 not killing older versions. Exit any older versions that
may be running before upgrading (or simply don't restart it until your next
reboot).

Status icon changes
...................

The `libappindicator` dependency is now mandatory.

Previously, we'd determine whether to use StatusIcon vs AppIndicator based on
the presence of this dependency. This was problematic for users who had the
library installed as a dependency for another program, but wanted StatusIcons.
If you want a StatusIcon, please set the `CAFFEINE_LEGACY_TRAY` to any value.

This also reduces confusion for users of desktops that _only_ support
AppIndicator, but were unaware of the difference or unaware of the optional
dependency.

If your desktop *does not* support AppIndicator, fallback to using a StatusIcon
should be automatic. If you get *no* icon out-of-the-box, please report the
issue.


Other changes
.............

 - Xorg-based inhibitors are now disabled on Wayland.

 - Python 3.6 or later is required. Python 3.6 and 3.7 are deprecated and will
   soon be dropped. This will be the last release with support for these
   versions.

 - Added support for xfce "presentation mode".

 - **Breaking**: python-docopt is no longer required. python-click is now
   required.

 - Pulseaudio support has been reworked, and should have less false positives,
   but it's still imperfect. In future, an MPRIS alternative might be a
   suitable replacement.

 - Various translations have been updated.

 - Desktop entries no longer have absolute paths, which should ease writing
   wrapper scripts or using tools like Firejail.

 - The "preferences" desktop entry has been dropped.
