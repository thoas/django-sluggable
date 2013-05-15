from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet


class SlugQuerySet(QuerySet):
    def filter_by_obj(self, obj, **kwargs):
        content_type = ContentType.objects.get_for_model(obj)

        return self.filter(content_type=content_type,
                           object_id=obj.pk,
                           **kwargs)

    def filter_by_model(self, klass, **kwargs):
        content_type = ContentType.objects.get_for_model(klass)

        return self.filter(content_type=content_type, **kwargs)


class SlugManager(models.Manager):
    def get_query_set(self):
        return SlugQuerySet(self.model)

    def filter_by_obj(self, *args, **kwargs):
        return self.get_query_set().filter_by_obj(*args, **kwargs)

    def filter_by_model(self, *args, **kwargs):
        return self.get_query_set().filter_by_model(*args, **kwargs)

    def get_current_for_obj(self, obj):
        try:
            return self.filter_by_obj(obj, redirect=False)
        except self.model.DoesNotExist:
            return None

    def is_slug_available(self, slug):
        if slug in self.get_forbidden_slugs():
            return False

        if self.filter(slug=slug).exists():
            return False

        return True


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

    class Meta:
        abstract = True

    def get_sluggable_models(self):
        raise NotImplementedError

    def get_forbidden_slugs(self):
        return []


class SluggableMixin(object):
    pass
