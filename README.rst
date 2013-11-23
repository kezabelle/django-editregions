django-editregions
==================

Editable regions in templates, editable through the standard Django
admin and database-query efficient.

A bit like django-cms placeholders, but sacrificing much of their
goodness.

Depends on allsorts of not-on-pypi things I've written:

* django-helpfulfields
* django-adminlinks

More flexible with:

* django-moreloaders

Usage
-----

Setting up::

    INSTALLED_APPS += (
        'helpfulfields',
        'adminlinks',
        'editregions',
        'editregions.contrib.files',
        'editregions.contrib.text',
        ...,
    )


Implementing into the admin::

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

Using in the frontend::

    {% load editregion %}
    {% editregion "region-name" mything_object %}

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
                "uploads.File": 2,
            }
        }
    }

Where each key is a region name for the ``{% editregion %}`` template tag,
and the list of models is ``<app_label>.<model_name>``. The value for
each model represents the number of chunks allowed of that type. ``null``
is a special value (equating to ``None``) which allows any number of chunks
to be added.

Without a configuration file, rendering will fail silently.
