Caffeine-ng
===========

⚠️ Migrated to codeberg.org
--------------------------
This project has `migrated to codeberg.org`_
--------------------------------------------

.. _migrated to codeberg.org: https://codeberg.org/WhyNotHugo/caffeine-ng

.. image:: https://travis-ci.com/caffeine-ng/caffeine-ng.svg?branch=master
  :target: https://travis-ci.com/caffeine-ng/caffeine-ng
  :alt: build status

.. image:: https://img.shields.io/pypi/v/caffeine-ng.svg
  :target: https://pypi.python.org/pypi/caffeine-ng
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/caffeine-ng.svg
  :target: https://github.com/caffeine-ng/caffeine-ng/blob/master/LICENCE
  :alt: licence

Caffeine is a little daemon that sits in your systray, and prevents the
screensaver from showing up, or the system from going to sleep. It does so when
an application is fullscreened (eg: youtube), or when you click on the systray
icon (which you can do, when, eg: reading).

History
-------

Caffeing-ng (since 2014) started as a fork of `Caffeine 2.4`_, since the
original version dropped support for the systray icon in favour of only
automatic detection of fullscreen apps only, which turned to be a rather
`controversial`_ decision.

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

* Python 3.6 to 3.9 is required.

* ``caffeine-ng`` works with the following screensavers / screenlockers:

  * Anything that implements the ``org.freedesktop.ScreenSaver`` API (this
    includes KDE, amongst others)
  * gnome-screensaver
  * XSS
  * Xorg + DPMS
  * xautolock
  * xidlehook.

See ``setup.py`` for required python packages

Installation
------------

Generic installation
....................

To manually install caffeine-ng, run::

      python setup.py build
      sudo python setup.py install
      sudo glib-compile-schemas /usr/share/glib-2.0/schemas

Debian and derivatives
......................

First install all the required packages::

      apt install python-click python-ewmh python-setproctitle python-wheel python-xdg

And mark them auto if you wish::

      apt-mark auto python-click python-ewmh python-setproctitle python-wheel python-xdg

Then you need to build sources with::

      make clean
      make build

Create a package for your distribution::

      checkinstall --pkgname=caffeine-ng --pkgversion=3.4 --requires="python-click \(\>=0.6.2\),python-ewmh \(\>=0.1.4\),python-setproctitle \(\>=1.1.10\),python-wheel \(\>=0.29.0\),python-xdg \(\>=0.25\)" --conflicts="caffeine" --nodoc python ./setup.py install --install-layout=deb

Replace version string with correct version and append this command with
``--install=no`` should you wish to inspect created package before installing
it Replace ``python`` with ``python3`` in package names above if you wish to
build caffeine-ng with python 3

Replace ``python`` with ``python3`` in ``checkinstall`` invocation to use
specific python version to build caffeine-ng.

``checkinstall`` is available for various distributions, so you may follow
these steps adapting them to your distribution

ArchLinux
.........

On ArchLinux, caffeine-ng is available at the `AUR`_.

.. _AUR: https://aur.archlinux.org/packages/caffeine-ng/

Gentoo
......

Gentoo users may find `caffeine-ng <https://github.com/PF4Public/gentoo-overlay/tree/master/x11-misc/caffeine-ng>`_ in `::pf4public <https://github.com/PF4Public/gentoo-overlay>`_ Gentoo overlay

Auto-start
----------

To have Caffeine-ng run on startup, add it to your System Settings => Startup
Programs list.

License
-------

Copyright (C) 2009 The Caffeine Developers
Copyright (C) 2014-2022 Hugo Osvaldo Barrera <hugo@barrera.io>

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
