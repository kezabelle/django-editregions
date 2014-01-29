# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from hashlib import sha1
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models.base import Model
from django.db.models.fields import (URLField, PositiveIntegerField, CharField,
                                     TextField)
from django.template.defaultfilters import slugify
from django.utils.encoding import (python_2_unicode_compatible, force_text,
                                   force_bytes)
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
                                             feed_cache_for_help, js_vname,
                                             js_vname_plural)
from editregions.contrib.embeds.signals import (feed_request_started,
                                                feed_request_finished)

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

    def get_safe_name(self):
        return slugify(self.get_name())

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


@python_2_unicode_compatible
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

    def __str__(self):
        return self.url

    def get_from_cache(self):
        feed_key = 'feed_{0}'.format(sha1(force_bytes(self.url)).hexdigest())
        feed = cache.get(feed_key, None)
        if feed is None:
            logger.debug('Feed not in cache, fetching... {0}'.format(self.url))
            feed_request_started.send(sender=self, instance=self)
            feed = parse(self.url)
            feed_request_finished.send(sender=self, instance=self, feed=feed)
            cache.set(feed_key, feed, self.cache_for)
        return feed

    class Meta:
        verbose_name = feed_vname
        verbose_name_plural = feed_vname_plural


class JavaScriptBase(Model):
    content = TextField(blank=False, null=False)

    class Meta:
        abstract = True


class JavaScript(EditRegionChunk, JavaScriptBase):
    class Meta:
        verbose_name = js_vname
        verbose_name_plural = js_vname_plural


class AssetBase(Model):
    local = CharField(max_length=2048, null=False, blank=True)
    external = CharField(max_length=2048, null=False, blank=True)

    def clean(self):
        super(AssetBase, self).clean()
        if self.local and self.external:
            raise ValidationError("Please choose either a local file or an "
                                  "external URL")
        if not self.local and not self.external:
            raise ValidationError("Please provide a local file or an "
                                  "external URL")

    def external_scheme_relative(self):
        requirements = (
            self.external.startswith('http'),
            '://' in self.external,
        )
        if self.external and all(requirements):
            self.external = '//{0}'.format(self.external.split('://')[1])
        return self.external

    class Meta:
        abstract = True


@python_2_unicode_compatible
class JavascriptAsset(EditRegionChunk, AssetBase):
    def __str__(self):
        if self.local:
            return 'Local file: {0}'.format(self.local)
        if self.external:
            return 'External URL: {0}'.format(self.external)
        return 'None'

    class Meta:
        verbose_name = "javascript file"
        verbose_name_plural = "javascript files"


@python_2_unicode_compatible
class StylesheetAsset(EditRegionChunk, AssetBase):
    def __str__(self):
        if self.local:
            return 'Local file: {0}'.format(self.local)
        if self.external:
            return 'External URL: {0}'.format(self.external)
        return 'None'

    class Meta:
        verbose_name = "stylesheet file"
        verbose_name_plural = "stylesheet files"
