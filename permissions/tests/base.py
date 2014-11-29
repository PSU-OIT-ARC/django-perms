from unittest import TestCase as BaseTestCase

from django.test import RequestFactory

from permissions import PermissionsRegistry as BasePermissionsRegistry


class PermissionsRegistry(BasePermissionsRegistry):

    def _get_model_instance(self, model, **kwargs):
        return model(**kwargs)


class Model:

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestCase(BaseTestCase):

    def setUp(self):
        self.registry = PermissionsRegistry()
        self.request_factory = RequestFactory()

