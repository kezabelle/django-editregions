# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db.models import (Model, PositiveIntegerField, CharField,
                              BooleanField)
from django.utils.encoding import python_2_unicode_compatible, force_text
from editregions.models import EditRegionChunk

logger = logging.getLogger(__name__)


@python_2_unicode_compatible
class SearchConfigBase(Model):
    max_num = PositiveIntegerField(default=3, validators=[
        MinValueValidator(0), MaxValueValidator(1000)])
    connection = CharField(default="default", max_length=50)
    request_objects = BooleanField(default=False)

    def __str__(self):
        return '{o.max_num!s} from "{o.connection!s}"'.format(o=self)

    class Meta:
        abstract = True


class MoreLikeThis(EditRegionChunk, SearchConfigBase):
    """For mounting this chunk on the Django admin"""
    class Meta:
        verbose_name = _("More like this")
        verbose_name_plural = _("More like this")


@python_2_unicode_compatible
class SearchResultsBase(SearchConfigBase):
    #: query to perform against Haystack
    query = CharField(max_length=255)
    #: CSV separated words to treat as higher value.
    boost = CharField(max_length=255)
    boost_amount = 1.5

    def clean(self):
        self.query = self.query.strip(' ')
        # force a trailing comma if none exists.
        if self.boost and not self.boost.endswith(','):
            self.boost = '{0},'.format(self.boost)

    def get_boosts(self):
        possible_boosts = self.boost.split(',')
        return tuple((word.strip(), self.boost_amount)
                     for word in possible_boosts
                     if word.strip())

    def __str__(self):
        if self.max_num < 1:
            return ''
        bits = ['Up to']
        if self.max_num > 0:
            bits.append(force_text(self.max_num))
        bits.append('best matches for "{0}"'.format(force_text(self.query)))
        if self.connection != 'default':
            bits.append('from "{0}"'.format(self.connection))
        return ' '.join(bits)

    class Meta:
        abstract = True


class SearchResults(EditRegionChunk, SearchResultsBase):
    """For mounting this chunk on the Django admin"""
    class Meta:
        verbose_name = _("Search results")
        verbose_name_plural = _("Search results")
