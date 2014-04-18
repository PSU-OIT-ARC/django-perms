#!/usr/bin/env python
from setuptools import setup

setup(
    name="django-perms",
    version='0.0.6',
    url='https://github.com/PSU-OIT-ARC/django-perms',
    author='Matt Johnson',
    author_email='mdj2@pdx.edu',
    description="Syntactic sugar for handling permission functions in views, templates and in code",
    packages=['permissions', 'permissions.templatetags'],
    zip_safe=False,
    classifiers=[
        'Framework :: Django',
    ],
)
