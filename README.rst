=================
FakeChrootFixture
=================

This package provides a fixtures_ compatible fixture for building and
executing integration tests in a copy-on-write chroot environment without
requiring the tests to be run as root.

In order to use it you will need fakeroot_, fakechroot_ and cowdancer_.

This code was extracted and refactored from the test harness within Yaybu_.

.. _fixtures: http://pypi.python.org/pypi/fixtures
.. _yaybu: http://yaybu.com
.. _fakechroot: https://github.com/fakechroot/fakechroot/wiki
.. _fakeroot: http://fakeroot.alioth.debian.org
.. _cowdancer: http://www.netfort.gr.jp/~dancer/software/cowdancer.html.en


So what does it do then?
========================

The first test to use the fixture will create (or refresh) a chroot. We use
fakechroot magic to do this in userspace without root. Each test is then run in
a cheap copy of this chroot. So each test gets its own clean (and fresh) chroot.

This chroot is perfect for testing. You can perform actions against a seeming
complete system and at the same time poke and prod at it from outside.


How do I use it?
================

Something like this::

    import unittest2
    from fakechroot import TestCase

    class TestInAChroot(TestCase):
        def test_true(self):
            retval = self.chroot.call(["/bin/true"])
            self.failUnlessEqual(retval, 0)


What other cool API's are there?
================================

The fixture object has a bunch of API helpers on it so you can write your tests
as though they were in the chroot. All the calls below will take a path in the
chroot (such as ``/foo``) and operate on the fully expanded path (which might
be ``/home/john/Projects/myproject/tmp2234a/foo``).

These were added as Yaybu needed them - patches for more are welcome.

``FakeChrootFixture.call``
    Executes a command inside the chroot with the appropriate LD_PRELOAD
    setup.

``FakeChrootFixture.exists``
    Returns ``True`` if a path inside the chroot exists.

``FakeChrootFixture.isdir``
    Returns ``True`` is a path in the chroot is a directory.

``FakeChrootFixture.mkdir``
    Creates a directory inside the chroot.

``FakeChrootFixture.open``
    Returns a file inside the chroot for read or write operations.

``FakeChrootFixture.touch``
    Runs the ``touch`` binary inside the chroot.
 
``FakeChrootFixture.chmod``
    Runs the ``chmod`` binary inside the chroot. We can't directly use
    ``os.chmod`` as it doesn't notify ``faked`` about the change.

``FakeChrootFixture.readlink``
    Grabs the value of a symlink. As this can contain the entire path of the
    chroot we strip off the chroot path.

``FakeChrootFixture.symlink``
    Actually creates a symlink within the chroot.

``FakeChrootFixture.stat``
    Performs an ``os.stat`` on the path.


How does it work?
=================

This works through a trio of ``LD_PRELOAD`` libs that essentially monkey patch
the chroot to think they have more privileged access than they do.

The ``fakeroot`` package is used to fool your code into thinking it is root and
that changes it is making as root (such as ``chmod``, for example) are taking
effect. A special ``faked`` daemon is used to coordinate this between
processes.

The ``fakechroot`` package is used to fool your code into thinking that the
``chroot`` syscall worked. This means that any code perform file operations is
tricked at a syscall level into acting on ``~/yourchroot/tmp/foo`` when it
innocently thinks it just touched ``/tmp/foo``.

The ``cowdancer`` package is what provides copy-on-write in userspace. The only
requirement is a filesystem that supports hard links. You create a copy on your
base image with ``cp -al``. This creates a farm of hardlinks. The ``cowdancer``
patches then force any changes that would have been written to the base image
to be written into a new file (thus breaking the hard link).


What are the limitations?
=========================

Your code only thinks it has root. So you can't bind port 80 or anything like
that.

Right now we only actively support Ubuntu. In particular, we are only actively
testing with Lucid and Precise. Whilst other Unixes may be supported in future
support for OS X is unfortunately unlikely (there is nothing like debootstrap)
and Windows doesn't have the concept of chroots.

There is some overhead to using a system like this. We have tuned some of this
away (for example, we setup the ``LD_PRELOAD`` stuff by hand to shave 3 process
invocations per ``.call()``), but you are still introducing a fair bit of
indirection. You won't be running hundreds of test cases per second.

All three libraries on their own are clever hacks. They are heavily used in
Debian, but they likely still have bugs. And when combined together those bugs
are likely magnified. This fixture will let you run some tests that might have
previously required root as a normal user, thus avoid running the code you just
utterly broke as root. But that's still enough power to wipe ``~``!


What are the alternatives?
==========================

Running your code in a VM is the best test, but even with snapshots running
each test in a clean environment would be a pain.

There have been lots of advances in Kernel namespacing. LXC could be a suitable
alternative - it depends on your use case.

