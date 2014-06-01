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

from .unittest2 import TestCase


class TestFakeChrootFixture(TestCase):

    def test_call_bin_true(self):
        self.assertEqual(0, self.chroot.call(["/bin/true"]))

    def test_call_bin_false(self):
        self.assertEqual(1, self.chroot.call(["/bin/false"]))

    def test_exists_true(self):
        self.assertEqual(self.chroot.exists("/bin/true"), True)

    def test_exists_false(self):
        self.assertEqual(self.chroot.exists("/bin/does_not_exists"), False)

    def test_isdir_true(self):
        self.assertEqual(self.chroot.isdir("/bin"), True)

    def test_isdir_false(self):
        self.assertEqual(self.chroot.isdir("/bin/true"), False)

    def test_mkdir(self):
        self.assertEqual(self.chroot.isdir("/newdir"), False)
        self.chroot.mkdir("/newdir")
        self.assertEqual(self.chroot.isdir("/newdir"), True)

    def test_open_read(self):
        data = self.chroot.open("/etc/passwd").read()
        self.assertTrue(len(data) > 0)

    def test_touch(self):
        self.assertEqual(self.chroot.exists("/test-touch"), False)
        self.chroot.touch("/test-touch")
        self.assertEqual(self.chroot.exists("/test-touch"), True)

    def test_chmod(self):
        self.chroot.touch("/test-chmod")
        self.assertTrue((self.chroot.stat("/test-chmod").st_mode & 0o777) != 0o755)
        self.chroot.chmod("/test-chmod", 0o755)

        self.assertEqual((self.chroot.stat("/test-chmod").st_mode & 0o777), 0o755)

    def test_symlink_and_readlink(self):
        self.chroot.symlink("/etc", "/other-etc")
        self.assertEqual(self.chroot.readlink("/other-etc"), "/etc")

    def test_stat(self):
        result = self.chroot.stat("/root")
        self.assertEqual(result.st_mode & 0o777, 0o700)
        # self.assertEqual(result.st_uid, 0)
        # self.assertEqual(result.st_gid, 0)

    def test_get_user(self):
        user = self.chroot.get_user("root")
        self.assertEqual(user[4], "/root")

    def test_get_group(self):
        group = self.chroot.get_group("root")
        self.assertEqual(group[1], "0")

