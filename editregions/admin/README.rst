editregions.admin
=================

``modeladmins.py`` contains:

  * ``EditRegionAdmin``, the mounted but hidden ``ModelAdmin`` for
    ``EditRegionChunk`` objects.
  * ``ChunkAdmin``, which should be used for mounting subclasses of
    ``EditRegionChunk`` into the admin.

``inlines.py`` contains:

  * ``EditRegionInline`` which is our fake inline for putting editregions into
    any ``ModelAdmin`` instance.

Everything else should probably be considered private API.
