# -*- coding: utf-8 -*-
from adminlinks.constants import POPUP_QS_VAR
from editregions.constants import (REQUEST_VAR_REGION, REQUEST_VAR_CT,
                                   REQUEST_VAR_ID)
from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR
from editregions.utils.regions import get_pretty_region_name
from editregions.utils.data import get_content_type


class EditRegionChangeList(ChangeList):

    def __init__(self, *args, **kwargs):
        """
        Stash a bunch of extra stuff on the changelist. Note that this used to
        be inlined in the EditRegionChunk ModelAdmin.
        """
        super(EditRegionChangeList, self).__init__(*args, **kwargs)
        try:
            request = kwargs['request']
        except KeyError as e:
            request = args[0]

        self.available_chunks = self.model_admin.get_changelist_filters(request.GET)
        self.formset = None
        self.region = request.GET.get(REQUEST_VAR_REGION, None)
        self.parent_content_type = request.GET.get(REQUEST_VAR_CT, None)
        self.parent_content_id = request.GET.get(REQUEST_VAR_ID, None)
        self.querydict = request.GET.copy()

        parent_obj = (get_content_type(self.parent_content_type).model_class()
                      .objects.get(pk=self.parent_content_id))
        template = parent_obj.get_live_template_names()[0]
        try:
            self.get_region_display = get_pretty_region_name(template, self.region)
        except TypeError as e:
            # unable to parse with the re module because self.region is None
            # and re expected string or buffer
            self.get_region_display = self.region

    def url_for_result(self, result):
        """
        We need to override this so that the changelists as inlines get the
        proper URLs.

        :return: the subclass (result) url
        :rtype: string
        """
        # we pass a whole bunch of data back to AdminChunkWrapper and get
        # querydict updated and get the real URL we want, not the rubbish
        # the default changelist provides.
        klass = self.model_admin.get_admin_wrapper_class()
        wrapped_obj = klass(opts=result._meta, obj=result,
                            namespace=self.model_admin.admin_site.name,
                            content_id=self.parent_content_id,
                            content_type=self.parent_content_type,
                            region=self.region)
        if not self.is_popup and POPUP_QS_VAR not in wrapped_obj.querydict:
            wrapped_obj.querydict.update({POPUP_QS_VAR: 1})
        return wrapped_obj.get_absolute_url()
