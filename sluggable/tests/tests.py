from django.test import TestCase

from .models import Answer, AnswerSlug, Poll, PollSlug, UserSlug, User


class SluggableTests(TestCase):
    def test_sluggable_models_for_decider(self):
        self.assertEqual(PollSlug.sluggable_models, [Poll])

    def test_slug_without_populate_from(self):
        with self.assertNumQueries(4):
            user = User.objects.create(username="thoas")

        self.assertEqual(UserSlug.objects.count(), 1)

        user.username = "oleiade"
        user.save()

        self.assertEqual(UserSlug.objects.count(), 2)

        current = UserSlug.objects.get_current(user)

        self.assertEqual(current.slug, "oleiade")

        user.username = "thoas"
        user.save()

        current = UserSlug.objects.get_current(user)

        self.assertEqual(current.slug, "thoas")

        self.assertEqual(UserSlug.objects.filter(redirect=True).count(), 1)

        user = User.objects.create(username="thoas")

        self.assertEqual(user.username, "thoas-2")

        old = User.objects.get(username="thoas")
        old.delete()

        user.username = "thoas"
        user.save()

        self.assertEqual(user.username, "thoas")

    def test_changed(self):
        poll = Poll.objects.create(question="Quick test")

        self.assertFalse(poll.slug_changed)

        poll = Poll.objects.get(slug="quick-test")

        self.assertFalse(poll.slug_changed)

        poll = Poll(question="Quick test")

        self.assertTrue(poll.slug_changed)

        poll.save()

        self.assertEqual(poll.slug, "quick-test-2")

    def test_simple_add(self):
        poll = Poll.objects.create(question="Quick test")

        self.assertEqual(poll.slug, "quick-test")

        self.assertEqual(PollSlug.objects.count(), 1)

        slug = PollSlug.objects.get(slug="quick-test")

        self.assertEqual(slug.slug, "quick-test")

        self.assertFalse(slug.redirect)

        self.assertEqual(slug.content_object, poll)

    def test_simple_when_slugfield_is_nullable(self):
        answer = Answer.objects.create()

        self.assertIsNone(answer.slug)

        self.assertEqual(AnswerSlug.objects.count(), 0)

    def test_simple_add_when_slugfield_is_nullable(self):
        answer = Answer.objects.create()

        answer.slug = "answer"
        answer.save()

        self.assertEqual(answer.slug, "answer")

        self.assertEqual(AnswerSlug.objects.count(), 1)

        slug = AnswerSlug.objects.get(slug="answer")

        self.assertEqual(slug.slug, "answer")

        self.assertFalse(slug.redirect)

        self.assertEqual(slug.content_object, answer)

    def test_redirect(self):
        poll = Poll.objects.create(question="Quick test")
        poll.question = "Another test"
        poll.save()

        self.assertEqual(poll.slug, "quick-test")

        poll.slug = "quick-test-2"
        poll.save()

        self.assertEqual(PollSlug.objects.count(), 2)

        slug = PollSlug.objects.get(slug="quick-test-2")

        self.assertFalse(slug.redirect)

        old = PollSlug.objects.get(slug="quick-test")

        self.assertTrue(old.redirect)

        current = PollSlug.objects.get_current(poll)

        self.assertEqual(old.current, slug)

        self.assertFalse(current is None)

        self.assertFalse(current.redirect)

    def test_redirect_restore_previous_slug(self):
        poll = Poll.objects.create(question="Quick test")
        poll.question = "Another test"
        poll.save()

        poll.slug = "quick-test-2"
        poll.save()

        self.assertEqual(PollSlug.objects.count(), 2)

        poll.slug = "quick-test"
        poll.save()

        self.assertEqual(PollSlug.objects.count(), 2)

        slug = PollSlug.objects.get(slug="quick-test")
        self.assertFalse(slug.redirect)

        self.assertEqual(PollSlug.objects.filter(redirect=False).count(), 1)

        current = PollSlug.objects.get_current(poll)

        self.assertEqual(current.slug, "quick-test")

    def test_is_slug_available(self):
        poll = Poll.objects.create(question="Quick test")

        self.assertFalse(PollSlug.objects.is_slug_available("quick-test"))

        self.assertTrue(PollSlug.objects.is_slug_available("quick-test", obj=poll))

    def test_delete(self):
        poll = Poll.objects.create(question="Quick test")

        self.assertEqual(PollSlug.objects.count(), 1)

        poll.delete()

        self.assertEqual(PollSlug.objects.count(), 0)
