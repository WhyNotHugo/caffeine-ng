#!/usr/bin/env python

from setuptools import setup, find_packages
from os import walk
from os.path import abspath, join, dirname


def get_data_files():
    script_path = abspath(__file__)
    share_path = join(dirname(script_path), "share")

    data_files = []
    for path, dirs, files in walk(share_path):
        clean_path = path.replace(share_path, "/usr/share", 1)
        data_files.append((clean_path, [join(path, file) for file in files]))

    data_files.append(
        ("/etc/xdg/autostart", ["share/applications/caffeine.desktop"])
    )

    return data_files


def get_description():
    return """A status bar application able to temporarily prevent the
activation of both the screensaver and the "sleep" powersaving mode."""


if __name__ == "__main__":
    setup(
        name="caffeine-ng",
        use_scm_version={
            'version_scheme': 'post-release',
            'write_to': 'caffeine/version.py',
        },
        description=get_description(),
        author="The Caffeine Developers",
        author_email="hugo@barrera.io",
        maintainer="Hugo Osvaldo Barrera",
        maintainer_email="hugo@barrera.io",
        url="https://github.com/hobarrera/caffeine-ng",
        packages=find_packages(),
        data_files=get_data_files(),
        install_requires=open('requirements.txt').read().splitlines(),
        entry_points={
            'gui_scripts': [
                'caffeine = caffeine.main:main'
            ]
        },
        classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: X11 Applications',
          'Environment :: X11 Applications :: GTK',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: BSD',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3',
        ],
        setup_requires=['setuptools_scm'],
    )
