# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.db.models import Model, TextField
from editregions.models import EditRegionChunk


class TextBase(Model):
    content = TextField(blank=False, null=False)

    class Meta:
        abstract = True


class WYM(EditRegionChunk, TextBase):
    class Meta:
        verbose_name = _("HTML (WYM)")
        verbose_name_plural = _("HTML (WYM)")


class MCE(EditRegionChunk, TextBase):
    class Meta:
        verbose_name = _("HTML (TinyMCE)")
        verbose_name_plural = _("HTML (TinyMCE)")
