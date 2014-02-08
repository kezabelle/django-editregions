django-editregions
==================

Allows for "editable regions" attached to *any* Django model instance,
with simple configuration and usage.

  * May be configured by template designers using straight-forward JSON
    with full support for Django template language logic.
  * Regions can be registered to appear in the ModelAdmin for the Model
    instance.
  * Content chunks are **opt-in**, and may have maximum usages per region.
  * Database efficient - one query to fetch all chunks attached to a
    Model instance, no matter how many times they're rendered. The opt-in
    method of chunk availability means only the required tables are ever
    requested. (uses `django-model-utils`_)


A bit like `django-CMS`_ placeholders + plugins, but sacrificing some of the
more complex functionality they provide:

  * Chunks may not be nested within eachother - they're a stack, not a tree.
  * Chunks have no concept of language. I'm monolingual, so figuring out
    support for multi-lingual chunks isn't something **I** need.
  * JavaScript popups for editing *in-page* is all provided by
    `django-adminlinks`_, for better or worse, and the experience is probably
    less friendly than the 3.x branch of `django-CMS`_

Depends on allsorts of not-on-pypi things I've written:

* `django-adminlinks`_ - for admin popups, and misc utilities.
* `django-moreloaders`_ - to allow flexible template caching

.. _django-adminlinks: https://github.com/kezabelle/django-adminlinks
.. _django-moreloaders: https://github.com/kezabelle/django-moreloaders
.. _django-CMS: https://github.com/divio/django-cms
.. _django-model-utils: https://github.com/carljm/django-model-utils

Status
------

Tests all pass locally on ``python2.6``, ``python2.7``, ``python3.3``
and ``pypy``. The same test suite fails on `Travis`_, and I've no idea
why. YMMV. Alpha-quality stuff here, folks.

.. _Travis: https://travis-ci.org/

Bundled "chunks"
----------------

models capable of being embedded into editable regions:

* WYM and TinyMCE text editors.
* File upload (including image handling...)
* Inline javascript
* External CSS & Javascript (both local & via remote URL)
* iframes
* external RSS feeds
* `Haystack`_ "more like this"
* `Haystack`_ search results for a given query

.. _Haystack: https://github.com/toastdriven/django-haystack

Usage
-----

Setting up::

    INSTALLED_APPS += (
        'adminlinks',
        'editregions',
        'editregions.contrib.files',
        'editregions.contrib.text',
        'editregions.contrib.embeds',
        ...,
        # and if you want haystack stuff ...
        'editregions.contrib.search',
    )


Implementing into the admin requires at the minimum the following::

    from django.contrib import admin
    from myapp.models import MyThing
    from editregions.admin.inlines import EditRegionInline


    class MyAdmin(admin.ModelAdmin):
        inlines = [
            EditRegionInline,
        ]

        def get_editregions_templates(self, obj):
            return [obj.template]
    admin.site.register(MyThing, MyAdmin)


There is a mixin object to provide that functionality without having to
write anything yourself::

    from django.contrib import admin
    from myapp.models import MyThing
    from editregions.admin.modeladmins import SupportsEditRegions
    from editregions.admin.inlines import EditRegionInline


    class MyAdmin(SupportsEditRegions, admin.ModelAdmin):
        pass
    admin.site.register(MyThing, MyAdmin)


Using in your frontend templates::

    {% load editregion %}
    {% editregion "region-name" mything_object %}


An editregion can be inherited from an ancestor object like so::

    {% editregion "region-name" myobject inherit %}


This requires the ``myobject`` instance to have a ``get_ancestors`` method
which returns all possibly parents. Both `django-mptt`_ and `django-treebeard`_
have that method, which should cover most tree-like usages.

.. _django-mptt: https://github.com/django-mptt/django-mptt
.. _django-treebeard: https://tabo.pe/projects/django-treebeard/

Configuration
-------------

Allowing chunks requires a **JSON** file with the same name & path
as the discovered template. Given a template of ``path/to/file.html``
the JSON file would be ``path/to/file.json``.

The region configuration might look like this::

    {
        "region-name": {
            "name": "Human friendly region name",
            "models": {
                "text.WYM": null,
                "text.MCE": null,
                "uploads.File": 2
            }
        }
    }


Where each key is a region name for the ``{% editregion %}`` template tag,
and the list of models is ``<app_label>.<model_name>``. The value for
each model represents the number of chunks allowed of that type. ``null``
is a special value (equating to ``None``) which allows any number of chunks
to be added.

Without a configuration file:

  * rendering will fail silently if ``DEBUG`` is ``False``
  * rendering will try and fail loudly and helpfully if ``DEBUG`` is ``True``
