from django.test import TestCase

from .models import Poll, PollSlug


class SluggableTests(TestCase):
    def test_simple_add(self):
        poll = Poll.objects.create(question='Quick test')

        self.assertEquals(poll.slug, 'quick-test')

        self.assertEquals(PollSlug.objects.count(), 1)

        slug = PollSlug.objects.get(pk=1)

        self.assertEquals(slug.slug, 'quick-test')

        self.assertFalse(slug.redirect)

        self.assertEquals(slug.content_object, poll)
