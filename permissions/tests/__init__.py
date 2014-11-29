import django
from django.conf import settings


settings.configure(
    ALLOWED_HOSTS=[
        'testserver',
    ],
    INSTALLED_APPS=[
        'permissions',
        'permissions.tests',
    ],
    ROOT_URLCONF='permissions.tests.urls'
)


django.setup()
