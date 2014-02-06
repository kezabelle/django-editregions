===============================
django-editregions test project
===============================

A simple sample Django project to demonstrate what ``editregions`` are,
and what the app does.

Instructions
------------

To get the necessary packages, do::

    pip install -r requirements.txt

Once everything has been installed, you can run the application via::

    python run.py

which should start a Django webserver listening on ``127.0.0.1:8000``.

Using
-----

The *admin* is the most interesting part, and is where you can edit
chunks and regions. Editable regions are pre-attached to ``User``.

The frontend consists of two views, one for listing users, another
for viewing the details of a user;

 * The user list mostly demonstrates `django-adminlinks`_ functionality.
 * The user detail shows off `django-editregions`_ functionality.

.. _django-adminlinks: https://github.com/kezabelle/django-adminlinks
.. _django-editregions: https://github.com/kezabelle/django-editregions

Verifying what it does
----------------------

The project includes `django-debug-toolbar`_ for checking templates loaded,
and database usage;

* After a few HTTP requests, requesting *any* number of
  editregions for a ``User`` should be amortized down into one query, as
  the ``ContentType`` will be cached, and the editregions are loaded greedily
  on first use.
* The parsing of JSON configuration should visibly only trigger one template
  load, no matter how many times it's required during the request/rendering.

.. _django-debug-toolbar: https://github.com/django-debug-toolbar/django-debug-toolbar
