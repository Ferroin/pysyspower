#!/usr/bin/env python3
'''syspower: A platform agnostic library for power state management.

   For any given operation, we first determine the platform type, and
   then try to use some extra stuff to narrow down what specific methods
   might work on this system for the requested operation (mostly needed
   on Linux), and then finally try those methods in a priority order.

   CONSOLE_AUTH_TYPES is a list of password-less console based prievelge
   escalation methods we will iterate through when trying to performa
   an operation.

   Copyright (c) 2016, Austin S. Hemmelgarn
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
   ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
   LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
   SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
   INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
   CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
   POSSIBILITY OF SUCH DAMAGE.'''

import sys
import os
import subprocess

CONSOLE_AUTH_TYPES = [
    ['sudo', '-n'],
    ['doas', '-n'],
    ['pkexec']
]


class SyspowerException(Exception):
    '''Base class for other errors.'''

class UnsupportedOperationError(SyspowerException):
    '''Raised when a particular operation is not supported on the current platform.

       This is essentially the same as returning NotImplemented, we just
       use a different name to be more clear.'''

class NoWorkingMethodError(SyspowerException):
    '''Raised when a method for the operation can't be found for the platform.

       In essence, if you get this, we technically support the platform,
       but none of the things we try to perform the requested operation
       on that platform worked.'''


def _try_commands(commands):
    '''Try to get at least one command to run.

       This first checks if we're root, and if so just tries all the
       commands and fails if none work.  Then it tries each of the
       privelege elevation methods, and finally just tries every command
       by itself.'''
    if os.geteuid() == 0:
        for command in commands:
            try:
                status = subprocess.check_call(command, shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
        return False
    for prefix in CONSOLE_AUTH_TYPES:
        for i in range(0, len(commands)):
            try:
                status = subprocess.check_call(prefix + commands[i], shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
    for command in commands:
        try:
            status = subprocess.check_call(command, shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
    return False

def _get_shutdown_poweroff_opts():
    '''Figure out what to pass to /sbin/shutdwon to power-off

       This is needed because options are inconsistent between modern
       Linux, old Linux, SVR4 derived systems, BSD derived systems,
       and Solaris derived systems.'''
    if os.name == 'posix' and sys.platform.startswith('darwin'):
        # Assume we're on OS X, which wants no arguments for poweroff
        return ''
    try:
        shutdownhelp = subprocess.check_output(['shutdown', '--help'], shell=True)
    except subprocess.SubprocessError:
        # Either shutdown doesn't support --help (which means it's
        # ancient), or doesn't exist.  In either case, assume old
        # Linux/SVR4 options, which should work on most systems (at
        # least to bring the system down.
        return '-h'
    if shutdownhelp.find(b'-p') != -1:
        # This covers BSD style shutdown.
        return '-p'
    elif shutdownhelp.find(b'-P') != -1:
        # This covers older Linux style shutdown.
        return '-hP'
    else:
        # This covers most other stuff.
        return ''

def _generic_unix_shutdown():
    '''Internal function that tries methods that are generic to most UNIX systems.'''
    cmdlist = [
        ['systemctl', 'poweroff'],
        ['shutdown', _get_shutdown_poweroff_opts(), 'now'],
        ['poweroff'],
        ['teliniti', '0'],
        ['halt']
    ]
    return _try_commands(cmdlist)

def _unix_gui_shutdown():
    '''Try all the different session management shutdown commands we know about.

       This currently works with:
        * Cinnamon
        * GNOME 2 and 3
        * MATE
        * XFCE 4
        * KDE 4 and 5

       I plan to try to get it working with the following as well:
        * LXDE/LXQT

       The following might be supported if I can figure out how to do it:
        * E17
        * Enlightenment '''
    searchpath = os.get_exec_path()
    cmds = [
        ['gnome-session-quit', '--power-off', '--force'],
        ['cinnamon-session-quit', '--power-off', '--force'],
        ['mate-session-quit', '--power-off', '--force'],
        ['xfce4-session-logout', '--halt'],
        ['qdbus', 'org.kde.ksmserver', '/KSMServer', 'org.kde.KSMServerInterface.logout', '0', '2', '2']
    ]
    for cmd in cmds:
        for search in searchpath:
            if os.access(os.path.join(search, cmd[0]), os.X_OK):
                try:
                    status = subprocess.check_call(cmd, shell=True)
                    if status == 0:
                        return True
                except subprocess.SubprocessError:
                    pass
    return False

def _generic_unix_reboot():
    '''Internal function that tries methods that are generic to most UNIX systems.'''
    cmdlist = [
        ['systemctl', 'reboot'],
        ['shutdown', '-r', 'now'],
        ['reboot'],
        ['telinit', '6']
    ]
    return _try_commands(cmdlist)

def _linux_suspend():
    '''Internal function to try different suspend methods on Linux.

       At the moment, this has zero session management integration.'''
    cmdlist = [
        ['systemctl', 'suspend'],
        ['pm-suspend'],
        ['s2ram']
    ]
    if _try_commands(cmdlist):
        return True
    try:
        # This only works if we're root, and the other methods are much
        # safer for userspace, but if we're root this is certain to work
        # (assuming the hardware and driver work correctly.
        support = subprocess.check_output(['cat', '/sys/power/state'], shell=True)
        if support.find(b'mem') != -1:
            with open('/sys/power/state', 'wb') as state:
                if state.write('mem'):
                    return True
    except (subprocess.SubprocessError, IOError, OSError):
        pass
    return False

def _linux_hibernate():
    '''Internal function to try different hibernate methods on Linux.

       At the moment, this has zero session management integration.'''
    cmdlist = [
        ['systemctl', 'hibernate'],
        ['pm-hibernate'],
        ['s2disk']
    ]
    if _try_commands(cmdlist):
        return True
    try:
        # This only works if we're root, and the other methods are much
        # safer for userspace, but if we're root this is certain to work
        # (assuming the hardware and driver work correctly.
        support = subprocess.check_output(['cat', '/sys/power/state'], shell=True)
        if support.find(b'disk') != -1:
            with open('/sys/power/state', 'wb') as state:
                if state.write('disk'):
                    return True
    except (subprocess.SubprocessError, IOError, OSError):
        pass
    return False

def _linux_hybrid_sleep():
    '''Internal function to try different hybrid-sleep methods on Linux.

       Does not currently have session management integration (and
       may never, as no session managers I know of support this
       themselves).'''
    cmdlist = [
        ['systemctl', 'hybrid-sleep'],
        ['pm-suspend-hybrid'],
        ['s2both']
    ]
    if _try_commands(cmdlist):
        return True
    try:
        # This only works if we're root, and the other methods are much
        # safer for userspace, but if we're root this is certain to work
        # (assuming the hardware and driver work correctly.
        support = subprocess.check_output(['cat', '/sys/power/state'], shell=True)
        if support.find(b'hybrid') != -1:
            with open('/sys/power/state', 'wb') as state:
                if state.write('hybrid'):
                    return True
    except (subprocess.SubprocessError, IOError, OSError):
        pass
    return False

def _unix_gui_logout():
    '''Try to log out of whatever graphical session we're in.

       This currently works with:
        * Cinnamon
        * GNOME 2 and 3
        * MATE
        * XFCE 4
        * KDE 4 and 5'''
    searchpath = os.get_exec_path()
    cmds = [
        ['gnome-session-quit', '--logout', '--force'],
        ['cinnamon-session-quit', '--logout', '--force'],
        ['mate-session-quit', '--logout', '--force'],
        ['xfce4-session-logout', '--logout'],
        ['qdbus', 'org.kde.ksmserver', '/KSMServer', 'org.kde.KSMServerInterface.logout', '0', '2', '3'],
    ]
    for cmd in cmds:
        for search in searchpath:
            if os.access(os.path.join(search, cmd[0]), os.X_OK):
                try:
                    status = subprocess.check_call(cmd, shell=True)
                    if status == 0:
                        return True
                except subprocess.SubprocessError:
                    pass
    return False


def shutdown():
    '''Initiate a system shutdown.

       In most cases, this will either never return (if the shutdown
       is immediate, or the method blocks until the shutdown occurs,
       then this wont' return) or raise an error (if we can't find a
       method that works or the platform is unsupported).  In the event
       that we do return, we'll return true if we think things worked
       (which may not mean that they actually did work).'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            if _unix_gui_shutdown():
                return True
            if _generic_unix_shutdown():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('darwin'):
            if _generic_unix_shutdown():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('SunOS') or sys.platform.startswith('solaris'):
            # Newer versions of Solaris have a wierd shutdown command
            # that behaves like telinit with confirmation, try that first
            # before trying the generic UNIX shutdown stuff.
            try:
                status = subprocess.check_call(['shutdown', '-y', '-i 5', '5'], shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
            if _generic_unix_shutdown():
                return True
            raise NoWorkingMethodError
        if _unix_gui_shutdown():
            return True
        if _generic_unix_shutdown():
            return True
        raise NoWorkingMethodError
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/s'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethodError
    else:
        raise UnsupportedOperationError

def reboot():
    '''Initiate a system reboot.

       In most cases, this will either never return (if the shutdown
       is immediate, or the method blocks until the shutdown occurs,
       then this wont' return) or raise an error (if we can't find a
       method that works or the platform is unsupported).  In the event
       that we do return, we'll return true if we think things worked
       (which may not mean that they actually did work).'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            if _generic_unix_reboot():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('darwin'):
            if _generic_unix_reboot():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('SunOS') or sys.platform.startswith('solaris'):
            # Newer versions of Solaris have a wierd shutdown command
            # that behaves like telinit with confirmation, try that first
            # before trying the generic UNIX reboot stuff.
            try:
                status = subprocess.check_call(['shutdown', '-y', '-i 6', '6'], shell=True)
            except subprocess.SubprocessError:
                pass
            if status == 0:
                return True
            if _generic_unix_reboot():
                return True
            raise NoWorkingMethodError
        if _generic_unix_reboot():
            return True
        raise NoWorkingMethodError
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/r'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethodError
    else:
        raise UnsupportedOperationError

def suspend():
    '''Suspend to RAM.

       This is equivalent to an ACPI S3 state on most systems, but may
       be different depending on the platform.

       Depending on the platform and method, this may return before the
       system has actually suspended to RAM, or it may not return until
       after the system next wakes up.  In either case, if there was no
       error, it will return True.'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            if _linux_suspend():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('darwin'):
            try:
                status = subprocess.check_call(['shutdown', '-s', 'now'], shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
            raise NoWorkingMethodError
        elif sys.platform.startswith('freebsd'):
            try:
                status = subprocess.check_call(['acpiconf', '-s', '3'], shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
            raise NoWorkingMethodError
        else:
            raise UnsupportedOperationError
    elif os.name == 'nt':
        raise UnsupportedOperationError
    else:
        raise UnsupportedOperationError

def hibernate():
    '''Hibernate/Suspend to disk.

       This is an OS mediated operation, not a firmware mediated one.'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            if _linux_hibernate():
                return True
            raise NoWorkingMethodError
        elif sys.platform.startswith('darwin'):
            raise UnsupportedOperationError
        elif sys.platform.find('BSD') != -1:
            try:
                status = subprocess.check_call(['pm-hibernate'], shell=True)
                if status == 0:
                    return True
            except subprocess.SubprocessError:
                pass
            raise NoWorkingMethodError
        else:
            raise UnsupportedOperationError
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/h'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethodError
    else:
        raise UnsupportedOperationError

def hybrid_sleep():
    '''Enter hybrid sleep.

       Hybrid sleep consists of doing everything needed for hibernation,
       except instead of powering off you enter ACPI S3 (suspend to
       RAM) state.  In most cases, you can start back up just as fast
       as from regular uspend, but if have a power failure, you don't
       lose anything (and start up as if from hibernation).

       Note that this is not the same as Windows 'Fast Startup', which
       is sometimes called a hybrid shutdown or hybrid sleep.'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            if _linux_hybrid_sleep():
                return True
            raise NoWorkingMethodError
        else:
            raise UnsupportedOperationError
    else:
        raise UnsupportedOperationError

def logout():
    '''Log out of the current session.

       This only works when called from inside a desktop session as the
       user who  owns the session.'''
    if os.name == 'posix':
        if sys.platform.startswith('darwin'):
            raise UnsupportedOperationError
        else:
            if _unix_gui_logout():
                return True
            raise NoWorkingMethodError
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/l'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethodError
    else:
        raise UnsupportedOperationError
