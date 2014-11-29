from unittest import TestCase

from permissions import PermissionsRegistry
from permissions.exc import NoSuchPermissionError, PermissionsError


class TestRegistry(TestCase):

    def setUp(self):
        self.registry = PermissionsRegistry()

    def test_register(self):

        @self.registry.register
        def can_do_things(user):
            pass

        self.assertTrue(hasattr(self.registry, 'can_do_things'))

        @self.registry.can_do_things
        def view(request):
            pass

    def test_register_with_args(self):

        class Pants:

            pass

        @self.registry.register(model=Pants, allow_anonymous=True)
        def can_do_things(user, pants):
            pass

        self.assertTrue(hasattr(self.registry, 'can_do_things'))

        @self.registry.can_do_things(field='pants_id')
        def view(request, pants_id):
            pass

    def test_cannot_use_register_as_perm_name(self):
        self.assertRaises(
            PermissionsError, self.registry.register, lambda u: None, name='register')

    def test_get_unknown_permission(self):
        with self.assertRaises(NoSuchPermissionError):
            self.registry.pants


    def test_bad_decoration(self):
        self.registry.register(lambda u: None, name='perm')
        self.assertRaises(PermissionsError, self.registry.perm, object())
