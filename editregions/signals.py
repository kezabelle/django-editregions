# -*- coding: utf-8 -*-
from django.dispatch import Signal

# fired for moving from region 'x' to region 'y' (regardless of position)
different_region_move_completed = Signal(providing_args=('instance',
                                                         'reflowed_previous',
                                                         'reflowed_current'))

# fired for moving from position '1' to '2' within region 'x'
same_region_move_completed = Signal(providing_args=('instance', 'reflowed'))

# fired after either of the above events.
move_completed = Signal(providing_args=('instance', 'reflowed'))
