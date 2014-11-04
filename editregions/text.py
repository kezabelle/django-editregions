# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _

chunk_v = _('content block')
chunk_vplural = _('content blocks')

position_label = _('position')
position_help = _('position in which this content appears. 1 is highest.')
render_label = _('renderer')
render_help = _('how to render this chunk.')
# datetimes_fieldset_label = _('dates')

region_v = _('region')
region_vplural = _('regions')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_no_obj = _('no object provided to the "%(tagname)s" template tag for'
                'region "%(region)s"')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_not_model = _('"%(tagname)s" expected a Django model, got %(type)s'
                   'instead')

admin_chunktype_label = _('type')
admin_summary_label = _('summary')
admin_position_label = _('#')
admin_modified_label = _(u'last modified')

validate_region_name_error = _('Enter a valid region name consisting of '
                               'letters, numbers, underscores and hyphens.')

region_name_startswith = _('Region names may not begin with "_"')
region_name_endswith = _('Region names may not end with "_"')
