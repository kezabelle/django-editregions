# -*- coding: utf-8 -*-
import logging
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.db.models import CharField
from .settings import DEFAULT_META_NAMES
from editregions.models import EditRegionChunk


logger = logging.getLogger(__name__)


def get_meta_name_choices():
    names = getattr(settings, 'EDITREGIONS_HTMLMETA_NAMES', None)
    if names is None:
        return DEFAULT_META_NAMES


class MetaElement(EditRegionChunk):
    name = CharField(max_length=50, choices=get_meta_name_choices())
    content = CharField(max_length=255)

    def clean(self):
        super(MetaElement, self).clean()
        if self.is_title() and len(self.content) > 55:
            logger.warning("HTML titles should not be longer than 55 characters")  # noqa

    def is_title(self):
        return self.name == 'title'

    def render_title(self):
        return '<title>{content!s}</title>'.format(self.content)

    def render_meta(self):
        return '<meta name="{name!s}" content="{content!s}">'.format(
            name=self.name, content=self.content)

    class Meta:
        verbose_name = _("Meta tag")
        verbose_name_plural = _("Meta tags")
