# pysyspower internal operational documentation #
Python code is generally supposed to be self-evident in how it works.
In this case, I feel that all of the actual Python code itself in syspower
is, but the sum total of the Python code is figuring out what system we're
on and trying all the possible methods for the operation on that system.
This means that there are quite a few 'magic' strings in the code that
aren't self-evident to people who don't use the systems in question,
and this file will try to explain those as well as possible, as well as
explaining a couple of design choices.

### Why we don't support shutdown times ###
This is actually a useful feature that I originally intended to include.
There are however a couple of issues involved in implementing it that
made me change my mind regarding it:
1. Not all methods on all systems support specifying a time for the
shutdown or reboot.  On UNIX for example, only the 'shutdown' command
supports this, poweroff, telinit, halt, and all the session manager
interfaces that I know of don't completely support it.  Because of this,
implementing this feature properly would require adding a custom timeout
handler in the library itself, which brings it's own issues (some of
the methods can only be checked by actually trying them).
2. Some systems use drastically different formats for the time specifier.
In particular, Windows and Solaris shutdown commands use seconds specified
with an option, while almost everything else uses minutes specified as
a positional parameter.

### Why syspower isn't object oriented ###
This is actually a common question about a lot of code I write, and
I'll give the same answer here I do elsewhere:
Object-oriented code is usually over-engineered for any particular
application, and as a result harder to maintain and slower than procdeural
or functional code.

To be more specific, the functionality provided by syspower is not
something that even makes sense for object-oriented code.  The obvious
approach (and the only reasonable one) for objec-orienting this would
be to have an ABC for operation methods, but doing that would make the
code much more complex than it actually needs to be (you absolutely do
not need an object to iterate over a list of possible commands and try
each one).  For comparison, I actually did take the time to write out
an OO version of syspower, it was more than 4 times as long and had
almost twice the overhead of the procedural version I've published,
wich no net benefit.

### Windows support ###
All of the operations we support on Windows are multiplexed through
`shutdown.exe`.  This particular command has been around in some form
with mostly the same command-line switches since before NT 4.0, works in
both cmd.exe and PowerShell, and transparently handles the authentication
required for the power-management operations it supports.  There are of
course other options in PowerShell (Stop-Computer for example powers off
the system), but they are not as easy to use (some require being called
from an admin shell), don't handle GUI seessions correctly on older
versions of Windows, and aren't portable to older versions of PowerShell.

### Privilege elevation support on UNIX-like systems ###
As of right now, we support three methods of privilege elevation on
UNIX-like systems:
1. sudo: This is by far the most common method.  Sudo originated as a
replacement for su (to deal with the limitations inherent in that design),
is found on almost every Linux distribution as part of the standard
install, and can be found on quite a few other UNIX systems as well.
2. doas: This is a sudo-like tool originally from OpenBSD.  It's not as
common, but it's also easy to support and easy to set up.
3. pkexec: This is an interface to PolicyKit, which is a framework common
on many Linux desktop systems.  It's much more complicated to configure
than the other options, and has other usage limitations (needs a running
session instance of DBus), but it's otherwise not hard to support.

It's not hard to add support for a new privilege elevation tool, it just
needs to have some way to support password-less elevation.

### UNIX-like support for shutdown and reboot (including OS X and Linux) ###
For UNIX-like systems, there's a bit more variance than Windows.
For shutdown and reboot, we try the following In order:
1. GUI session manager interfaces.  Doing this first ensures that any
running desktop handles things correctly if possible.  This is currently
skipped on OS X since I know nothing aobut how to make RPC's against
the session manager.
2. If we're on Solaris, try the weird shutdown command found on newer
versions.
3. If we're running as EUID=0 (root on most systems), try all the generic
methods directly and bail if none of them work.  We do this because the
privilege elevation tools usually won't work for the root user (at least,
not how we try them), and aren't needed anyway.
4. Try all the generic methods in order with each privelege elevation
method we know about.
5. Finally, try directly invoking all the generic methods (some of the
methods have their own options for access control other than just UID).

The generic methods we try for shutdown and reboot on UNIX are (in order):
1. systemctl: This is the preferred method on SystemD based systems.
It's essentially a waste of time right now on non-Linux systems, but
that may change in the future, and it's easier to just try it with
everything else.
2. shutdown: This is the preferred standard method on most UNIX systems
to handle reboot and shutdown.  However, we need special handling for
this for powering off a system because options are inconsistent across
platforms.  In particular, any of nothing (Darwin and OS X), '-p'
(most BSD systems), '-hP' (most modern Linux systems), or '-h' (most
other systems, may not actually power down the hardware) may be needed.
3. poweroff: This is a command sometimes found on UNIX-like systems to
power down the system completely.  On some systems, shutdown calls this
to do the actual power off, on others this calls shutdown, and on others
it's an alias for telinit.  This is only tried for an actual shutdown.
4. reboot: Similar to poweroff, but more universally available.
Only tried for a reboot.
5. telinit: This is a very low-level command dating back at least to the
original System V init implementation.  It is a simple tool that tells
init to switch to a particular runlevel (0 for shutdown, 6 for reboot).
This is also a rather dangerous method on many systems because it bypasses
most login management tools and gives no warnings to users, hence being
at the end of the list for reboots and second to last for shutdowns.
6. halt: This is our absolute last-ditch effort for a shutdown.  It tells
the kernel to bring down userspace (usually in an orderly fashion), shut
itself down, and then stop the processor.  It is the original system
shutdown tool from when software mediated poweroff wasn't possible.

### UNIX-like support for suspend, hibernate, and hybrid-sleep ###
For the two non-Linux cases here (suspend on OS X and FreeBSD), things
are pretty simple, there's a single option that's called, and that's it.
For Linux however, things are a bit more complicated, and we try the
following methods:
1. systemctl: Similar to shutdown, this is for SystemD based systems.
2. pm-utils: This is present on any system that uses UPower or SystemD,
so it's generally workable on any desktop box.
3. swsuspend: This is a userspace implementation of hibernate and
hybrid-sleep support that works with the kernel to implement suspend.
It is what gets used by pm-utils if it's availible.
4. Direct writes to /sys/power/state: This only works as root, and
directly invokes kerenl level support for the requested function.
We check first to see if the kernel says it supports the requested mode.
