import sys

from .exc import NoSuchPermissionError
from .registry import PermissionsRegistry


__all__ = ['permission']


registry = None


def permission(perm_func=None, **kwargs):
    """Add a permission to the global registry.

    Optional keyword args:

        - ``model`` A model class
        - ``allow_anonymous`` Normally, anonymous users will be forced
          to log in; setting this disables that
        - ``name`` A name for the permission; this defaults to
          ``perm_func.__name__``
        - ``replace`` If a permission has already been registered with
          a given name, an error will be raised unless this is set

    This decorator registers a permission function for use in templates
    and creates a decorator for it, which can be used on a Django view.
    This function can be used in two ways::

        # some/app/perms.py
        from permissions import permission

        @permission
        def can_do_something(user):
            ...

    Or::

        @permission(model=Car)
        def can_do_something_to_a_car(user, car):
            ...

    In the latter case, when can_do_something_to_a_car is used as a
    Django view decorator, the second argument to the view function is
    assumed to be the PK of a Car model object. That object is looked
    up, and passed to the permission function.

    This function automagically adds a ``decorators`` global to the
    module where the permission function being registered is defined.
    The ``decorators`` global is a simple object container for all the
    permissions defined in the module. These decorators can be used on
    views like so::

        # some/app/views.py
        from .perms import decorators

        @decorators.can_do_stuff
        def some_view(request):
            ...

    .. note:: Permission functions *cannot* be used directly to decorate
              views. You must import and access the view decorators via
              the ``decorators`` global as shown above.

    """
    global registry
    if registry is None:
        registry = PermissionsRegistry()
    if perm_func is None:
        return lambda f: permission(f, **kwargs)
    entry = registry.register(perm_func, _return_entry=True, **kwargs)
    perm_module = sys.modules[perm_func.__module__]
    if not hasattr(perm_module, 'decorators'):
        setattr(perm_module, 'decorators', DecoratorContainer())
    setattr(perm_module.decorators, entry.name, entry.view_decorator)
    return perm_func


class DecoratorContainer:

    """This is just a simple container for decorators.

    An instance of this class is tacked onto the module a permision
    function comes from. Its attributes are set dynamically to return
    the permission function as a decorator.

    """

    def __getattr__(self, name):
        # If this gets invoked, it means the permission identified by
        # ``name`` wasn't found in the "usual" places--that is, it's not
        # an attribute of the container instance, its class, super
        # classes, etc.
        raise NoSuchPermissionError(name)
