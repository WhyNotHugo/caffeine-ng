
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

Also, this rewrite allows for cleaning up some skeletons in the closet.

- ``caffeine-ng`` now depend on ``click``, and no longer depends on ``docopt``.
- The CLI interface has changed slightly. When passing extra arguments use
  ``caffeine start``. For example ``caffeine start --activate``.

The way the PID file is handled has hardened and simplified, but this will
result in caffeine 4.0 not killing older versions. Exit any older versions that
may be running before upgrading (or simply restart after doing so).

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
