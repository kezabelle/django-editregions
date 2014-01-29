# -*- coding: utf-8 -*-
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from tinymce.widgets import TinyMCE
from wymeditor.widgets import WYMEditorArea
from editregions.contrib.text.forms import WYMEditorForm, MCEEditorForm


class WYMEditorFormTestCase(TestCase):
    def test_init(self):
        form = WYMEditorForm()
        self.assertIsInstance(form.fields['content'].widget, WYMEditorArea)


class MCEEditorFormTestCase(TestCase):
    def test_init(self):
        form = MCEEditorForm()
        self.assertIsInstance(form.fields['content'].widget, TinyMCE)
