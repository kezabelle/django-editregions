editregions.contrib.embeds
==========================

Provides support for putting in:

* <iframe src="...">
* RSS feeds, parsed by `feedparser`_ and cached using Django's built-in caching.

  * Don't use it with a dummy backend!
* JavaScript, directly, using `django-ace`_ to provide syntax highlighting.

  * This is potentially unsafe, so consider long and hard before enabling it.
  * I may remove it, ultimately.
* Remote or local JavaScript/CSS files

  * Local CSS files will be available if their path is
    ``editregions/embeds/*.css``, and all static folders will be searched.
  * Local JS files will be the same, but the search path
    is ``editregions/embeds/*.js``
  * Remote files can be made scheme-relative by using ``obj.external_scheme_relative()``

.. _django-ace: https://github.com/bradleyayers/django-ace
.. _feedparser: https://code.google.com/p/feedparser/
