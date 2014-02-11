=======================
Writing your own chunks
=======================

While there are some simple chunk types available *out of the box*, far and
away the most useful aspect of ``django-editregions`` is the easy addition
of new chunks, or changes to the rendering of existing ones.

Making a new chunk
------------------

Let's briefly run through creating ``CustomChunk``, our spurious chunk type.

Making the model
^^^^^^^^^^^^^^^^

First, create a new model, representing the data you wish to be saved by
content administrators. To be a valid chunk, your model must subclass
``EditRegionChunk``::

    from django.db import models
    from editregions.models import EditRegionChunk

    class CustomChunk(EditRegionChunk):
        field = models.CharField()
        another_field = models.PositiveIntegerField()
        last_field = models.DateTimeField()

By inheriting from ``EditRegionChunk``, a number of other fields are created,
among them ``created`` and ``modified``, for keeping track of changes.

.. note:: Don't forget to either ``python manage.py syncdb``, or if you're
          using South, ``python manage.py schemamigration <app> --auto <desc> && python manage.py migrate <app>`` before trying to move on!

Making the admin
^^^^^^^^^^^^^^^^

Like the model, the ``ModelAdmin`` for our ``CustomChunk`` needs to be
configured in a certain way. As before, there's a class (``ChunkAdmin``)
which may be mixed in to provide the required functionality
with the least-developer effort::

    from django.contrib import admin
    from editregions.admin.modeladmins import ChunkAdmin
    from .models import CustomChunk

    class CustomChunkAdmin(ChunkAdmin, admin.ModelAdmin):
        pass

    admin.site.register(CustomChunk, CustomChunkAdmin)

.. note:: The ``ChunkAdmin`` should always be to the left of the ``ModelAdmin``
          in the class declaration. It just should, trust me on this.

Setting up for rendering  our chunk
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Our ``CustomChunkAdmin`` needs to be augmented with a couple of methods to
allow the the application to render them in various ways:

  * ``render_into_region`` is used by the ``{% editregion %}`` template tag to
    output a string into a Django template.
  * ``render_into_summary`` is used by the admin to display human readable blurbs
    for the chunk's contents.
  * ``render_into_mediagroup`` is used by the ``{% editregion_top %}`` and
    ``{% editregion_bottom %}`` template tags to output a chunk's required media
    in a Django template.

Of those three methods, only ``render_into_region`` is *required*.

Example ``render_into_region``
******************************
Should return a string, or ``None`` if the chunk should not output anything::

    from django.contrib import admin
    from editregions.admin.modeladmins import ChunkAdmin

    class CustomChunkAdmin(ChunkAdmin, admin.ModelAdmin):
        def render_into_region(self, obj, context, extra, **kwargs):
            context.update({'test': 1})
            templates = ['app/customchunk_{0}.html'.format(obj.pk),
                         'app/customchunk.html']
            return render_to_string(templates, context_instance=context)

Example ``render_into_summary``
*******************************

which should return a string::

    from django.contrib import admin
    from editregions.admin.modeladmins import ChunkAdmin

    class CustomChunkAdmin(ChunkAdmin, admin.ModelAdmin):
        def render_into_summary(self, obj, context, extra, **kwargs):
            return unicode(obj)

Example ``render_into_mediagroup``
**********************************

Defines assets (CSS, Javascript) required for rendering the chunk; if defined,
``render_into_mediagroup`` should return a dictionary containing any of
the keys ``top``, ``bottom``, the values of which should be iterables
such as a ``list`` or a ``tuple``::

    from django.contrib import admin
    from editregions.admin.modeladmins import ChunkAdmin

    class CustomChunkAdmin(ChunkAdmin, admin.ModelAdmin):
        def render_into_mediagroup(self, obj, context, extra, **kwargs):
            return {
                'top': [
                    '<link rel="stylesheet" type="text/css" href="a.css">',
                    '<link rel="stylesheet" type="text/css" href="b.css">',
                ],
                'bottom': [
                    '<script type="text/javascript">var x = 1;</script>',
                ]
            }

That's it. Pretty much just standard Django Models and Modeladmins, really.

Changing an existing renderer
-----------------------------

If there's already a chunk Model which stores the data you want, the
simplest solution is to replace the ModelAdmin which renders it, like below,
where we're replacing the admin assigned for ``TheChunk`` with our
customised version::

    from django.contrib import admin
    from django.contrib.sites import NotRegistered
    from app.models import TheChunk
    from app.admin import TheChunkAdmin

    class BetterChunkAdmin(TheChunkAdmin):
        def render_into_region(self, obj, context, extra, **kwargs):
            if obj.pk == 1:
                return None
            return super(BetterChunkAdmin, self).render_into_region(
                obj=obj, context=context, extra=extra, **kwargs)
    try:
        admin.site.unregister(TheChunk)
    except ImportError:
        pass
    admin.site.register(TheChunk, BetterChunkAdmin)

Now our chunk (``TheChunk``) will use ``BetterChunkAdmin``, which is currently
just hardcoded to avoid rendering ``TheChunk`` with a ``pk`` of **1**.

You're welcome to do whatever you like inside the various rendering methods,
as long as they continue to return the right data type.

.. note:: In order to avoid the original ``TheChunkAdmin`` trying to register
          itself *after* the one we just setup, the app configuring
          ``BetterChunkAdmin`` should appear **after** the original app in
          ``INSTALLED_APPS``.

