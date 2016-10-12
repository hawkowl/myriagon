#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import, print_function

from setuptools import find_packages
from setuptools import setup

setup(
    name='myriagon',
    license='MIT',
    use_incremental=True,
    description='Time tracking, task tracking.',
    author='Amber Brown',
    author_email='hawkowl@atleastfornow.net',
    url='https://github.com/hawkowl/myriagon',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Utilities',
    ],
    keywords=[
    ],
    install_requires=[
        "incremental>=16.9.1",
        "icalendar",
        "Twisted==16.5.0rc1",
        "appdirs",
        "attrs",
        "cattrs",
    ],
    entry_points={
        'console_scripts': [
            'myriagon = myriagon.__main__:main'
        ]
    },
    setup_requires=[
        "incremental>=16.9.1"
    ],
    extras_require={
        ':sys_platform=="darwin"': ['pyobjc-framework-CFNetwork'],
    },

    options={
        'app': {
            'formal_name': 'Myriagon',
            'bundle': 'net.atleastfornow',
        },
        'macos': {
            'app_requires': [
                'toga-cocoa'
            ],
            'icon': 'src/myriagon/myriagon',
        },
    }
)
