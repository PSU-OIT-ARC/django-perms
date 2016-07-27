#!/usr/bin/env python
import django
from django.conf import settings
from django.core.management import call_command


settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    ALLOWED_HOSTS=[
        'testserver',
    ],
    INSTALLED_APPS=[
        'permissions',
        'permissions.tests',
    ],
    MIDDLEWARE_CLASSES=[],
    ROOT_URLCONF='permissions.tests.urls',
    TEST_RUNNER='django.test.runner.DiscoverRunner',
)

if django.VERSION[:2] >= (1, 7):
    from django import setup
else:
    setup = lambda: None

setup()

call_command("test")
