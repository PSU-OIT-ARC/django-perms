from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied

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

    def test_apply_to_class_based_view(self):

        @self.registry.register(allow_anonymous=True)
        def can_do_things(user):
            return user.can_do_things

        @self.registry.require('can_do_things')
        class View(object):

            def dispatch(self, req):
                return getattr(self, req.method.lower())(req)

            def get(self, req):
                pass

        self.assertEqual(View.dispatch.__name__, 'dispatch')

        request = self.request_factory.get('/things')
        request.user = User()

        request.user.can_do_things = True
        view = View()
        view.dispatch(request)

        request.user.can_do_things = False
        self.assertRaises(PermissionDenied, view.dispatch, request)

    def test_apply_to_class_based_view_with_model(self):

        @self.registry.register(model=Model, allow_anonymous=True)
        def can_do_stuff(user, instance):
            return user.can_do_stuff and instance is not None

        @self.registry.require('can_do_stuff')
        class View(object):

            def dispatch(self, req, model_id, *args, **kwargs):
                return getattr(self, req.method.lower())(req, model_id, *args, **kwargs)

            def get(self, req, model_id):
                return model_id

        request = self.request_factory.get('/stuff/1')
        request.user = User()

        request.user.can_do_stuff = True
        view = View()
        view.dispatch(request, 1)

        request.user.can_do_stuff = False
        self.assertRaises(PermissionDenied, view.dispatch, request, model_id=1)
