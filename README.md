# Django Perms

[![Build Status](https://travis-ci.org/PSU-OIT-ARC/django-perms.svg?branch=develop)](https://travis-ci.org/PSU-OIT-ARC/django-perms)

## Install

Add `'django-perms'` to `install_requires` and/or to `requirements.txt`.

Or install it directly with pip:

    pip install django-perms

If you want to use permissions template filters, add `'permissions'` to
your project's `INSTALLED_APPS` setting.

## Usage

Create a module named `perms` in the top level of your Django project.
In this module, create a permissions registry:

    # project/package/perms.py
    from permissions import PermissionsRegistry
    permissions = PermissionsRegistry()

NOTE: You can create the permissions registry anywhere; creating it in
a module name `perms` is just a convention.

If you have some permissions that will be useful across more than one of
your Django apps, the top level `perms` module is a good place to define
them:

    @permissions.register
    def is_staff(user):
        return user.is_staff

The `is_staff` permission can be applied to a view like so:

    from package.perms import permissions

    @permissions.required('is_staff')
    def some_view_only_accessible_by_staff(request):
        pass  # Do important stuff

Note that all permissions functions *must* take a User model object as
their first argument.

App-specific permissions are typically defined in a module named `perms`
in the app's package. For example, let's say you have a `widgets` app in
your project, then you might define some permissions like so:

    # project/package/widgets/perms.py
    from package.perms import permissions

    @permissions.register
    def can_create_widget(user):
        if user.is_staff:
            return True
        num_widgets = Widget.objects.filter(created_by=user).count()
        return num_widgets <= MAX_WIDGETS

    @permissions.register(model=Widget)
    def can_edit_widget(user, widget):
        if user.is_staff:
            return True
        return user == widget.owner

    @permissions.register(model=Widget, allow_anonymous=True)
    def can_view_widget(user, widget):
        if user.is_staff:
            return True
        if user.is_anonymous():
            return widget.is_public
        return user == widget.owner

Those widget permissions can be applied to your widget views like this:

    # project/package/widgets/views.py
    from django.http import HttpResponse
    from package.perms import permissions
    from .models import Widget

    @permissions.require('can_create_widget')
    def create_widget(request):
        # Create a widget here
        return HttpResponse('Widget created')

    @permissions.require('can_edit_widget', model=Widget)
    def edit_widget(request, widget_id):
        widget = get_object_or_404(Widget, pk=widget_id)
        # Edit the widget here
        return HttpResponse('Edited %s' % widget)

    # If you want to look up widgets by a field other than the primary
    # key field, you can specify the `field` option:
    @permissions.require('can_edit_widget', field='name')
    def edit_widget(request, name):
        widget = get_object_or_404(Widget, name=name)
        return HttpResponse('Edited %s' % widget)

If you're using class-based views, you can apply a permission to a class
or to a method:

    @permissions.require('xyz')
    class MyView(View):

        # All methods require the 'xyz' permission.

        def get(request):
            pass

        def post(request):
            pass

    class MyOtherView(View):

        # Only the post method requires the 'xyz' permission. Other
        # methods are unprotected.

        def get(request):
            pass

        @permissions.require('xyz')
        def post(request):
            pass

When a permission is registered, a corresponding template filter is also
created. Given the permissions registered above, you can do this in your
templates:

    {% load permissions %}

    {% if user|is_staff %}
        Hello, staff user.
    {% endif %}

    {% if user|can_create_widget %}
        You can create widgets!
    {% endif %}

    {% if user|can_edit_widget:widget %}
        You can edit this widget!
    {% endif %}

## Permissions Registered with a Model

When registering a permission that operates on a model, it's assumed
that the second argument of any view function requiring that permission
is the model lookup field (typically a primary key):

    @permissions.register(model=Fruit)
    def can_eat_fruit(user, fruit):
        return not user.is_allergic_to(fruit)

    @permissions.require('can_eat_fruit')
    def consume_fruit_view(request, fruit_id):
        pass # Consume the fruit if allowed

The `fruit_id` passed to the `consume_fruit_view` will be used by the
permissions machinery to load a `Fruit` object, which will be passed
into the `can_eat_fruit` permission function.

When using class-based views, the `self` arg is skipped when looking for
the lookup field.

## Allowing Staff and/or Superusers Access to All Views by Default

If you find yourself writing `if user.is_staff: return True` at the top
of most or all your permission functions, you can allow staff permission
to access all views by default:

    permissions = PermissionsRegistry(is_staff=True)

If you have a view that shouldn't be accessible to staff for some
reason, you can override the default `is_staff` setting on a per-
permission basis:

    @permissions.register(is_staff=False)
    def is_superuser(user):
        return user.is_superuser

There's an analogous `is_superuser` option.

## Anonymous Users

By default, anonymous users will be redirected to the login page. In
some cases, it may make sense to give anonymous users a chance to access
certain views.

For example, if you have an `Article` model with an `is_published`
field, you may want to allow anonymous users to access articles that
have been published. To allow this, you'd define and require a
permission like this:

    # perms.py
    @permissions.register(model=Article, allow_anonymous=True)
    def can_view_article(user, article):
        if article.is_published:
            return True
        if user.is_anonymous():
            return False  # Redirect to login page
        return user == article.owner

    # views.py
    @permissions.require('can_view_article')
    def article_view(request, article_id):
        pass  # Show article

If the permission check fails for an anonymous user, they will be
redirected to the login page.
