
from unittest2 import TestCase
from fixtures import TestWithFixtures
from . import FakeChrootFixture


class TestFakeChrootFixture(TestCase, TestWithFixtures):

    def setUp(self):
        self.chroot = self.useFixture(FakeChrootFixture())

    def test_call_bin_true(self):
        self.assertEqual(0, self.chroot.call(["/bin/true"]))

    def test_call_bin_false(self):
        self.assertEqual(0, self.chroot.call(["/bin/false"]))

