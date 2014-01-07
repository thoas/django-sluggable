from django.db.models import signals
from django.db import models
from django.utils import six

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
        self.populate_from = kwargs.pop('populate_from', None)
        self.always_update = kwargs.pop('always_update', False)
        self.index_sep = kwargs.pop('sep', settings.SLUGGABLE_SEPARATOR)
        self.manager = kwargs.pop('manager', None)

        # unique_with value can be string or tuple
        self.unique_with = kwargs.pop('unique_with', ())
        if isinstance(self.unique_with, six.string_types):
            self.unique_with = (self.unique_with,)

        self.slugify = kwargs.pop('slugify', settings.slugify)
        assert hasattr(self.slugify, '__call__')

        if self.unique_with:
            # we will do "manual" granular check below
            kwargs['unique'] = False

        super(SluggableField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SluggableField, self).contribute_to_class(cls, name)

        signals.post_init.connect(self.instance_post_init, sender=cls)
        signals.pre_save.connect(self.instance_pre_save, sender=cls)
        signals.post_save.connect(self.instance_post_save, sender=cls)
        signals.post_delete.connect(self.instance_post_delete, sender=cls)

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

            # ensure the slug is unique (if required)
            if self.unique or self.unique_with:
                slug = utils.generate_unique_slug(self, instance, slug, self.manager)

            setattr(instance, self.name, slug)

            return slug

        return None

    def instance_post_save(self, instance, **kwargs):
        if getattr(instance, '%s_changed' % self.name, False):
            instance.slugs.update_slug(instance,
                                             getattr(instance, self.name),
                                             created=kwargs.get('created', False))

        setattr(instance, '%s_changed' % self.name, False)

    def instance_post_delete(self, instance, **kwargs):
        instance.slugs.filter_by_obj(instance).delete()

    def get_prep_lookup(self, lookup_type, value):
        if hasattr(value, 'value'):
            value = value.value

        return super(SluggableField, self).get_prep_lookup(lookup_type, value)

    def get_prep_value(self, value):
        if value is None:
            return None

        return unicode(value)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        args, kwargs = introspector(self)
        kwargs.update({
            'populate_from': 'None' if callable(self.populate_from) else repr(self.populate_from),
            'unique_with': repr(self.unique_with),
        })
        return ('sluggable.fields.SluggableField', args, kwargs)
