# pysyspower #
pysyspower is a Python 3.1+ library for (reasonably) cross platform
control of system power states and related session management.
It abstracts away most of the platform specific stuff involving
thing such as shutting down the system, rebooting, and similar tasks.
It originated because I couldn't find any similar libraries and needed
this functionality for one of my other projects.

pysyspower is licensed under a 2 clause BSD license, check LICENSE or the
docstring for the exact details.

pysyspower needs at minimum Python 3.1, but has no other dependencies
beyond the standard library and the basic tools already found on most
systems.

For info on how this all actually works, check ./INTERNALS.md

### Functionality ###
As of right now, the following functions are at least partially
implemented on at least one supported platform:
 * Shutdown
 * Reboot
 * Suspend to disk
 * Suspend to RAM
 * Hybrid suspend (prepares everything for suspend to disk, then suspends
   to RAM).
 * Log out of the current GUI session

The following functions are planned to be implemented:
 * Lock screen/activate screensaver

The following methods of privilege elevation are supported for non-root
users on UNIX-like systems:
 * sudo
 * doas
 * pkexec (PolicyKit, requires special setup and is pretty much completely
   untested)

Session manager integration supporting shutdown, reboot, and logout
is offered for the following desktop environments on (most) UNIX-like
systems:
 * GNOME (2.10 and newer)
 * MATE
 * Cinnamon
 * XFCE (4.x series)
 * KDE (4.0 and newer)

### Platform support ###
###### Linux ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to disk/hibernate
 * Suspend to RAM
 * Hybrid suspend
 * Log out of the current GUI session

###### BSD ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to RAM (FreeBSD only)
 * Log out of the current GUI session

###### macOS / OS X ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to RAM

Current support is very rudimentary, requires special setup, and lacks
proper desktop integration.  I hope to eventually have proper support,
but it's not a priority for me since I don't use OS X myself.

I'm about 90% certain that OS X actually does a hybrid sleep when you
tell it to suspend.  I don't have the hardware (or time) to verify this,
but most of the documentation seems to indicate that it's just a suspend,
so I'm putting it here.  If I can verify that this is in fact a hybrid
sleep, then I'll move the support into that function instead.

###### Other UNIX-like systems ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Log out of the current GUI session (only for supported desktop
   environments)

In general, this stuff _should_ work on most other UNIX-like systems,
but I can't make any guarantees because I've only based this code on
documentation and personal experience, and have nothing to test it on.
If you have a system to test on and come across a bug, don't hesitate
to open an issue, and I'll try to fix it, but even then I can't make
any guarantees.

Some systems may halt instead of powering off.  This is largely
unavoidable on many such systems because they have limited functionality
in the standard tools.

Special handling is done on Solaris because some versions have a weird
version of shutdown that doesn't work at all like any of the standard UNIX
'shutdown' tool.

###### Windows ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to disk/hibernate
 * Log out of the current GUI session

On current versions of Windows (8 and newer), there's no practical way
that I know of to get the system to actually suspend to RAM  without
using compiled code (which I absolutely want to avoid).  If someone can
find a way that doesn't involve compiled code or extra dependencies,
send me a (tested) patch, and I'll be happy to include it.

### TODO ###
 * Implement missing functionality, and document what can't be implemented.
 * Get proper installation tools set up.
 * Add support for more privilege elevation tools on UNIX.
 * Wire up code so syspower can be used as a cross-platform shutdown
   script (useful for testing).

### API ###
The external API is actually remarkably simple.  There is one function
for each supported operation:
 * shutdown()
 * reboot()
 * suspend()
 * hibernate()
 * hybrid\_sleep()
 * logout()

They all work relatively similarly, determining first the type of
system, and then running through known methods of effecting the requested
operation on that system.  None of them take any argument, and most are
likely to never return.

If the requested operation isn't supported, you'll get a
UnsupportedOperationError.  This means that either the current system
just doesn't support that operation, or that I know of no way to implement
that operation on this system without needing extra dependencies.

If syspower can't find a way to perform the requested operation (for
example, you're a non-root user on UNIX and don't have anything set up
that would let you run privileged commands without a password), then
you'll get a NoWorkingMethodError.

Both exception classes are subtypes of SyspowerException, so you can
use that to catch either type.
