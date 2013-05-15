from autoslug.fields import AutoSlugField

from django.db.models import signals


class SluggableField(AutoSlugField):
    def __init__(self, *args, **kwargs):
        self.decider = kwargs.pop('decider', None)

        super(SluggableField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(SluggableField, self).contribute_to_class(cls, name)

        signals.pre_save.connect(self.post_save, sender=cls)
        signals.post_save.connect(self.post_save, sender=cls)
        signals.post_delete.connect(self.post_delete, sender=cls)

        setattr(cls, self.name, SluggableObjectDescriptor(self))

    def pre_save(self, instance, **kwargs):
        pass

    def post_save(self, instance, **kwargs):
        pass

    def post_delete(self, instance, **kwargs):
        pass


class SluggableObjectDescriptor(object):
    def __init__(self, field_with_rel):
        self.field = field_with_rel

    def __get__(self, instance, instance_type=None):
        val = getattr(instance, self.field.attname)
        if val is None:
            # If NULL is an allowed value, return it.
            if self.field.null:
                return None

        return val

    def __set__(self, instance, value):
        setattr(instance, self.field.attname, value)
