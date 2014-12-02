import inspect
import logging
from collections import namedtuple
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.shortcuts import get_object_or_404

from .exc import DuplicatePermissionError, NoSuchPermissionError, PermissionsError
from .templatetags.permissions import register


log = logging.getLogger(__name__)


Entry = namedtuple('Entry', (
    'name', 'perm_func', 'view_decorator', 'model', 'allow_staff', 'allow_superuser',
    'allow_anonymous'
))


NO_VALUE = object()


class PermissionsRegistry:

    """A registry of permissions.

    Args:

        - allow_staff: Allow staff to access all views by default. If
          this is set and the user is a staff member, the permission
          logic will not be invoked.

        - allow_superuser: Allow superusers to access all views by
          default. If this is set and the user is a superuser, the
          permission logic will not be invoked.

        - allow_anonymous: Allow anonymous users. Note: this is
          different from the two options above in that it doesn't
          grant permission by default but instead just gives anonymous
          users a chance to access a view--the permission logic is still
          invoked.

        All of these options can be overridden on a per-permission
        basis by passing the corresponding argument to :meth:`register`.

    Create a registry somewhere in your project::

        # my/project/perms.py
        from permissions import PermissionsRegistry

        permissions = PermissionsRegistry()

    Then register permissions for an app like so::

        # my/project/app/perms.py
        from my.project.perms import permissions

        @permissions.register
        def can_do_stuff(user):
            ...

        @permissions.register(model=MyModel)
        def can_do_things(user, instance):
            ...

    Then require permissions on views like this::

        # my/project/app/views.py
        from my.project.perms import permissions

        @permissions.require('can_do_stuff')
        def my_view(request):
            ...

    TODO: Write more documentation.

    """

    def __init__(self, allow_staff=False, allow_superuser=False, allow_anonymous=False):
        self._registry = dict()
        self._allow_staff = allow_staff
        self._allow_superuser = allow_superuser
        self._allow_anonymous = allow_anonymous

    def register(self, perm_func=None, model=None, allow_staff=None, allow_superuser=None,
                 allow_anonymous=None, name=None, replace=False, _return_entry=False):
        """Register permission function & return the original function.

        This is typically used as a decorator::

            permissions = PermissionsRegistry()
            @permissions.register
            def can_do_something(user):
                ...

        For internal use only: you can pass ``_return_entry=True`` to
        have the registry :class:`.Entry` returned instead of
        ``perm_func``.

        """
        allow_staff = self._allow_staff if allow_staff is None else allow_staff
        allow_superuser = self._allow_superuser if allow_superuser is None else allow_superuser
        allow_anonymous = self._allow_anonymous if allow_anonymous is None else allow_anonymous

        if perm_func is None:
            return (
                lambda perm_func_:
                    self.register(
                        perm_func_, model, allow_staff, allow_superuser, allow_anonymous, name,
                        replace, _return_entry)
            )

        name = name if name is not None else perm_func.__name__
        if name == 'register':
            raise PermissionsError('register cannot be used as a permission name')
        elif name in self._registry and not replace:
            raise DuplicatePermissionError(name)

        view_decorator = self._make_view_decorator(
            name, perm_func, model, allow_staff, allow_superuser, allow_anonymous)
        entry = Entry(
            name, perm_func, view_decorator, model, allow_staff, allow_superuser, allow_anonymous)
        self._registry[name] = entry

        @wraps(perm_func)
        def filter_func(user, instance=NO_VALUE):
            return (
                allow_staff and user.is_staff or
                allow_superuser and user.is_superuser or
                perm_func(user) if instance is NO_VALUE else perm_func(user, instance)
            )

        register.filter(name, filter_func)

        log.debug('Registered permission: {0}'.format(name))
        return entry if _return_entry else perm_func

    __call__ = register

    def require(self, perm_name, **kwargs):
        """Use as a decorator on a view to require a permission.

        Optional args:

            - ``field`` The name of the model field to use for lookup
              (this is only relevant when requiring a permission that
              was registered with ``model=SomeModelClass``)

        Examples::

            @registry.require('can_do_stuff')
            def view(request):
                ...

            @registry.require('can_do_stuff_with_model', field='alt_id')
            def view_model(request, model_id):
                ...

        """
        try:
            view_decorator = self._registry[perm_name].view_decorator
        except KeyError:
            raise NoSuchPermissionError(perm_name)
        return view_decorator(**kwargs) if kwargs else view_decorator

    def __getattr__(self, name):
        return self.require(name)

    def _make_view_decorator(self, perm_name, perm_func, model, allow_staff, allow_superuser,
                             allow_anonymous):

        # Putting this import here is a hack-around for testing. Merely
        # importing login_required causes django.conf.settings to be
        # accessed in some other module, which causes
        # ImproperlyConfigured to be raised during the import phase of
        # test discovery.
        from django.contrib.auth.decorators import login_required

        def view_decorator(view=None, field='pk'):

            if view is None:
                return lambda view_: view_decorator(view_, field)
            elif not callable(view):
                raise PermissionsError('Bad call to permissions decorator')

            # When a permission is applied to a class, which is presumed
            # to be a class-based view, instead apply the permission to
            # the class's dispatch() method. This will effectively
            # require the permission for all of the class's view methods:
            # get(), post(), etc. The class is returned as is.
            #
            # @permissions.require('can_do_stuff')
            # class MyView(View):
            #
            #     def get(request):
            #         ...
            #
            # In this example, the call to require() returns this
            # instance of view_decorator. When view_decorator is
            # called (via @), MyView is passed in. When the lines
            # below are reached, we decorate MyView.dispatch() and
            # then return MyView.
            if isinstance(view, type):
                view.dispatch = view_decorator(view.dispatch, field)
                return view

            # This contains the names of all of the view's args
            # (positional and keyword). This is used to find the field
            # value for permissions that operate on a model.
            view_arg_names = inspect.getargspec(view).args

            @wraps(view)
            def wrapper(*args, **kwargs):
                # The following allows permissions decorators to work on
                # view functions and class-based view methods. Either
                # the first or the second arg must be the request. In
                # the latter case, the first arg will be an instance of
                # a class-based view).
                if isinstance(args[0], HttpRequest):
                    request_index = 0
                elif isinstance(args[1], HttpRequest):
                    request_index = 1
                else:
                    raise PermissionsError('Could not find request in args passed to view')

                request = args[request_index]
                user = request.user
                args_index = request_index + 1
                remaining_args = args[args_index:]  # Args after request

                if not allow_anonymous and user.is_anonymous():
                    return login_required(lambda *_, **__: True)(request)

                if model is not None:
                    if remaining_args:
                        # Assume the 1st positional arg after request
                        # passed to the view contains the field value...
                        field_val = remaining_args[0]
                    else:
                        # ...unless there are no positional args after
                        # the request; in that case, use the value of
                        # the first keyword arg.
                        field_val = kwargs[view_arg_names[args_index]]
                    test = lambda: perm_func(
                        user, self._get_model_instance(model, **{field: field_val}))
                else:
                    test = lambda: perm_func(user, *remaining_args, **kwargs)

                has_permission = (
                    allow_staff and user.is_staff or
                    allow_superuser and user.is_superuser or
                    test()
                )

                if has_permission:
                    return view(*args, **kwargs)
                else:
                    # Tack on the permission name to the request for
                    # better error handling since Django doesn't
                    # give you access to the PermissionDenied
                    # exception object.
                    request.permission_name = perm_name
                    raise PermissionDenied(
                        'The "{0}" permission is required to access this resource'
                        .format(perm_name))

            return wrapper
        return view_decorator

    def _get_model_instance(self, model, **kwargs):
        return get_object_or_404(model, **kwargs)
