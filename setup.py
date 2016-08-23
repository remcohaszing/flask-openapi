#!/usr/bin/env python3
"""
The setup script for Flask-OpenAPI.

"""
from setuptools import find_packages
from setuptools import setup


with open('README.rst') as f:
    readme = f.read()


setup(
    name='Flask-OpenAPI',
    version='0.1.0a1',
    author='Remco Haszing',
    author_email='remcohaszing@gmail.com',
    description='Generate a swagger.json handler from a Flask app',
    long_description=readme,
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'flask ~= 0.11',
        'jsonschema ~= 2.5',
        'pyyaml ~= 3.11'
    ],
    zip_safe=True)
