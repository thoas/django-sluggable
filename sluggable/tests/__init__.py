from django.test import TestCase

from .models import Poll, PollSlug


class SluggableTests(TestCase):
    def test_simple_add(self):
        poll = Poll.objects.create(question='Quick test')
