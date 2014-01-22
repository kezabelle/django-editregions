# -*- coding: utf-8 -*-
from django.test import TestCase
from editregions.contrib.search.forms import get_haystack_connections


class HaystackConnectionsFormChoicesTestCase(TestCase):
    def test_configured_connections_with_titles(self):
        settings = {
            'HAYSTACK_CONNECTIONS': {
                'default': {
                    'TITLE': 'OHMYGLOB',
                },
                'neato': {
                    'TITLE': 'xyz',
                }
            }
        }
        with self.settings(**settings):
            titled = tuple(get_haystack_connections())
            self.assertEqual(titled, (
                ('default', 'OHMYGLOB'),
                ('neato', 'xyz')
            ))

    def test_configured_connections_without_titles(self):
        settings = {
            'HAYSTACK_CONNECTIONS': {
                'default': {},
                'neato': {}
            }
        }
        with self.settings(**settings):
            titled = tuple(get_haystack_connections())
            self.assertEqual(titled, (
                ('default', 'Default'),
                ('neato', 'Neato')
            ))
