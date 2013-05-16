from django.test import TestCase

from .models import Poll, PollSlug


class SluggableTests(TestCase):
    def test_sluggable_models_for_decider(self):
        self.assertEquals(PollSlug.sluggable_models, [Poll])

    def test_simple_add(self):
        poll = Poll.objects.create(question='Quick test')

        self.assertEquals(poll.slug, u'quick-test')

        self.assertEquals(PollSlug.objects.count(), 1)

        slug = PollSlug.objects.get(slug='quick-test')

        self.assertEquals(slug.slug, 'quick-test')

        self.assertFalse(slug.redirect)

        self.assertEquals(slug.content_object, poll)

    def test_redirect(self):
        poll = Poll.objects.create(question='Quick test')
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

        current = PollSlug.objects.get_current(poll)

        self.assertFalse(current is None)

        self.assertFalse(current.redirect)

    def test_redirect_restore_previous_slug(self):
        poll = Poll.objects.create(question='Quick test')
        poll.question = 'Another test'
        poll.save()

        poll.slug = 'quick-test-2'
        poll.save()

        self.assertEquals(PollSlug.objects.count(), 2)

        poll.slug = 'quick-test'
        poll.save()

        self.assertEquals(PollSlug.objects.count(), 2)

        slug = PollSlug.objects.get(slug='quick-test')
        self.assertFalse(slug.redirect)

        self.assertEquals(PollSlug.objects.filter(redirect=False).count(), 1)

        current = PollSlug.objects.get_current(poll)

        self.assertEquals(current.slug, 'quick-test')

    def test_is_slug_available(self):
        poll = Poll.objects.create(question='Quick test')

        self.assertFalse(PollSlug.objects.is_slug_available('quick-test'))

        self.assertTrue(PollSlug.objects.is_slug_available('quick-test', obj=poll))

    def test_delete(self):
        poll = Poll.objects.create(question='Quick test')

        self.assertEquals(PollSlug.objects.count(), 1)

        poll.delete()

        self.assertEquals(PollSlug.objects.count(), 0)
