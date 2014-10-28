#!/usr/bin/env python

from distutils.core import setup
import os
import shutil
import subprocess


def get_version():
    """Returns the current version. If this is a git checkout, add HEAD to
    it."""
    version = open("VERSION").readline().strip()
    if os.path.exists(".git"):
        git_rev = subprocess.getoutput("git rev-parse --short HEAD")
        version += "-r" + git_rev

    return version


if __name__ == "__main__":
    script_path = os.path.abspath(__file__)
    share_path = os.path.join(os.path.dirname(script_path), "share")

    # Write the current version into share/caffeine/VERSION
    open(os.path.join(share_path, "caffeine", "VERSION"), "w") \
        .write(get_version())
    version_file = os.path.join("share", "caffeine")

    data_files = []

    for path, dirs, files in os.walk(share_path):
        clean_path = path.replace(share_path, "share", 1)
        data_files.append(tuple((clean_path, [os.path.join(path, file)
                                              for file in files])))

    desktop_name = "caffeine.desktop"
    desktop_file = os.path.join("share", "applications", desktop_name)

    autostart_dir = os.path.join("etc", "xdg", "autostart")

    if not os.path.exists(autostart_dir):
        os.makedirs(autostart_dir)

    shutil.copy(desktop_file, autostart_dir)
    data_files.append(tuple(("/" + autostart_dir,
                             [os.path.join(autostart_dir, desktop_name)])))

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
