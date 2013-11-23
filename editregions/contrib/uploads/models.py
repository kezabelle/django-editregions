# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from django.db.models import Model, FileField, CharField
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
        return os.path.splitext(self.data.name)[1][1:]

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
