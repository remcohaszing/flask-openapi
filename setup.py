#!/usr/bin/env python3
from setuptools import find_packages
from setuptools import setup


setup(
    name='Flask-OpenAPI',
    version='0.1.0.alpha0',
    author='Remco Haszing',
    author_email='remcohaszing@gmail.com',
    packages=find_packages(),
    install_requires=[
        'flask ~= 0.11.0',
        'jsonschema ~= 2.5.1'
    ],
    zip_safe=True)
