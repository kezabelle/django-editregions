# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.datastructures import MultiValueDictKeyError
from editregions.constants import REQUEST_VAR_REGION
from django.contrib.admin.views.main import ChangeList
from editregions.utils.regions import get_pretty_region_name

_real_edit_url = '%(admin)s:%(app)s_%(model)s_change'

class EditRegionChangeList(ChangeList):

    def __init__(self, *args, **kwargs):
        super(EditRegionChangeList, self).__init__(*args, **kwargs)
        try:
            request = kwargs['request']
        except KeyError as e:
            request = args[0]

        self.available_chunks = self.model_admin.get_changelist_filters(request.GET)
        self.formset = None
        try:
            self.region = request.GET[REQUEST_VAR_REGION]
            self.get_region_display = get_pretty_region_name(self.region)
        except MultiValueDictKeyError as e:
            self.region = None
            self.get_region_display = None

    def url_for_result(self, result):
        """
        We need to override this so that the changelists as inlines get the
        proper URLs.
        """
        bits = {
            'admin': self.model_admin.admin_site.name,
            'app': result._meta.app_label,
            'model': result._meta.module_name,
        }
        return reverse(_real_edit_url % bits, args=(result.pk,))
