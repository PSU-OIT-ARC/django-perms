from django.test import TestCase

from django.template import Context, Template

from permissions import PermissionsRegistry


class Model:

    pass


def can_do(user):
    return user is not None


def can_do_with_model(user, instance):
    return None not in (user, instance)


class TestTemplateTags(TestCase):

    def setUp(self):
        self.registry = PermissionsRegistry()
        self.registry.register(can_do)
        self.registry.register(can_do_with_model, model=Model)
        self.template = Template(
            '{% load permissions %}'
            '{% if user|can_do %}can_do{% endif %}'
            '{% if user|can_do_with_model:instance %}can_do_with_model{% endif %}'
        )

    def test_can_do(self):
        context = Context({'user': object(), 'instance': None})
        result = self.template.render(context)
        self.assertIn('can_do', result)

    def test_cannot_do(self):
        context = Context({'user': None, 'instance': None})
        result = self.template.render(context)
        self.assertNotIn('can_do', result)

    def test_can_do_with_model(self):
        context = Context({'user': object(), 'instance': object()})
        result = self.template.render(context)
        self.assertIn('can_do_with_model', result)

    def test_cannot_do_with_model(self):
        context = Context({'user': None, 'instance': object()})
        result = self.template.render(context)
        self.assertNotIn('can_do_with_model', result)
