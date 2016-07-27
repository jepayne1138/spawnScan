#!/usr/bin/env python

import os
from io import open
from setuptools import setup, find_packages

setup_dir = os.path.dirname(os.path.realpath(__file__))

# Get the long description from the README file
with open(os.path.join(setup_dir, 'README.rst'), encoding='utf-8') as readme:
    long_description = readme.read()

setup(
    name='spawnScan',
    author='TBTerra',
    description='A simple and fast spawnPoint finder for pokemon go',
    long_description=long_description,
    version='0.1.1',
    url='https://github.com/TBTerra/spawnScan',
    packages=find_packages(),
    install_requires=[
        'geojson'
    ],
    dependency_links=[
        'https://github.com/tejado/pgoapi/tarball/v1.1.0#egg=pgoapi-v1.1.0'
    ],
    entry_points={
        'console_scripts': [
            'spawnscan = spawnscan.console:main',
        ]
    }
)
