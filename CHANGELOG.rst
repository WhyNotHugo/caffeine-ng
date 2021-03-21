
Changelog
=========

v4.0.0
------

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
,may be running before upgrading (or simply restart after doing so).
