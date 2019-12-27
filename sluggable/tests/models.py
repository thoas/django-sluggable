from django.db import models

from sluggable.models import Slug
from sluggable.fields import SluggableField


class PollSlug(Slug):
    class Meta:
        abstract = False


class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    slug = SluggableField(populate_from="question", decider=PollSlug)

    def __str__(self):
        return self.question


class UserSlug(Slug):
    class Meta:
        abstract = False


class User(models.Model):
    username = SluggableField(decider=UserSlug, unique=True)


class AnswerSlug(Slug):
    class Meta:
        abstract = False


class Answer(models.Model):
    slug = SluggableField(null=True, decider=AnswerSlug)
