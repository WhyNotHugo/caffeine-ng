#!/usr/bin/env python

from distutils.core import setup
from os import makedirs, walk
from os.path import exists, abspath, join, dirname
import subprocess


def get_version():
    """Returns the current version. If this is a git checkout, add HEAD to
    it."""
    version = open("VERSION").readline().strip()
    if exists(".git"):
        git_rev = subprocess.getoutput("git rev-parse --short HEAD")
        version += "-r" + git_rev

    return version


if __name__ == "__main__":
    script_path = abspath(__file__)
    share_path = join(dirname(script_path), "share")

    # Write the current version into share/caffeine/VERSION
    open(join(share_path, "caffeine", "VERSION"), "w").write(get_version())
    version_file = join("share", "caffeine")

    data_files = []
    for path, dirs, files in walk(share_path):
        clean_path = path.replace(share_path, "share", 1)
        data_files.append((clean_path, [join(path, file) for file in files]))

    desktop_file = join("share", "applications", "caffeine.desktop")
    autostart_dir = join("etc", "xdg", "autostart")

    if not exists(autostart_dir):
        makedirs(autostart_dir)

    data_files.append(("/" + autostart_dir, [desktop_file]))

    setup(name="caffeine-ng",
          version=get_version(),
          description="""A status bar application able to temporarily prevent
          the activation of both the screensaver and the "sleep" powersaving
          mode.""",
          author="The Caffeine Developers",
          author_email="hugo@barrera.io",
          maintainer="Hugo Osvaldo Barrera",
          maintainer_email="hugo@barrera.io",
          url="https://github.com/hobarrera/caffeine-ng",
          packages=["caffeine"],
          data_files=data_files,
          scripts=["bin/caffeine"],
          classifiers=[
              'Development Status :: 5 - Production/Stable',
              'Environment :: X11 Applications',
              'Environment :: X11 Applications :: GTK',
              'Intended Audience :: End Users/Desktop',
              'License :: OSI Approved :: GNU General Public License v3',
              'Operating System :: POSIX',
              'Operating System :: POSIX :: BSD',
              'Operating System :: POSIX :: Linux',
              'Programming Language :: Python :: 3',
              ]

          )
