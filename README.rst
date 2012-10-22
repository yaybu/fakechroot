=================
FakeChrootFixture
=================

This package providers a ``fixtures`` compatible fixture for building and
executing integration tests in a copy-on-write chroot environment without
requiring the tests to be run as root.

This code was extracted and refactored from the test harness within `Yaybu
<http://yaybu.com>`_.


How do I use it?
================

There are 2 basic patterns to use this fixture. First of all, you can create a
subclass of the ``fixtures.TestWithFixtures`` class::

    import fixtures
    import fakechroot

    class TestInAChroot(fixtures.TestWithFixtures):
        def setUp(self):
            self.chroot = self.useFixture(fakechroot.FakeChrootFixture())

        def test_true(self):
            retval = self.chroot.call(["/bin/true"])
            self.failUnlessEqual(retval, 0)

Fixtures also implement the context protocol so you could also::

    import fakechroot

    class TestInAChroot(unittest.TestCase):
        def test_true(self):
            with fakechroot.FakeChrootFixture() as chroot:
                retval = chroot.call(["/bin/true"])
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


