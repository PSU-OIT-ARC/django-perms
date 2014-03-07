# Django Perms

## Install

`pip install django-perms`

Add 'permissions' to your installed apps.

## Usage

Consider the following functions (in widgets/perms.py):

    def can_create_widget(user):
        if user.is_admin:
            return True

        if Widget.objects.filter(created_by=user).count() <= MAX_WIDGETS_PER_USER:
            return True

    def can_edit_widget(user, widget):
        if user.is_admin:
            return True

        if user.pk == widget.created_by_id:
            return True

All permissions functions *must* take a User model object as a first argument. The latter permission function takes a second argument, some kind of object to check permissions against.

To register these as permission functions, use the `@permission` decorator:

    ...
    from permissions import permission

    @permission
    def can_create_widget(user):
        ...

    @permission(model=Widget)
    def can_edit_widget(user, widget):
        ...

Permission functions that take a single argument (the user object), can use the simple `@permission` decorator. Permission functions that take a second argument *must* specify the model class that the second argument to the permission function is expected to be.

Now in widgets/views.py, you can do something like:

    # the `decorators` attribute on the widgets/perms.py module was added at runtime by the permissions app
    from .perms import decorators

    @decorators.can_create_widget
    def create(request):
        return HttpResponse("Create a widget!")

    @decorators.can_edit_widget
    def edit(request, widget_id):
        widget = get_object_or_404(Widget, pk=widget_id)
        return HttpResponse("You can edit %s" % str(widget))

In your templates, you can do:

    {% load permissions %}

    {% if user|can_create_widget %}
        You can create widgets!
    {% endif %}

    {% if user|can_edit_widget:widget_object %}
        You can edit this widget!
    {% endif %}


## How it Works

When you register a permission function using `@permission`, a Django template filter is created based on the function. It also creates a simple decorator, which can be used on a Django view. The decorator takes the `request.user` object, and passes it to the permission function. If the permission function returns True, the Django view is loaded. Otherwise a PermissionDenied exception is raised.

In the more complicated `@permission(model=Widget)` case, a Django template filter is created. It also creates a decorator which can be used on a Django view. **This decorator assumes the second argument to the Django view is the PK of the model class you specified.** It then performs a model lookup using that PK, and passes the `request.user` object, and the model object to the permission function. If the model object DoesNotExist, a 404 is raised.

When a PermissionDenied error is raised, the request object gets a `permission_name` attribute that is a string of the permission function's name.

Anonymous users will be sent to the login page (the permission decorators only work on logged in users).
