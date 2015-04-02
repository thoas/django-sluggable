from __future__ import unicode_literals

from django.db.models import signals
from django.db import models

from . import settings, utils

try:
    from south.modelsinspector import introspector
except ImportError:
    introspector = lambda self: [], {}


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
        instance.__dict__[self.field.attname] = value

        setattr(instance, '%s_changed' % self.field.attname, True)


class SluggableField(models.SlugField):
    descriptor_class = SluggableObjectDescriptor

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

        signals.post_init.connect(self.instance_post_init, sender=cls)
        signals.pre_save.connect(self.instance_pre_save, sender=cls)
        signals.post_save.connect(self.instance_post_save, sender=cls)
        signals.post_delete.connect(self.instance_post_delete, sender=cls)

        if self.decider:
            if not hasattr(self.decider, 'sluggable_models'):
                self.decider.sluggable_models = []

            self.decider.sluggable_models.append(cls)

        setattr(cls, self.name, self.descriptor_class(self))
        setattr(cls, '%s_changed' % self.name, True)

    def instance_post_init(self, instance, *args, **kwargs):
        if instance.pk:
            setattr(instance, '%s_changed' % self.name, False)

    def instance_pre_save(self, instance, *args, **kwargs):
        original_value = value = self.value_from_object(instance)

        if self.always_update or (self.populate_from and not value):
            value = utils.get_prepopulated_value(instance, self.populate_from)

        if value and (original_value != value or getattr(instance, '%s_changed' % self.name, False)):
            slug = utils.crop_slug(self.slugify(value), self.max_length)

            slug = self.decider.objects.generate_unique_slug(instance, slug,
                                                             self.max_length,
                                                             self.index_sep)

            setattr(instance, self.name, slug)

            return slug

        return None

    def instance_post_save(self, instance, **kwargs):
        if getattr(instance, '%s_changed' % self.name, False):
            self.decider.objects.update_slug(instance,
                                             getattr(instance, self.name),
                                             created=kwargs.get('created', False))

        setattr(instance, '%s_changed' % self.name, False)

    def instance_post_delete(self, instance, **kwargs):
        self.decider.objects.filter_by_obj(instance).delete()

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'value'):
            value = value.value

        return super(SluggableField, self).get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        if value is None:
            return None

        return value

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        args, kwargs = introspector(self)
        kwargs.update({'populate_from': 'None'})
        return ('sluggable.fields.SluggableField', args, kwargs)
