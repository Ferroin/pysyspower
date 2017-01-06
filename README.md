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

### Functionality ###
As of right now, the following functions are at least partially
implemented on at least one supported platform:
 * Shutdown
 * Reboot
 * Suspend to disk
 * Suspend to RAM

The following functions are planned to be implemented:
 * Lock screen/activate screensaver
 * Log out

The following methods of privilege elevation are supported for non-root
users on UNIX-like systems:
 * sudo
 * doas
 * pkexec (PolicyKit, requires special setup and is pretty much completely
   untested)

Session manager integration is offered for the following desktop
environments on (most) UNIX-like systems:
 * GNOME (both 2 and 3)
 * MATE
 * Cinnamon
 * XFCE4

### Platform support ###
###### Linux ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to disk/hibernate
 * Suspend to RAM

Session management integration is incomplete, we currently don't have
support for KDE or LXDE/LXQT.

###### BSD ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to RAM (untested, probably only works on FreeBSD)

Session management integration is incomplete, we currently don't have
support for KDE or LXDE/LXQT.

Suspend to RAM support for BSD is completely untested, it may or may
not work, and the method used is based on FreeBSD documentation, so it
may or may not work on other BSD systems.

###### macOS / OS X ######
Supports the following functionality:
 * Shutdown
 * Reboot
 * Suspend to RAM

Current support is very rudimentary, requires special setup, and lacks
proper desktop integration.  I hope to eventually have proper support,
but it's not a priority for me since I don't use OS X myself.

I'm about 90% certain that OS X actually does a hybrid sleep when you
tell it to suspend.  It's impossible to be 100% certain though because
of the tight firmware integration of the OS and the inability to verify
if anything is powered.  However, because the resume behavior is
consistent in all cases I've seen with suspend to RAM performance for
other systems, I'm listing it as such since it fills a similar usage.

###### Other UNIX-like systems ######
Supports the following functionality:
 * Shutdown
 * Reboot

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

On current versions of Windows (8 and newer), there's no practical way
that I know of to get the system to actually suspend to RAM  without
using compiled code (which I absolutely want to avoid).  If someone can
find a way that doesn't involve compiled code or extra dependencies,
send me a (tested) patch, and I'll be happy to include it.

### TODO ###
 * Implement missing functionality, and document what can't be implemented.
 * Get proper installation tools set up.
 * Add support for more privilege elevation tools on UNIX.
