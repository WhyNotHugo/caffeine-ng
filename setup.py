#!/usr/bin/env python

import os
from os import walk

from setuptools import find_packages, setup


def get_data_files():
    data_files = []

    for path, dirs, files in walk('share'):
        target_path = os.path.join('/usr', path)

        data_files.append((
            target_path, [os.path.join(path, f) for f in files]
        ))

    data_files.append(
        ("/etc/xdg/autostart", ["share/applications/caffeine.desktop"])
    )

    return data_files


if __name__ == "__main__":
    setup(
        name="caffeine-ng",
        use_scm_version={
            'version_scheme': 'post-release',
            'write_to': 'caffeine/version.py',
        },
        description=(
            "Tray bar app to temporarily inhibit screensaver and sleep mode."
        ),
        long_description=open('README.rst').read(),
        author="The Caffeine Developers",
        author_email="hugo@barrera.io",
        maintainer="Hugo Osvaldo Barrera",
        maintainer_email="hugo@barrera.io",
        url="https://github.com/caffeine-ng/caffeine-ng",
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
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
        ],
        setup_requires=['setuptools_scm'],
    )
