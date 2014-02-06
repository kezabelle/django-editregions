# -*- coding: utf-8 -*-
from django.forms.models import modelform_factory
try:
    from unittest.case import TestCase, expectedFailure
except ImportError:
    from django.utils.unittest.case import TestCase, expectedFailure
from django_ace import AceWidget
from editregions.contrib.embeds.forms import JavaScriptEditorForm, StylesheetAssetForm, JavascriptAssetForm
from editregions.contrib.embeds.models import JavaScript, JavascriptAsset, StylesheetAsset


class JavaScriptEditorFormTestCase(TestCase):
    def test_init(self):
        form = modelform_factory(model=JavaScript, form=JavaScriptEditorForm,
                                 fields=['content'])()
        self.assertIsInstance(form.fields['content'].widget, AceWidget)
        self.assertEqual(form.fields['content'].widget.mode, 'javascript')
        self.assertEqual(form.fields['content'].widget.theme, 'chrome')


class StylesheetAssetFormTestCase(TestCase):
    def test_init(self):
        form = StylesheetAssetForm()
        self.assertEqual(form.only_patterns, ('editregions/embeds/*.css',))
        self.assertEqual(form.fields['local'].choices, [('', '---------')])

    def test_found_patterns(self):
        form = StylesheetAssetForm(only_patterns=('test-*.css',))
        self.assertEqual(form.only_patterns, ('test-*.css',))
        expected = sorted(list(form.fields['local'].choices))
        self.assertEqual(expected, [
            ('test-1.css', 'test-1.css'), ('test-2.css', 'test-2.css')
        ])

    @expectedFailure
    def test_skipping_fields(self):
        """I dunno why this still has local in it afterwards. hmmms."""
        form = modelform_factory(model=StylesheetAsset,
                                 form=StylesheetAssetForm, fields=[],
                                 exclude=['local'])()
        self.assertNotIn('local', form.fields)


class JavascriptAssetFormTestCase(TestCase):
    def test_init(self):
        form = JavascriptAssetForm()
        self.assertEqual(form.only_patterns, ('editregions/embeds/*.js',))
        self.assertEqual(form.fields['local'].choices, [('', '---------')])

    def test_found_patterns(self):
        form = JavascriptAssetForm(only_patterns=('test-*.js',))
        self.assertEqual(form.only_patterns, ('test-*.js',))
        expected = sorted(list(form.fields['local'].choices))
        self.assertEqual(expected, [
            ('test-1.js', 'test-1.js')
        ])

    @expectedFailure
    def test_skipping_fields(self):
        """I dunno why this still has local in it afterwards. hmmms."""
        form = modelform_factory(model=JavascriptAsset,
                                 form=JavascriptAssetForm, fields=[],
                                 exclude=['local'])()
        self.assertNotIn('local', form.fields)
