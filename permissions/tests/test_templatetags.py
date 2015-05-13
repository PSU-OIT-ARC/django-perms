from django.test import TestCase

from django.template import Context, Template

from permissions import PermissionsRegistry

from .base import Model, User


def can_do(user):
    return 'can_do' in user.permissions


def can_do_with_model(user, instance):
    return 'can_do_with_model' in user.permissions


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
        user = User(permissions=['can_do'])
        context = Context({'user': user})
        result = self.template.render(context)
        self.assertIn('can_do', result)

    def test_cannot_do(self):
        user = User()
        context = Context({'user': user})
        result = self.template.render(context)
        self.assertNotIn('can_do', result)

    def test_can_do_with_model(self):
        user = User(permissions=['can_do_with_model'])
        context = Context({'user': user, 'instance': Model()})
        result = self.template.render(context)
        self.assertIn('can_do_with_model', result)

    def test_cannot_do_with_model(self):
        user = User()
        context = Context({'user': user, 'instance': Model()})
        result = self.template.render(context)
        self.assertNotIn('can_do_with_model', result)
