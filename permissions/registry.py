import logging
from collections import namedtuple
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .exc import DuplicatePermissionError, NoSuchPermissionError, PermissionsError
from .templatetags.permissions import register


log = logging.getLogger(__name__)


Entry = namedtuple('Entry', ('name', 'perm_func', 'view_decorator', 'model', 'allow_anonymous'))


class PermissionsRegistry:

    """A registry of permissions.

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

    TODO: Write more documentation.

    """

    def __init__(self):
        self.__registry = dict()

    def register(self, perm_func=None, model=None, allow_anonymous=False, name=None,
                 replace=False, _return_entry=False):
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
        if perm_func is None:
            return lambda f: self.register(f, model, allow_anonymous, name, replace, _return_entry)

        name = name if name is not None else perm_func.__name__
        if name == 'register':
            raise PermissionsError('register cannot be used as a permission name')
        elif name in self.__registry and not replace:
            raise DuplicatePermissionError(name)

        view_decorator = self.__make_view_decorator(name, perm_func, model, allow_anonymous)
        entry = Entry(name, perm_func, view_decorator, model, allow_anonymous)
        self.__registry[name] = entry

        register.filter(name, perm_func)

        log.debug('Registered permission: {0}'.format(name))
        return entry if _return_entry else perm_func

    __call__ = register

    def __getattr__(self, name):
        try:
            return self.__registry[name].view_decorator
        except KeyError:
            raise NoSuchPermissionError(name)

    def __make_view_decorator(self, perm_name, perm_func, model, allow_anonymous):
        def view_decorator(view=None, field='pk'):

            if view is None:
                return lambda view_: view_decorator(view_, field)
            elif not callable(view):
                raise PermissionsError('Bad call to permissions decorator')

            @wraps(view)
            def wrapper(request, *args, **kwargs):
                if not allow_anonymous and request.user.is_anonymous():
                    return login_required(lambda *_, **__: True)(request)

                if model is not None:
                    try:
                        field_val = args[0]
                    except IndexError:
                        local_vars = view.__code__.co_varnames
                        field_val = kwargs[local_vars[1]]
                    model_obj = get_object_or_404(model, **{field: field_val})
                    test = perm_func(request.user, model_obj)
                else:
                    test = perm_func(request.user, *args, **kwargs)

                if test:
                    return view(request, *args, **kwargs)
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
