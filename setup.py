#!/usr/bin/env python

import os
from setuptools import setup, find_packages
from pip.req import parse_requirements

setup_dir = os.path.dirname(os.path.realpath(__file__))
path_req = os.path.join(setup_dir, 'requirements.txt')
install_reqs = parse_requirements(path_req, session=False)

# Get the long description from the README file
with open(os.path.join(setup_dir, 'README.md'), encoding='utf-8') as readme:
    long_description = readme.read()

reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='spawnScan',
    author='TBTerra',
    description='A simple and fast spawnPoint finder for pokemon go',
    long_description=long_description,
    version='0.1.1',
    url='https://github.com/TBTerra/spawnScan',
    packages=find_packages(),
    install_requires=reqs
)
