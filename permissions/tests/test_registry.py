from django.contrib.auth.models import AnonymousUser

from permissions.exc import NoSuchPermissionError, PermissionsError

from .base import Model, TestCase


class TestRegistry(TestCase):

    def test_register(self):

        @self.registry.register
        def can_do_things(user):
            pass

        self.assertTrue(hasattr(self.registry, 'can_do_things'))

        @self.registry.can_do_things
        def view(request):
            pass

    def test_register_with_args(self):

        @self.registry.register(model=Model, allow_anonymous=True)
        def can_do_things(user, instance):
            self.assertIsInstance(instance, Model)
            self.assertEqual(instance.model_id, 1)
            return user.can_do_things

        self.assertTrue(hasattr(self.registry, 'can_do_things'))

        @self.registry.require('can_do_things', field='model_id')
        def view(request, model_id):
            pass

        request = self.request_factory.get('/things/1')
        request.user = AnonymousUser()
        request.user.can_do_things = True
        view(request, 1)

    def test_cannot_use_register_as_perm_name(self):
        self.assertRaises(
            PermissionsError, self.registry.register, lambda u: None, name='register')

    def test_get_unknown_permission(self):
        with self.assertRaises(NoSuchPermissionError):
            self.registry.pants
        with self.assertRaises(NoSuchPermissionError):
            self.registry.require('pants')

    def test_bad_decoration(self):
        self.registry.register(lambda u: None, name='perm')
        self.assertRaises(PermissionsError, self.registry.perm, object())
