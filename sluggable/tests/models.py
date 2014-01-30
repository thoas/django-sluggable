from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes import generic

from sluggable.models import Slug
from sluggable.fields import SluggableField


class PollSlug(Slug):
    pass

@python_2_unicode_compatible
class Poll(models.Model):
    question = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    slug = SluggableField(populate_from='question', unique=True)
    slugs = generic.GenericRelation(PollSlug)

    def __str__(self):
        return self.question


class UserSlug(Slug):
    pass

class User(models.Model):
    username = SluggableField(unique=True)
    slugs = generic.GenericRelation(UserSlug)


class PostSlug(Slug):
    pass

class Post(models.Model):
    user = models.ForeignKey(User)
    slug = SluggableField(unique_with='user')
    slugs = generic.GenericRelation(PostSlug)

class DayPost(models.Model):
    date = models.DateField()
    slug = SluggableField(unique_with='date')
    slugs = generic.GenericRelation(PostSlug)

class WordPost(models.Model):
    user = models.ForeignKey(User)
    word = models.CharField(max_length=50, blank=True)
    slug = SluggableField(unique_with=('user', 'word'))
    slugs = generic.GenericRelation(PostSlug)
