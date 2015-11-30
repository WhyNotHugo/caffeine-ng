#!/usr/bin/env python

from setuptools import setup, find_packages
from os import makedirs, walk
from os.path import exists, abspath, join, dirname


if __name__ == "__main__":
    script_path = abspath(__file__)
    share_path = join(dirname(script_path), "share")

    data_files = []
    for path, dirs, files in walk(share_path):
        clean_path = path.replace(share_path, "/usr/share", 1)
        data_files.append((clean_path, [join(path, file) for file in files]))

    desktop_file = join("share", "applications", "caffeine.desktop")
    autostart_dir = join("etc", "xdg", "autostart")

    if not exists(autostart_dir):
        makedirs(autostart_dir)

    data_files.append(("/" + autostart_dir, [desktop_file]))

    setup(name="caffeine-ng",
          use_scm_version={
              'version_scheme': 'post-release',
              'write_to': 'caffeine/version.py',
          },
          description="""A status bar application able to temporarily prevent
          the activation of both the screensaver and the "sleep" powersaving
          mode.""",
          author="The Caffeine Developers",
          author_email="hugo@barrera.io",
          maintainer="Hugo Osvaldo Barrera",
          maintainer_email="hugo@barrera.io",
          url="https://github.com/hobarrera/caffeine-ng",
          packages=find_packages(),
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
              ],
          setup_requires=['setuptools_scm'],
          )
