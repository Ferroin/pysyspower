# syspower #
syspower is a Python 3.x library for (reasonably) cross platform control
of system power states.  It abstracts away most of the platform specific
stuff involving thing such as shutting down the system, rebooting,
and similar tasks.  It originated because I couldn't find any similar
libraries and needed this functionality for one of my other projects.

syspower is licensed under a 2 clause BSD license, check LICENSE or the
docstring for the exact details.

### Functionality ###
As of right now, the following functions are at least partially
implemented on at least one supported platform:
 * Shutdown
 * Reboot

The following functions are planned to be implemented:
 * Lock screen/activate screensaver
 * Log out
 * Suspend to RAM
 * Suspend to disk

The following methods of privilege elevation are supported for non-root
users on UNIX-like systems:
 * sudo
 * doas
 * pkexec (PolicyKit, requires special setup and is pretty much completely
   untested)

### Platform support ###
###### Linux ######
Supports the following functionality:
 * Shutdown
 * Reboot

Session management integration is currently not implemented, but is
planned.

###### BSD ######
Supports the following functionality:
 * Shutdown
 * Reboot

As with Linux, session management integration is not currently
implemented, but support is planned.

###### macOS / OS X ######
Supports the following functionality:
 * Shutdown
 * Reboot

Current support is very rudimentary and lacks proper desktop integration.
I hope to eventually have proper support, but it's not a priority for
me since I don't use OS X myself.

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

### TODO ###
 * Implement missing functionality, and document what can't be implemented.
 * Get proper installation tools set up.
 * Add support for more privilege elevation tools on UNIX.
