Taurine
=======

Taurine is a little daemon that sits in you systray, and prevents the
screensaver from showing up, or the systems from going to sleep.
It does so when an application is fullscreened (eg: youtube), or when you click
on the systray icon (which you can do, when, eg: reading).

This is a fork of [Caffeine 2.4](http://launchpad.net/caffeine/), since later
versions dropped support for the systray icon in favour of only automatic
detection of fullscreen apps only, which resulted rather
[controversial](https://bugs.launchpad.net/caffeine/+bug/1321750).

The intention of this fork is to also evolve on it's own, not only fixing
issues, but also implemented missing features, when relevant.

System requirements
-------------------

* Any Linux desktop system that offers the `org.freedesktop.ScreenSaver` DBus
  API.  This includes, but is not limited to, Linux Mint 16 and Ubuntu 14.04.
  Probably works on lots of older distributions, too.

* Python 2 and Python 3

* kaa-metadata, python-xlib, gir1.2-appindicator3-0.1

Installation
------------

* ```python setup.py install```

* To have Caffeine Plus run on startup, add it to your System Settings =>
  Startup Programs list.

License
-------

Taurine is distributed under the GNU General Public License, either version
3, or (at your option) any later version. See GPL for details.

The Taurine status icons are Copyright (C) 2014 mildmojo
(http://github.com/mildmojo), and distributed under the terms of the GNU Lesser
General Public License, either version 3, or (at your option) any later
version.  See LGPL.

The Taurine SVG shortcut icons are Copyright (C) 2009 Tommy Brunn
(http://www.blastfromthepast.se/blabbermouth), and distributed under the
terms of the GNU Lesser General Public License, either version 3, or (at
your option) any later version. See LGPL.

Hacking
-------

To run: ```./bin/caffeine```
To compile translations: ```./update_translations```

If you want to test out a translation without changing the language for the
whole session: "LANG=ru_RU.UTF-8 ./bin/caffeine" (Replace ru_RU.UTF-8
with whatever language you want to use. You will need to a language pack
for the specific language) Be aware that some stock items
will not be translated unless you log in with a given language.
