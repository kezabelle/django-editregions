# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from CommonMark import DocParser
from CommonMark import HTMLRenderer
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.db.models import CharField
from .utils import valid_md_file
from editregions.models import EditRegionChunk


logger = logging.getLogger(__name__)


class Markdown(EditRegionChunk):
    filepath = CharField(max_length=255, verbose_name=_('filename'),
                         validators=[valid_md_file])

    @cached_property
    def content(self):
        try:
            return render_to_string(self.filepath, {})
        except TemplateDoesNotExist:
            logger.error("Markdown file has been moved or removed", exc_info=1)
            return ''

    @cached_property
    def rendered_content(self):
        if self.content:
            parsed = DocParser().parse(self.content)
            return HTMLRenderer().render(parsed)
        return ''

    class Meta:
        verbose_name = _("Markdown file")
        verbose_name_plural = _("Markdown files")
