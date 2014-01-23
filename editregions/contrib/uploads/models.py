# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.core.files.images import get_image_dimensions
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.db.models import Model, FileField, CharField
try:
    from django.utils.image import Image
except ImportError:  # pragma: no cover ... 1.4?
    try:
        from PIL import Image
    except ImportError:
        import Image
from editregions.models import EditRegionChunk


class FileBase(Model):
    data = FileField(upload_to='editregions/files', verbose_name=_("file"))
    title = CharField(max_length=255, null=True, blank=True,
                      verbose_name=_("title"), help_text=_("Optional text to "
                                                           "display instead of "
                                                           "the filename"))

    def get_filename(self):
        return os.path.basename(self.data.name)

    def get_filetype(self):
        return os.path.splitext(self.data.path)[1][1:].lower()

    def is_image(self):
        # taken from ImageField
        try:
            Image.open(self.data).verify()
            return True
        except Exception:
            return False

    def _get_dimensions(self):
        if self.is_image():
            return get_image_dimensions(self.data)
        return None

    @cached_property
    def dimensions(self):
        return self._get_dimensions()

    def dimensions_as_str(self):
        try:
            return '%dx%d' % self.dimensions
        except TypeError:
            # wasn't an image after all ...
            return ''

    class Meta:
        abstract = True


@python_2_unicode_compatible
class File(EditRegionChunk, FileBase):

    def __str__(self):
        if self.title:
            return self.title
        elif self.data:
            return self.get_filename()
        return 'No file or title'

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
