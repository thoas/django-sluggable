import django

from django.db import models
from django.contrib.contenttypes.models import ContentType
try:
    from django.contrib.contenttypes.fields import GenericForeignKey
except ImportError:
    from django.contrib.contenttypes.generic import GenericForeignKey  # noqa

from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import python_2_unicode_compatible


from .utils import get_obj_id, generate_unique_slug


class SlugQuerySet(QuerySet):
    def filter_by_obj(self, obj, **kwargs):
        content_type = kwargs.pop('content_type',
                                  ContentType.objects.get_for_model(obj))

        return self.filter_by_obj_id(obj.pk,
                                     content_type=content_type,
                                     **kwargs)

    def filter_by_obj_id(self, obj_id, content_type, **kwargs):
        return self._filter_or_exclude(kwargs.pop('exclude', False),
                                       content_type_id=get_obj_id(content_type),
                                       object_id=obj_id,
                                       **kwargs)

    def filter_by_model(self, klass, **kwargs):
        content_type = kwargs.pop('content_type',
                                  ContentType.objects.get_for_model(klass))

        return self.filter(content_type_id=get_obj_id(content_type),
                           **kwargs)


class SlugManager(models.Manager):
    def get_queryset(self):
        return SlugQuerySet(self.model)

    if django.VERSION < (1, 6):
        get_query_set = get_queryset

    def filter_by_obj(self, *args, **kwargs):
        return self.get_queryset().filter_by_obj(*args, **kwargs)

    def filter_by_obj_id(self, *args, **kwargs):
        return self.get_queryset().filter_by_obj_id(*args, **kwargs)

    def filter_by_model(self, *args, **kwargs):
        return self.get_queryset().filter_by_model(*args, **kwargs)

    def get_current(self, obj, content_type=None):
        if isinstance(obj, models.Model):
            obj_id = obj.pk

            if not content_type:
                content_type = ContentType.objects.get_for_model(obj)
        else:
            obj_id = obj

        try:
            return self.filter_by_obj_id(obj_id,
                                         content_type=content_type,
                                         redirect=False).get()
        except ObjectDoesNotExist:
            return None

    def is_slug_available(self, slug, obj=None):
        if slug in self.model.forbidden_slugs():
            return False

        qs = self.filter(slug=slug)

        if obj is not None:
            qs = qs.filter_by_obj(obj, exclude=True)

        if qs.exists():
            return False

        return True

    def generate_unique_slug(self, instance, slug, max_length, index_sep):

        qs = self.filter_by_obj(instance, exclude=True)

        return generate_unique_slug(qs, instance, slug, max_length,
                                    'slug', index_sep)

    def update_slug(self, instance, slug,
                    erase_redirects=False,
                    created=False):
        content_type = ContentType.objects.get_for_model(instance)

        pk = instance.pk

        update = False
        affected = True
        filters = {
            'content_type': content_type,
            'object_id': pk,
            'redirect': False,
            'slug': slug,
        }

        if not created:
            try:
                current = self.get(**filters)
                new = False
                update = current.slug != slug
            except self.model.DoesNotExist:
                new = True
                update = True

        if created or update:
            if not created:
                base_qs = self.filter(content_type=content_type,
                                      object_id=pk)

                qs = base_qs.exclude(slug=slug)

                if not new and erase_redirects:
                    qs.delete()
                else:
                    qs.update(redirect=True)

                affected = base_qs.filter(slug=slug).update(redirect=False)

            if not affected or created:
                slug = self.model(**filters)
                slug.save()


@python_2_unicode_compatible
class Slug(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    slug = models.CharField(max_length=255,
                            verbose_name=_('URL'),
                            db_index=True,
                            unique=True)
    redirect = models.BooleanField(default=False,
                                   verbose_name=_('Redirection'))

    created = models.DateTimeField(auto_now_add=True)

    objects = SlugManager()

    class Meta:
        abstract = True

    def __str__(self):
        return _('%s for %s') % (self.slug, self.content_object)

    @classmethod
    def forbidden_slugs(self):
        return []

    @property
    def current(self):
        if not self.redirect:
            return self

        klass = self.__class__

        return klass.objects.get_current(self.object_id,
                                         content_type=self.content_type_id)
