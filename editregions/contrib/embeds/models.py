# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from hashlib import sha1 as cachehash
from django.core.cache import cache
from django.db.models.base import Model
from django.db.models.fields import URLField, PositiveIntegerField, CharField
from django.utils.encoding import python_2_unicode_compatible
from feedparser import parse
from model_utils import Choices
from editregions.models import EditRegionChunk
from editregions.contrib.embeds.text import (iframe_vname_plural, iframe_vname,
                                             iframe_name_label, iframe_name_help,  # noqa
                                             iframe_url_label, iframe_dimensions_help,  # noqa
                                             iframe_url_help, feed_url_label,
                                             feed_url_help, feed_vname,
                                             feed_vname_plural, feed_cache_day,
                                             feed_cache_hday, feed_cache_qday,
                                             feed_cache_hour, feed_cache_for_label,  # noqa
                                             feed_cache_for_help)

logger = logging.getLogger(__name__)


class IframeBase(Model):
    """
    An abstract set of model fields for mixing into other models.

    Note: the maximum length for the URLField is set to 2048,
    because that is the limit in older IE versions for GET requests (including
    querystrings).
    It is possibly still true.
    """
    url = URLField(max_length=2048, blank=False, null=False,
                   verbose_name=iframe_url_label, help_text=iframe_url_help)
    # optional fields.
    # These may get used, but it depends on the template author to do so.
    height = PositiveIntegerField(default=None, blank=True, null=True,
                                  help_text=iframe_dimensions_help)
    width = PositiveIntegerField(default=None, blank=True, null=True,
                                 help_text=iframe_dimensions_help)
    name = CharField(max_length=255, blank=True, null=False,
                     verbose_name=iframe_name_label, help_text=iframe_name_help)

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Iframe(EditRegionChunk, IframeBase):
    """For mounting this chunk on the Django admin"""

    def get_name(self):
        return self.name or u'chunk-iframe-%d' % self.pk

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = iframe_vname
        verbose_name_plural = iframe_vname_plural


class FeedBase(Model):
    max_num = PositiveIntegerField(default=5, verbose_name='', help_text='')
    url = URLField(max_length=2048, blank=False, null=False,
                   verbose_name=feed_url_label, help_text=feed_url_help)

    class Meta:
        abstract = True


class Feed(EditRegionChunk, FeedBase):
    FEED_CACHE_DURATIONS = Choices(
        (86400, 'a_day', feed_cache_day),
        (43200, 'half_day', feed_cache_hday),
        (24600, 'quarter_day', feed_cache_qday),
        (3600, 'an_hour', feed_cache_hour),
    )
    cache_for = PositiveIntegerField(choices=FEED_CACHE_DURATIONS,
                                     default=FEED_CACHE_DURATIONS.a_day,
                                     verbose_name=feed_cache_for_label,
                                     help_text=feed_cache_for_help)

    def __unicode__(self):
        return self.url

    def get_from_cache(self):
        feed_key = 'feed_{0}'.format(cachehash(self.url).hexdigest())
        feed = cache.get(feed_key, None)
        if feed is None:
            logger.debug('Feed not in cache, fetching... {0}'.format(self.url))
            feed = parse(self.url)
            cache.set(feed_key, feed, self.cache_for)
        return feed

    class Meta:
        verbose_name = feed_vname
        verbose_name_plural = feed_vname_plural
