from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from ..exc import PermissionsError
from ..meta import PermissionsMeta

from .base import Model, TestCase


class TestMeta(TestCase):

    def setUp(self):
        super(TestMeta, self).setUp()

        @self.registry.register(model=Model)
        def can_view(user, instance):
            return user.can_view

    def _do_view_tests(self, View):
        view = View()
        request = self.request_factory.get('/things/1')
        request.user = User()
        request.user.can_view = False
        self.assertRaises(PermissionDenied, view.get, request, 1)
        request.user.can_view = True
        view.get(request, 1)

    def test_registry_metaclass(self):

        class View(object, metaclass=self.registry.metaclass):

            permissions = {
                'get': 'can_view',
            }

            def get(self, request, model_id):
                pass

        self._do_view_tests(View)

    def test_specify_permissions_registry_on_view_class(self):

        class View(object, metaclass=PermissionsMeta):

            permissions_registry = self.registry

            permissions = {
                'get': 'can_view',
            }

            def get(self, request, model_id):
                pass

        self._do_view_tests(View)

    def test_no_registry(self):

        with self.assertRaises(PermissionsError):
            class View(object, metaclass=PermissionsMeta):

                permissions = {
                    'get': 'can_view',
                }

                def get(self, request, model_id):
                    pass
