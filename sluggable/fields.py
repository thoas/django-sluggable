from django.db.models import signals
from django.db import models

from . import settings, utils


class ValueContainer(object):
    def __init__(self, value):
        self.value = value
        self.changed = False

    def __unicode__(self):
        return self.value

    def __eq__(self, other):
        if hasattr(other, 'value'):
            return self.value == other.value

        return self.value == other

    def __nonzero__(self):
        return bool(self.value)

    def __ne__(self, other):
        return not self.__eq__(other)


class SluggableObjectDescriptor(object):
    def __init__(self, field_with_rel):
        self.field = field_with_rel
        self.changed = False

    def __get__(self, instance, instance_type=None):
        val = instance.__dict__.get(self.field.attname, None)

        if val is None:
            # If NULL is an allowed value, return it.
            if self.field.null:
                return None

        return val

    def __set__(self, instance, value):
        value = self.field.attr_class(value)

        instance.__dict__[self.field.attname] = value

        value.changed = True


class SluggableField(models.SlugField):
    descriptor_class = SluggableObjectDescriptor
    attr_class = ValueContainer

    def __init__(self, *args, **kwargs):
        self.decider = kwargs.pop('decider', None)
        self.populate_from = kwargs.pop('populate_from', None)
        self.always_update = kwargs.pop('always_update', False)
        self.index_sep = kwargs.pop('sep', settings.SLUGGABLE_SEPARATOR)
        self.manager = kwargs.pop('manager', None)
        self.slugify = kwargs.pop('slugify', settings.slugify)
        assert hasattr(self.slugify, '__call__')

        super(SluggableField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SluggableField, self).contribute_to_class(cls, name)

        signals.pre_save.connect(self.instance_pre_save, sender=cls)
        signals.post_save.connect(self.instance_post_save, sender=cls)
        signals.post_delete.connect(self.instance_post_delete, sender=cls)

        if not hasattr(self.decider, 'sluggable_models'):
            self.decider.sluggable_models = []

        self.decider.sluggable_models.append(cls)

        setattr(cls, self.name, self.descriptor_class(self))

    def instance_pre_save(self, instance, *args, **kwargs):
        original_value = value = self.value_from_object(instance)

        if self.always_update or (self.populate_from and not value):
            value = utils.get_prepopulated_value(instance, self.populate_from)

        if value and (original_value != value or getattr(instance, self.name).changed):
            slug = utils.crop_slug(self.slugify(value), self.max_length)

            slug = self.decider.objects.generate_unique_slug(instance, slug,
                                                             self.max_length,
                                                             self.name,
                                                             self.index_sep)

            setattr(instance, self.name, slug)

            return slug

        return None

    def instance_post_save(self, instance, **kwargs):
        self.decider.objects.update_slug(instance, instance.slug)

    def instance_post_delete(self, instance, **kwargs):
        self.decider.objects.filter_by_obj(instance).delete()

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'value'):
            value = value.value

        return super(SluggableField, self).get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        if value is None:
            return None

        return unicode(value)
