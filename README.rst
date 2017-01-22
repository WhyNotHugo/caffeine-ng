Caffeine-ng
===========

.. image:: https://gitlab.com/hobarrera/caffeine-ng/badges/master/build.svg
  :target: https://gitlab.com/hobarrera/caffeine-ng/commits/master
  :alt: build status

.. image:: https://img.shields.io/pypi/v/caffeine-ng.svg
  :target: https://pypi.python.org/pypi/caffeine-ng
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/caffeine-ng.svg
  :alt: licence

Caffeine is a little daemon that sits in your systray, and prevents the
screensaver from showing up, or the system from going to sleep.
It does so when an application is fullscreened (eg: youtube), or when you click
on the systray icon (which you can do, when, eg: reading).

This is a fork of `Caffeine 2.4`_, since later
versions dropped support for the systray icon in favour of only automatic
detection of fullscreen apps only, which resulted rather
`controversial`_.

The intention of this fork is to also evolve on its own, not only fixing
issues, but also implemented missing features, when relevant.

Caffeine-ng was shortly know as Taurine, a play on its successor's name, since
taurine is a known stimulant, commonly found in energy drinks.  However, this
name did not last, since the artwork would not match adequately, and changing
it was undesirable.

.. _Caffeine 2.4: http://launchpad.net/caffeine/
.. _controversial: https://bugs.launchpad.net/caffeine/+bug/1321750

System requirements
-------------------

* Either a screensaver that implements the ``org.freedesktop.ScreenSaver``
  API (this includes KDE, amongst others) API, gnome-screensaver, XSS and/or
  DPMS, xautolock.
* Python 3

See ``requirements.txt`` for required python packages

Installation
------------

To manually install caffeine-ng, run::

      python setup.py build
      sudo python setup.py install
      sudo glib-compile-schemas /usr/share/glib-2.0/schemas

Or pre-packaged:

* On ArchLinux, caffeine-ng is available at the `AUR`_.

To have Caffeine-ng run on startup, add it to your System Settings => Startup
Programs list.

.. _AUR: https://aur.archlinux.org/packages/caffeine-ng/

License
-------

Copyright (C) 2009 The Caffeine Developers
Copyright (C) 2014-2017 Hugo Osvaldo Barrera <hugo@barrera.io>

Caffeine-ng is distributed under the GNU General Public License, either version
3, or (at your option) any later version. See LICENCE for details.

The Caffeine-ng status icons are Copyright (C) 2014 mildmojo
(http://github.com/mildmojo), and distributed under the terms of the GNU Lesser
General Public License, either version 3, or (at your option) any later
version.  See LGPL.

The Caffeien-ng SVG shortcut icons are Copyright (C) 2009 Tommy Brunn
(http://www.blastfromthepast.se/blabbermouth), and distributed under the
terms of the GNU Lesser General Public License, either version 3, or (at
your option) any later version. See LGPL.

Hacking
-------

* To run: ``./bin/caffeine``
* To compile translations: ``./update_translations``

If you want to test out a translation without changing the language for the
whole session: "LANG=ru_RU.UTF-8 ./bin/caffeine" (Replace ru_RU.UTF-8
with whatever language you want to use. You will need to a language pack
for the specific language) Be aware that some stock items
will not be translated unless you log in with a given language.
