from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from permissions import decorator, permission
from permissions.exc import DuplicatePermissionError, NoSuchPermissionError

from .base import Model, TestCase


class TestDecorator(TestCase):

    def setUp(self):
        super(TestDecorator, self).setUp()
        # Reset global registry on every run
        decorator.registry = self.registry

    def tearDown(self):
        globals().pop('decorators', None)

    def test_decoration(self):

        def can_do_stuff(user):
            return user.can_do_stuff

        original_can_do_stuff = can_do_stuff

        self.assertNotIn('decorators', globals())

        perm_func = permission(can_do_stuff, allow_anonymous=True)

        self.assertIs(original_can_do_stuff, perm_func)
        self.assertTrue(hasattr(decorator.registry, 'can_do_stuff'))
        self.assertIn('decorators', globals())

        @decorators.can_do_stuff
        def view(request):
            pass

        request = self.request_factory.get('/stuff')
        request.user = AnonymousUser()
        request.user.can_do_stuff = True
        view(request)
        request.user.can_do_stuff = False
        self.assertRaises(PermissionDenied, view, request)

    def test_decoration_with_model(self):

        @decorator.permission(model=Model, allow_anonymous=True)
        def can_do_things(user, instance):
            self.assertIsInstance(instance, Model)
            return user.can_do_things

        self.assertTrue(hasattr(decorator.registry, 'can_do_things'))

        @decorators.can_do_things
        def view(request, model_id):
            pass

        request = self.request_factory.get('/things/1')
        request.user = AnonymousUser()
        request.user.can_do_things = True
        view(request, model_id='1')

    def test_register_duplicate(self):
        decorator.permission(lambda u: None, name='perm')
        self.assertRaises(
            DuplicatePermissionError, decorator.permission, lambda u: None, name='perm')

    def test_unknown_permission(self):
        decorator.permission(lambda u: None, name='perm')
        with self.assertRaises(NoSuchPermissionError):
            decorators.huh(lambda r: None)
