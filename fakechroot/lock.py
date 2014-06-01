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

"""
Simple locking strategy

This is used to prevent races when using a multi-process test runner.
"""

import os
import time
import six


class Locked(Exception):
    pass


class Lock(object):

    def __init__(self, path):
        self.path = path
        self.fp = None

        if not os.path.isdir(os.path.dirname(path)):
            raise ValueError("'%s' is not a valid directory" % os.path.dirname(path))
 
    def open(self):
        if self.locked():
            raise Locked(self.path)

        try:
            self.fp = os.open(self.path, os.O_CREAT | os.O_RDWR | os.O_EXCL)
        except OSError:
            for i in range(20):
                if self.locked():
                    raise Locked(self.path)
                time.sleep(0.1)
            raise

        os.write(self.fp, six.binary_type(os.getpid()))

    def close(self):
        if self.fp:
            os.close(self.fp)
            self.fp = None
            if os.path.exists(self.path):
                os.unlink(self.path)

    def locked(self):
        if not os.path.exists(self.path):
            return False

        try:
            pid = int(open(self.path).read())
        except ValueError:
            return False
        except IOError:
            if not os.path.exists(self.path):
                return False
            raise
        try:
            os.kill(pid, 0)
        except OSError:
            return False

        if pid == os.getpid():
            raise AssertionError("Already locked by current process?")

        return True

    def wait(self):
        while self.locked():
            time.sleep(0.1)
 
