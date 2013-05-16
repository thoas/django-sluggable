.. _ref-usage:

=====
Usage
=====

Integrating in an application
-----------------------------

To use `django-sluggable`_ we will provide a basic application in this section.

Consider having the following ``models.py``::

    # users/models.py

    class User(models.Model):
        username = models.CharField(max_length=150)

Now you want urls like ``/users/<username>`` but also keeping your SEO when
a specific user is changing his username: we want a permanent redirection
between the old username and the new one.


In ``models.py``, we will define a decider model which will store all usernames::

    # users/models.py

    from sluggable.models import Slug

    class UserSlug(Slug):
        class Meta:
            abstract = False

In the case of our ``User`` class the slug is basically the username of the user,
so we will change the type of the ``username`` field.

::

    # users/models.py

    from sluggable.fields import SluggableField

    class User(models.Model):
        username = SluggableField(decider=UserSlug)

        def __unicode__(self):
            return self.username


Now you have your sluggable model, let's play with the API,
by adding our first member in the console::

    In [1]: from users.models import User, UserSlug
    In [2]: user = User.objects.create(username="thoas")

When you are creating a new ``User`` it will also create a linked model by
using the `contenttypes`_ framework of Django::

    In [3]: user_slug = UserSlug.objects.get(slug="thoas")
    In [4]: user_slug.redirect
    False

With this ``UserSlug`` you can now track every username changes by your users.

Remember your first created user right? We will change its username::

    In [5]: user.username = 'oleiade'
    In [6]: user.save()

You new username is now your primary username and you will be able to provide
a permanent redirection between the old one and new one::

    In [7]: user_slug = UserSlug.objects.get(slug="oleiade")
    In [8]: user_slug.redirect
    False
    In [9]: old_slug = UserSlug.objects.get(slug="thoas")
    In [10]: old_slug.redirect
    True

If you are accessing an old slug, you can also retrieve the current one at any
time::

    In [11]: old_slug.current
    <Slug thoas for oleiade>

If you do not have a ``Slug`` instance, no problem you can use the default manager
for that::

    In [12]: Slug.objects.get_current(user)
    <Slug oleiade for oleiade>

Working with class-based views
------------------------------

More to come

.. _`contenttypes`: https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
.. _`django-sluggable`: https://github.com/thoas/django-sluggable
