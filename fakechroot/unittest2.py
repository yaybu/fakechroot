# Copyright 2013 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
import os
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from .fakechroot import FakeChroot


class TestCase(unittest.TestCase):

    FakeChroot = FakeChroot
    location = os.path.join(os.path.dirname(__file__), "..")

    def setUp(self):
        self.chroot = self.FakeChroot.create_in_tempdir(self.location)
        self.addCleanup(self.chroot.destroy)
        self.chroot.build()

    def failUnlessExists(self, path):
        if not self.chroot.exists(path):
            self.fail("Path '%s' does not exist" % path)

    def failIfExists(self, path):
        if self.chroot.exists(path):
            self.fail("Path '%s' exists" % path)

