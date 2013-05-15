from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet


from .utils import get_obj_id, generate_unique_slug


class SlugQuerySet(QuerySet):
    def filter_by_obj(self, obj, **kwargs):
        content_type = kwargs.pop('content_type',
                                  ContentType.objects.get_for_model(obj))

        return self.filter(content_type_id=get_obj_id(content_type),
                           object_id=obj.pk,
                           **kwargs)

    def filter_by_obj_id(self, obj_id, content_type, **kwargs):
        return self.filter(content_type_id=get_obj_id(content_type),
                           object_id=obj_id,
                           **kwargs)

    def filter_by_model(self, klass, **kwargs):
        content_type = kwargs.pop('content_type',
                                  ContentType.objects.get_for_model(klass))

        return self.filter(content_type_id=get_obj_id(content_type),
                           **kwargs)


class SlugManager(models.Manager):
    def get_query_set(self):
        return SlugQuerySet(self.model)

    def filter_by_obj(self, *args, **kwargs):
        return self.get_query_set().filter_by_obj(*args, **kwargs)

    def filter_by_model(self, *args, **kwargs):
        return self.get_query_set().filter_by_model(*args, **kwargs)

    def get_current(self, obj, content_type=None):
        if isinstance(obj, models.Model):
            obj_id = obj.pk

            if not content_type:
                content_type = ContentType.objects.get_for_model(obj)

        obj_id = obj

        try:
            return self.filter_by_obj_id(obj_id,
                                         redirect=False,
                                         content_type=content_type).get()
        except self.model.DoesNotExist:
            return None

    def is_slug_available(self, slug, obj=None):
        if slug in self.get_forbidden_slugs():
            return False

        qs = self.filter(slug=slug)

        if not obj is None:
            qs.exclude(object_id=obj.pk,
                       content_type=ContentType.objects.get_for_model(obj))

        if qs.exists():
            return False

        return True

    def generate_unique_slug(self, instance, slug, max_length,
                             field_name, index_sep):

        return generate_unique_slug(self, instance, slug, max_length,
                                    field_name, index_sep)


class Slug(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    slug = models.CharField(max_length=255,
                            verbose_name=_('URL'),
                            db_index=True,
                            unique=True)
    redirect = models.BooleanField(default=False,
                                   verbose_name=_('Redirection'))

    objects = SlugManager()

    class Meta:
        abstract = True

    def get_forbidden_slugs(self):
        return []

    def get_current(self):
        if self.redirect:
            return self

        return Slug.objects.get_current_for_obj(self.object_id,
                                                content_type=self.content_type_id)


class SluggableMixin(object):
    pass
