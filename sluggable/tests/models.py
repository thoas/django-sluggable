from django.db import models

from sluggable.models import Slug
from sluggable.fields import SluggableField


class PollSlug(Slug):
    class Meta:
        abstract = False


class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    slug = SluggableField(populate_from='question', decider=PollSlug)

    def __unicode__(self):
        return self.question
