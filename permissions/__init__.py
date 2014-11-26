import inspect
import sys
from collections import defaultdict, Callable

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .templatetags.permissions import register as template_register


__all__ = ['permission']

def permission(permission_function=None, model=None, allow_anonymous=False):
    """
    This decorator registers a permission function for use in templates, and
    creates a decorator for it, which can be used on a Django view. This
    function can be used in two ways:

    @permission
    def can_do_something(user):

    or

    @permission(model=Car)
    def can_do_something_to_a_car(user, car):

    In the latter case, when can_do_something_to_a_car is used as a Django view
    decorator, the second argument to the view function is assumed to be the PK
    of a Car model object. That object is looked up, and passed to the
    permission function.
    """
    if permission_function:
        # this is just a basic permission_function registration
        _register(permission_function, allow_anonymous=allow_anonymous)
        return permission_function
    elif model:
        # we were passed a model, so we need to decorate based on that
        def wrapper(perm_fn):
            # register the permission
            _register(perm_fn, model=model, allow_anonymous=allow_anonymous)
            return perm_fn
        return wrapper

class DecoratorContainer:
    """
    This is just a simple container for decorators. This class is
    tacked onto the module a permision function comes from. It's attributes
    are set dynamically to return the permission function as a decorator.
    """
    pass

# stores all the names of the perm functions so we know if there is a name
# collision
perm_names = set()

# this dict is used to store meta information about a permission (like which
# model class it is for). The key is the permission function __name__, and the
# value is a dict of meta information
perm_attributes = defaultdict(dict)

def _register(perm_function, model=None, allow_anonymous=False):
    # make sure this permission function isn't overriding one already defined
    if perm_function.__name__ in perm_names:
        raise ValueError("The permission function '%s' is already defined" % perm_function.__name__)

    # save the permission function
    perm_names.add(perm_function.__name__)

    # if a model class is defined for this permission function, we need to save
    # that information
    if model:
        perm_attributes[perm_function.__name__]['model'] = model

    perm_attributes[perm_function.__name__]['allow_anonymous'] = allow_anonymous

    # here is where some magic happens. We want to create a `decorators`
    # attribute on the module that defined this permission function. This
    # `decorators` attribute is a simple container for all the permission
    # functions defined in its respective module. But when the caller accesses
    # `decorators.can_do_something`, the permission function (can_do_something)
    # is turned into a decorator, which can be used on Django views.
    perm_module = sys.modules[perm_function.__module__]
    # initialize the decorator attribute if it isn't set
    if not hasattr(perm_module, 'decorators'):
        setattr(perm_module, 'decorators', DecoratorContainer())
    # create an attribute on the module.decorators attribute, named after the
    # permission function, that returns the permission function usable as a
    # decorator on a Django view function
    setattr(perm_module.decorators, perm_function.__name__, lambda *args, **kwargs: decorate(*args, perm_function=perm_function, **kwargs))

    # now add the function to our template tag filters
    # only perm functions with 1 or 2 arguments can be django filter tags 
    if len(inspect.getargspec(perm_function).args) <= 2:
        template_register.filter(perm_function.__name__, perm_function)

def decorate(*args, **kwargs):
    """
    This decorates a Django view function. When the view function is called, it
    fetches the user object out of the request (which is assumed to be the
    first parameter to the view), and runs the perm_function, to see if the
    view can be accessed.
    """
    def closure(view_function, perm_function, field="pk"):
        def wrapper(*args, **kwargs):
            # the request is always assumed to be the first argument to a Django view
            request = args[0]
            user = request.user
            perm_name = perm_function.__name__
            allow_anonymous =perm_attributes[perm_name].get("model", None)

            # anons have no permissions
            if not allow_anonymous and user.is_anonymous():
                return login_required(lambda *args, **kwargs: 1)(request)

            # are we dealing with a perm function that has an associated model class?
            model = perm_attributes[perm_name].get("model", None)
            if model is not None:
                # try to get the model_pk either as an arg, or kwarg
                try:
                    model_pk = args[1]
                except IndexError:
                    params = view_function.__code__.co_varnames
                    model_pk = kwargs[params[1]]

                model_obj = get_object_or_404(model, **{field: model_pk})
                test = perm_function(user, model_obj)
            else:
                test = perm_function(user, *args[1:], **kwargs)

            if test:
                return view_function(*args, **kwargs)
            else:
                # tack on the permission name to the request for better error
                # handling since Django doesn't give you access to the
                # PermissionDenied exception object
                request.permission_name = perm_name
                raise PermissionDenied("You need the permission %s" % perm_name)

        return wrapper

    if len(args) == 1 and isinstance(args[0], Callable):
        # the caller is using this decorator without arguments. ie @can_do_something
        return closure(*args, **kwargs)
    else:
        # the caller is using this decorator with arguments ie @can_do_something(field="foo")
        perm_function = kwargs.pop("perm_function")
        field = kwargs.pop("field")
        return lambda view_function: closure(view_function, perm_function, field)
