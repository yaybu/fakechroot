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

import collections
import os, glob, signal, shlex, subprocess, tempfile
import shutil

from .lock import Lock, Locked


supported_distros = ('lucid', 'precise', 'quantal', 'raring')

stat_result = collections.namedtuple(
    "stat_result",
    ("st_mode", "st_ino", "st_dev", "st_nlink", "st_uid", "st_gid",
     "st_size", "st_atime", "st_mtime", "st_ctime")
)


class FakeChrootError(Exception):
    pass


class FakeChroot(object):

    firstrun = True
    fakerootkey = None
    checked_supported = False
    Exception = RuntimeError

    def __init__(self, path, base_path=None, distro='precise'):
        self.distro = distro

        self.path = path
        self.chroot_path = os.path.join(path, "chroot")
        self.faked_state_path = os.path.join(path, "faked-state")
        self.ilist_path = os.path.join(path, "ilist")
        self.overlay_dir = os.path.join(path, 'overlay')

        self.src_path = os.path.realpath(os.path.join(path, ".."))
        self.base_path = base_path or os.path.join(self.src_path, "base-image")
        self.lock_path = self.base_path + ".lock"

        self.faked = None

    @classmethod
    def create_in_tempdir(cls, parent):
        path = tempfile.mkdtemp(dir=parent)
        return cls(path)

    def _assert_supported(self):
        if FakeChroot.checked_supported:
            return

        dependencies = (
            "/usr/bin/fakeroot",
            "/usr/bin/fakechroot",
            "/usr/sbin/debootstrap",
            "/usr/bin/cow-shell",
            )

        for dep in dependencies:
            if not os.path.exists(dep):
                raise FakeChrootError("Need '%s' to run integration tests" % dep)
        FakeChroot.checked_supported = True

    def build(self):
        self._assert_supported()

        # The first time we use the fixture per test run we might 'refresh' it
        # - that means making sure that it actually exists and that the latest code is
        # deployed in it.
        if self.firstrun:
            lock = Lock(self.lock_path)

            try:
                lock.open()

                if not os.path.exists(self.base_path):
                    self.build_environment()

                self.refresh_environment()

                # We only refresh the base environment once, so
                # set this on the class to make sure any other fixtures pick it up
                FakeChroot.firstrun = False
            except Locked:
                lock.wait()
            else:
                lock.close()

        # Each fixture gets its own directory. In theory this allows us to run
        # tests in parallel...

        # Clone the base-image - we use 'cp -al' because we won't the clone to
        # be made out of hardlinks.
        subprocess.check_call(["cp", "-al", self.base_path, self.chroot_path])

        # This is the same delightful incantation used in cow-shell to setup an
        # .ilist file for our fakechroot.
        subprocess.check_call([
            "cowdancer-ilistcreate",
            self.ilist_path,
            "find . -xdev \( -type l -o -type f \) -a -links +1 -print0 | xargs -0 stat --format '%d %i '",
            ], cwd=self.chroot_path)

        # This is really annoying. Setuptools doesnt preserve permissions. So booo.
        overlay_src = os.path.join(os.path.dirname(__file__), "overlay")
        if not os.path.exists(self.overlay_dir):
            os.mkdir(self.overlay_dir)
        for bin in os.listdir(overlay_src):
            src = os.path.join(overlay_src, bin)
            dst = os.path.join(self.overlay_dir, bin)
            shutil.copyfile(src, dst)
            os.chmod(dst, 0o755)

    def run_commands(self, commands):
        for command in commands:
            command = command % dict(base_image=self.base_path, distro=self.distro)
            p = subprocess.Popen(shlex.split(command))
            if p.wait():
                raise SystemExit("Command failed")

    def build_environment(self):
        commands = [
            "fakeroot fakechroot debootstrap --variant=fakechroot --include=subversion,git-core,python-setuptools,python-dateutil,ubuntu-keyring,gpgv,python-dev,build-essential %(distro)s %(base_image)s",
            "fakeroot fakechroot /usr/sbin/chroot %(base_image)s apt-get update",
            ]

        self.run_commands(commands)

        # On newer installations /var/run is now a symlink to /run
        # This breaks our fakechrootage so don't do it
        if os.path.islink(os.path.join(self.base_path, "var", "run")):
            os.unlink(os.path.join(self.base_path, "var", "run"))
            os.mkdir(os.path.join(self.base_path, "var", "run"))

    def refresh_environment(self):
        # Ths hook lets subclasses do stuff to the fakechroot base image once per test suite invocation
        pass

    def get_session(self):
        if self.fakerootkey:
            return self.fakerootkey

        if os.path.exists(self.faked_state_path):
            state = open(self.faked_state_path, "rb").read()
        else:
            p = subprocess.Popen(['faked-sysv'], stdout=subprocess.PIPE)
            state, stderr = p.communicate()
            with open(self.faked_state_path, "wb") as fp:
                fp.write(state)

        self.fakerootkey, self.faked = state.decode().split(":")

        return self.fakerootkey

    def write_temporary_file(self, contents):
        f = tempfile.NamedTemporaryFile(dir=os.path.join(self.chroot_path, 'tmp'), delete=False)
        f.write(contents)
        f.close()
        return f.name, "/tmp/" + os.path.realpath(f.name).split("/")[-1]

    def get_env(self):
        self._assert_supported()

        currentdir = os.path.dirname(__file__)

        env = {}

        path = os.path.realpath(os.path.join(self.chroot_path, "..", ".."))

        env['FAKECHROOT'] = 'true'
        env['FAKECHROOT_EXCLUDE_PATH'] = ":".join([
            '/dev', '/proc', '/sys', path,
            ])
        env['FAKECHROOT_CMD_SUBST'] = ":".join([
            '/usr/sbin/chroot=/usr/sbin/chroot.fakechroot',
            '/sbin/ldconfig=/bin/true',
            '/usr/bin/ischroot=/bin/true',
            '/usr/bin/ldd=/usr/bin/ldd.fakechroot',
            '/usr/bin/sudo=%s' % os.path.join(self.overlay_dir, "sudo"),
            '/usr/bin/env=%s' % os.path.join(self.overlay_dir, "env"),
            ])
        env['FAKECHROOT_BASE'] = self.chroot_path

        if "FAKECHROOT_DEBUG" in os.environ:
            env['FAKECHROOT_DEBUG'] = 'true'

        # Set up fakeroot stuff
        env['FAKEROOTKEY'] = self.get_session()

        # Cowdancer stuff
        env['COWDANCER_ILISTFILE'] = self.ilist_path
        env['COWDANCER_REUSE'] = 'yes'

        # Meh, we inherit the invoking users environment - LAME.
        env['HOME'] = '/root'
        env['PWD'] = '/'
        env['LOGNAME'] = 'root'
        env['USERNAME'] = 'root'
        env['USER'] = 'root'

        LD_LIBRARY_PATH = []
        for path in ("/usr/lib/fakechroot", "/usr/lib64/fakechroot", "/usr/lib32/fakechroot", ):
            if os.path.exists(path):
                LD_LIBRARY_PATH.append(path)
        LD_LIBRARY_PATH.extend(glob.glob("/usr/lib/*/fakechroot"))

        for path in ("/usr/lib/libfakeroot", ):
            if os.path.exists(path):
                LD_LIBRARY_PATH.append(path)
        LD_LIBRARY_PATH.extend(glob.glob("/usr/lib/*/libfakeroot"))

        # Whether or not to use system libs depends on te presence of the next line
        if True:
            LD_LIBRARY_PATH.append("/usr/lib")
            LD_LIBRARY_PATH.append("/lib")

        LD_LIBRARY_PATH.append(os.path.join(self.chroot_path, "usr", "lib"))
        LD_LIBRARY_PATH.append(os.path.join(self.chroot_path, "lib"))

        env['LD_LIBRARY_PATH'] = ":".join(LD_LIBRARY_PATH)
        env['LD_PRELOAD'] = "libfakechroot.so libfakeroot-sysv.so /usr/lib/cowdancer/libcowdancer.so"
        return env

    def call(self, command):
        p = subprocess.Popen(command, cwd=self.chroot_path, env=self.get_env(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout, stderr = p.communicate()
        return p.returncode

    def exists(self, path):
        return os.path.exists(self._enpathinate(path))

    def isdir(self, path):
        return os.path.isdir(self._enpathinate(path))

    def isfile(self, path):
        return os.path.isfile(self._enpathinate(path))

    def islink(self, path):
        return os.path.islink(self._enpathinate(path))

    def lexists(self, path):
        return os.path.lexists(self._enpathinate(path))

    def get(self, path):
        return self.open(path).read()

    def put(self, path, contents, chmod=0o644):
        self.open(path, 'w').write(contents)

    def makedirs(self, path):
        os.makedirs(self._enpathinate(path))

    def unlink(self, path):
        os.unlink(self._enpathinate(path))

    def check_call(self, command):
        p = subprocess.Popen(command, cwd=self.chroot_path, env=self.get_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        return p.returncode, stdout, stderr

    def stat(self, path):
        returncode, stdout, stderr = self.check_call(["stat", "-L", "-t", path])
        if returncode != 0:
            raise OSError
        data = stdout.decode().split(" ")
        return stat_result(
            int(data[3], 16),  # st_mode
            int(data[8]),  # st_ino
            int(data[7], 16),  # st_dev
            int(data[9]),  # st_nlink
            int(data[4]),  # st_uid
            int(data[5]),  # st_gid
            int(data[1]),  # st_size
            int(data[11]),  # st_atime
            int(data[12]),  # st_mtime
            int(data[13]),  # st_ctime
        )

    def lstat(self, path):
        returncode, stdout, stderr = self.check_call(["stat", "-t", path])
        if returncode != 0:
            raise OSError
        data = stdout.decode().split(" ")
        return stat_result(
            int(data[3], 16),  # st_mode
            int(data[8]),  # st_ino
            int(data[7], 16),  # st_dev
            int(data[9]),  # st_nlink
            int(data[4]),  # st_uid
            int(data[5]),  # st_gid
            int(data[1]),  # st_size
            int(data[11]),  # st_atime
            int(data[12]),  # st_mtime
            int(data[13]),  # st_ctime
        )

    def mkdir(self, path):
        os.mkdir(self._enpathinate(path))

    def open(self, path, mode='r'):
        return open(self._enpathinate(path), mode)

    def touch(self, path):
        if not self.exists(path):
            with self.open(path, "w") as fp:
                fp.write("")

    def chmod(self, path, mode):
        self.call(["chmod", "%04o" % mode, path])

    def readlink(self, path):
        relpath = os.path.relpath(os.readlink(self._enpathinate(path)), self.chroot_path)
        for x in (".", "/"):
            if relpath.startswith(x):
                relpath = relpath[1:]
        return "/" + relpath

    def symlink(self, source, dest):
        os.symlink(self._enpathinate(source), self._enpathinate(dest))

    def _enpathinate(self, path):
        return os.path.join(self.chroot_path, *path.split(os.path.sep))

    def get_user(self, user):
        users_list = open(self._enpathinate("/etc/passwd")).read().splitlines()
        users = dict(u.split(":", 1) for u in users_list)
        return users[user].split(":")

    def get_group(self, group):
        # Returns a tuple of group info if the group exists, or raises KeyError if it does not
        groups_list = open(self._enpathinate("/etc/group")).read().splitlines()
        groups = dict(g.split(":", 1) for g in groups_list)
        return groups[group].split(":")

    def cleanup_session(self):
        # Another fakechroot instance might have created a fakeroot session
        if not self.faked and os.path.exists(self.faked_state_path):
            self.get_session()

        if self.faked:
            os.kill(int(self.faked.strip()), signal.SIGTERM)
            self.faked = None

    def destroy(self):
        self.cleanup_session()
        if os.path.exists(self.faked_state_path):
            os.unlink(self.faked_state_path)
        if os.path.exists(self.ilist_path):
            os.unlink(self.ilist_path)
        # shutil.rmtree has disappeared up itself deleting large base images
        if os.path.exists(self.chroot_path):
            subprocess.check_call(["rm", "-rf", self.chroot_path])
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
