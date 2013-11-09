# -*- coding: utf-8 -*-
from django.contrib import admin
from editregions.models import EditRegionChunk
from editregions.admin.modeladmins import EditRegionAdmin
from editregions.admin.inlines import EditRegionInline
admin.site.register(EditRegionChunk, EditRegionAdmin)
