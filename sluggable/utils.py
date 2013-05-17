from __future__ import unicode_literals

from django.db import models


def get_obj_id(obj):
    obj_id = obj

    if isinstance(obj, models.Model):
        obj_id = obj.pk

    return obj_id


def get_prepopulated_value(instance, populate_from):
    """
    Returns preliminary value based on `populate_from`.
    """
    if hasattr(populate_from, '__call__'):
        return populate_from(instance)

    attr = getattr(instance, populate_from)
    return callable(attr) and attr() or attr


def crop_slug(slug, max_length):
    if max_length < len(slug):
        return slug[:max_length]

    return slug


def generate_unique_slug(qs, instance, slug, max_length,
                         field_name, index_sep):
    """
    Generates unique slug by adding a number to given value until no model
    instance can be found with such slug. If ``unique_with`` (a tuple of field
    names) was specified for the field, all these fields are included together
    in the query when looking for a "rival" model instance.
    """

    original_slug = slug = crop_slug(slug, max_length)

    index = 1

    # keep changing the slug until it is unique
    while True:
        # find instances with same slug
        rivals = qs.filter(**{field_name: slug}).exclude(pk=instance.pk)

        if not rivals:
            # the slug is unique, no model uses it
            return slug

        # the slug is not unique; change once more
        index += 1

        # ensure the resulting string is not too long
        tail_length = len(index_sep) + len(str(index))
        combined_length = len(original_slug) + tail_length
        if max_length < combined_length:
            original_slug = original_slug[:max_length - tail_length]

        # re-generate the slug
        data = dict(slug=original_slug,
                    sep=index_sep,
                    index=index)

        slug = '%(slug)s%(sep)s%(index)d' % data

    return slug
