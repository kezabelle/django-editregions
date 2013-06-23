# -*- coding: utf-8 -*-
from django.conf import settings
from appconf import AppConf


REQUEST_VAR_REGION = 'region'
REQUEST_VAR_CT = 'content_type'
REQUEST_VAR_ID = 'content_id'


class EditRegionsConf(AppConf):
    #: Configuration dictionary for all regions.
    #: May be an empty dictionary, or a complex data structure.
    #:
    #: The **Keys** represent **region groups**, which is how unique combinations
    #: of regions may be exposed via the admin.
    #:
    #: The **Values** take the form of a 3-tuple:
    #:
    #:      * **0** is the region name for use in code (templates, etc)
    #:      * **1** is the display name of the region, typically wrapped in
    #:        a call to `gettext`
    #:      * **2** is a dictionary of available chunk types and the limits
    #:        imposed on them. :data:`None` is a special value indicating
    #:        no limit.
    EDIT_REGIONS = {}

    class Meta:
        prefix = ''
