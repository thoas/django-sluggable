from django.db.models import signals
from django.db import models


class SluggableField(models.SlugField):
    def __init__(self, *args, **kwargs):
        self.decider = kwargs.pop('decider', None)
        self.populate_from = kwargs.pop('populate_from', None)
        self.always_update = kwargs.pop('always_update', False)

        super(SluggableField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SluggableField, self).contribute_to_class(cls, name)

        signals.pre_save.connect(self.post_save, sender=cls)
        signals.post_save.connect(self.post_save, sender=cls)
        signals.post_delete.connect(self.post_delete, sender=cls)

        setattr(cls, self.name, SluggableObjectDescriptor(self))

    def pre_save(self, *args, **kwargs):
        pass

    def post_save(self, instance, **kwargs):
        pass

    def post_delete(self, instance, **kwargs):
        pass


class SluggableObjectDescriptor(object):
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        val = instance.__dict__.get(self.field.attname, None)

        if val is None:
            # If NULL is an allowed value, return it.
            if self.field.null:
                return None

        return val

    def __set__(self, instance, value):
        instance.__dict__[self.field.attname] = value
