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

CONSOLE_AUTH_TYPES = {
    'sudo -n',
    'doas -n',
    'pkexec'
}

class UnsupportedOperation(Exception):
    '''Raised when a particular operation is not supported on the current platform.

       This is essentially the same as returning NotImplemented, we just
       use a different name to be more clear.'''

class NoWorkingMethod(Exception):
    '''Raised when a method for the operation can't be found for the platform.

       In essence, if you get this, we technically support the platform,
       but none of the things we try to perform the requested operation
       on that platform worked.'''


def _try_commands(commands):
    '''Tries each command in sequence, returning True if one succeeded and False otherwise.'''
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
    '''Internal function that tries methods that are generic to most UNIX systems.

       First, we check if we're EUID 0, and if so just try calling
       shutdown directly (followed by poweroff and halt if they exist
       and shutdown fails).

       Then we try to call them in the same order using the various
       methods in CONSOLE_AUTH_TYPES.

       Third we try directly calling shutdown, poweroff, telinit 0,
       and halt in that order (some of thewse will actually work if
       we're not root).'''
    cmdlist = [
        ['shutdown', _get_shutdown_poweroff_opts(), 'now'],
        ['poweroff'],
        ['teliniti', '0'],
        ['halt']
    ]
    if os.geteuid() == 0:
        if _try_commands(cmdlist):
            return True
    for prefix in CONSOLE_AUTH_TYPES:
        tmpcmdlist = list()
        for i in range(0, len(cmdlist)):
            tmpcmdlist.append(cmdlist[i])
            tmpcmdlist[i].insert(0, prefix)
        if _try_commands(tmpcmdlist):
            return True
    if _try_commands(cmdlist):
        return True
    return False

def _generic_unix_reboot():
    '''Internal function that tries methods that are generic to most UNIX systems.

       Similar arrangement to _generic_unix_shutdown, just with
       shutdown -r, reboot, and telinit 6.'''
    cmdlist = [
        ['shutdown', '-r', 'now'],
        ['reboot'],
        ['telinit', '6']
    ]
    if os.geteuid() == 0:
        if _try_commands(cmdlist):
            return True
    for prefix in CONSOLE_AUTH_TYPES:
        tmpcmdlist = list()
        for i in range(0, len(cmdlist)):
            tmpcmdlist.append(cmdlist[i])
            tmpcmdlist[i].insert(0, prefix)
        if _try_commands(tmpcmdlist):
            return True
    if _try_commands(cmdlist):
        return True
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
            if _generic_unix_shutdown():
                return True
            raise NoWorkingMethod
        elif sys.platform.startswith('darwin'):
            if _generic_unix_shutdown():
                return True
            raise NoWorkingMethod
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
            raise NoWorkingMethod
        if _generic_unix_shutdown():
            return True
        raise NoWorkingMethod
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/s'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethod
    else:
        raise UnsupportedOperation

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
            raise NoWorkingMethod
        elif sys.platform.startswith('darwin'):
            if _generic_unix_reboot():
                return True
            raise NoWorkingMethod
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
            raise NoWorkingMethod
        if _generic_unix_reboot():
            return True
        raise NoWorkingMethod
    elif os.name == 'nt':
        try:
            status = subprocess.check_call(['shutdown', '/r'], shell=True)
            if status == 0:
                return True
        except subprocess.SubprocessError:
            pass
        raise NoWorkingMethod
    else:
        raise UnsupportedOperation

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
            raise UnsupportedOperation
        elif sys.platform.startswith('darwin'):
            raise UnsupportedOperation
        else:
            raise UnsupportedOperation
    elif os.name == 'nt':
        raise UnsupportedOperation
    else:
        raise UnsupportedOperation

def hibernate():
    '''Hibernate/Suspend to disk.

       This is an OS mediated operation, not a firmware mediated one.'''
    if os.name == 'posix':
        if sys.platform.startswith('linux'):
            raise UnsupportedOperation
        elif sys.platform.startswith('darwin'):
            raise UnsupportedOperation
        else:
            raise UnsupportedOperation
    elif os.name == 'nt':
        raise UnsupportedOperation
    else:
        raise UnsupportedOperation
