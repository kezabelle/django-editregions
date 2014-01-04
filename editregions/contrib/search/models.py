# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _
from django.db.models import (Model, PositiveIntegerField, CharField,
                              BooleanField)
from django.utils.encoding import python_2_unicode_compatible, force_text
from editregions.contrib.search.text import (max_num_label, max_num_help,
                                             connection_label, connection_help,
                                             request_objects_label,
                                             request_objects_help, query_label,
                                             query_help, boost_label,
                                             boost_help, csv_validator_error)
from editregions.models import EditRegionChunk

logger = logging.getLogger(__name__)


def configured_haystack_connection(value):
    """
    Validator for making sure the provided connection is one of those
    configured in the project's settings.
    """
    connections = getattr(settings, 'HAYSTACK_CONNECTIONS', {})
    if value[:50] not in connections.keys():
        raise ValidationError('Invalid search backend provided.')


class SearchConfigBase(Model):
    max_num = PositiveIntegerField(default=3, verbose_name=max_num_label,
                                   help_text=max_num_help, validators=[
                                       MinValueValidator(0),
                                       MaxValueValidator(1000)
                                   ])
    connection = CharField(default="default", max_length=50,
                           verbose_name=connection_label,
                           help_text=connection_help, validators=[
                               configured_haystack_connection])
    request_objects = BooleanField(default=False,
                                   verbose_name=request_objects_label,
                                   help_text=request_objects_help)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class MoreLikeThis(EditRegionChunk, SearchConfigBase):
    """For mounting this chunk on the Django admin"""
    def __str__(self):
        return '{o.max_num!s} from "{o.connection!s}"'.format(o=self)

    class Meta:
        verbose_name = _("More like this")
        verbose_name_plural = _("More like this")


def csv_validator(value):
    if len(value) > 0:
        if ',' not in value and ' ' in value:
            raise ValidationError(csv_validator_error)


class SearchResultsBase(SearchConfigBase):
    #: query to perform against Haystack
    query = CharField(max_length=255, verbose_name=query_label,
                      help_text=query_help)
    #: CSV separated words to treat as higher value.
    boost = CharField(max_length=255, blank=True, verbose_name=boost_label,
                      help_text=boost_help, validators=[csv_validator])
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

    class Meta:
        abstract = True


@python_2_unicode_compatible
class SearchResults(EditRegionChunk, SearchResultsBase):
    """For mounting this chunk on the Django admin"""
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
        verbose_name = _("Search results")
        verbose_name_plural = _("Search results")
