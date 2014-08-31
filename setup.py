#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of nose-docker.
# https://github.com/heynemann/nose-docker

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Bernardo Heynemann heynemann@gmail.com


from setuptools import setup, find_packages
from nose_docker import __version__

tests_require = [
    'mock',
    'nose',
    'coverage',
    'yanc',
    'preggy',
    'tox',
    'ipdb',
    'coveralls',
    'sphinx',
]

setup(
    name='nose-docker',
    version=__version__,
    description='nose-docker allows you to run tests inside docker containers.',
    long_description='''
nose-docker allows you to run tests inside docker containers.
''',
    keywords='',
    author='Bernardo Heynemann',
    author_email='heynemann@gmail.com',
    url='https://github.com/heynemann/nose-docker',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: Unix',
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: PyPy",
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'nose',
        'sh',
        'pyyaml',
    ],
    extras_require={
        'tests': tests_require,
    },
    entry_points={
        'nose.plugins': (
            "docker=nose_docker.plugin:NoseDockerPlugin",
        ),
    },
)
