from django.test import TestCase as BaseTestCase

from django.test import RequestFactory

from permissions import PermissionsRegistry as BasePermissionsRegistry


class PermissionsRegistry(BasePermissionsRegistry):

    def _get_user_model(self):
        return User

    def _get_model_instance(self, model, **kwargs):
        return model(**kwargs)


class Model(object):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class User(Model):

    def __init__(self, **kwargs):
        kwargs.setdefault('permissions', [])
        super(User, self).__init__(**kwargs)

    def is_anonymous(self):
        return False


class AnonymousUser(User):

    def is_anonymous(self):
        return True


class TestCase(BaseTestCase):

    def setUp(self):
        self.registry = PermissionsRegistry()
        self.request_factory = RequestFactory()

