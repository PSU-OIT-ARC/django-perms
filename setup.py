#!/usr/bin/env python
from setuptools import setup

setup(
    name="django-perms",
    version='0.0.8',
    url='https://github.com/PSU-OIT-ARC/django-perms',
    author='Matt Johnson',
    author_email='mdj2@pdx.edu',
    description="Syntactic sugar for handling permission functions in views, templates and in code",
    packages=['permissions', 'permissions.templatetags'],
    zip_safe=False,
    extras_require={
        'dev': [
            'coverage',
            'django',
            'django-nose',
            'nose',
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
