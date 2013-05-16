from django.test import TestCase

from .models import Poll, PollSlug


class SluggableTests(TestCase):
    def test_simple_add(self):
        poll = Poll.objects.create(question='Quick test')

        self.assertEquals(poll.slug, u'quick-test')

        self.assertEquals(PollSlug.objects.count(), 1)

        slug = PollSlug.objects.get(slug='quick-test')

        self.assertEquals(slug.slug, 'quick-test')

        self.assertFalse(slug.redirect)

        self.assertEquals(slug.content_object, poll)

        poll.question = 'Another test'
        poll.save()

        self.assertEquals(poll.slug, u'quick-test')

        poll.slug = 'quick-test-2'
        poll.save()

        self.assertEquals(PollSlug.objects.count(), 2)

        slug = PollSlug.objects.get(slug='quick-test-2')

        self.assertFalse(slug.redirect)

        slug = PollSlug.objects.get(slug='quick-test')
        self.assertTrue(slug.redirect)
