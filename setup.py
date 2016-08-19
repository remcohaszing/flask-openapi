#!/usr/bin/env python3
from setuptools import find_packages
from setuptools import setup


setup(
    name='Flask-OpenAPI',
    version='0.0.1',
    author='Remco Haszing',
    author_email='remcohaszing@gmail.com',
    packages=find_packages(),
    install_requires=[
        'flask ~= 0.11.0'
    ],
    zip_safe=True)
