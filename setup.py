import sys

from setuptools import setup, find_packages


with open('VERSION') as version_fp:
    VERSION = version_fp.read().strip()


if sys.version_info[:2] < (3, 4):
    django_version = '1.8'
else:
    django_version = '1.9'


setup(
    name='django-perms',
    version=VERSION,
    url='https://github.com/PSU-OIT-ARC/django-perms',
    author='Matt Johnson',
    author_email='mdj2@pdx.edu',
    maintainer='Wyatt Baldwin',
    maintainer_email='wbaldwin@pdx.edu',
    description='Syntactic sugar for handling permission functions in views, templates, and code',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        'six>=1.10.0',
    ],
    extras_require={
        'dev': [
            'coverage',
            'django>={version},<{version}.999'.format(version=django_version),
            'flake8',
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
)
