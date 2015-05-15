import sys

from setuptools import setup, find_packages


django_version = '<1.7' if sys.version_info < (2, 7) else ''



setup(
    name='django-perms',
    version='1.2.0',
    url='https://github.com/PSU-OIT-ARC/django-perms',
    author='Matt Johnson',
    author_email='mdj2@pdx.edu',
    maintainer='Wyatt Baldwin',
    maintainer_email='wyatt.baldwin@pdx.edu',
    description='Syntactic sugar for handling permission functions in views, templates and in code',
    packages=find_packages(),
    zip_safe=False,
    extras_require={
        'dev': [
            'coverage',
            'django{version}'.format(version=django_version),
            'django-nose',
            'nose',
            'six',
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
