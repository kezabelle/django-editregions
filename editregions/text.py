# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from helpfulfields.text import modified_label

chunk_v = _(u'content block')
chunk_vplural = _(u'content blocks')

position_label = _(u'position')
position_help = _(u'position in which this content appears. 1 is highest.')
render_label = _(u'renderer')
render_help = _(u'how to render this chunk.')
# datetimes_fieldset_label = _(u'dates')

region_v = _(u'region')
region_vplural = _(u'regions')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_no_obj = _(u'no object provided to the "%(tagname)s" template tag for region "%(region)s"')

#: Text for the exception raised by
#: :class:`~editregions.templatetags.editregion.EditRegionTag`. Only raised if
#: `DEBUG` is :data:`True`
ttag_not_model = _(u'"%(tagname)s" expected a Django model, got %(type)s instead')

admin_chunktype_label = _(u'type')
admin_summary_label = _(u'summary')
admin_position_label = _(u'#')
ttag_no_ancestors = _('%(obj)s must have `%(attr)s` to continue using'
                      '`%(thing)s`')
admin_modified_label = modified_label
