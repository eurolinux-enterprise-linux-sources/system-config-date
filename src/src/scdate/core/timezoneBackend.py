# -*- coding: utf-8 -*-
#
# timezoneBackend - provides the backend for system time zone calls
#
# Copyright © 2001 - 2007, 2009, 2012 Red Hat, Inc.
# Copyright © 2001 - 2004 Brent Fox <bfox@redhat.com>
#                         Tammy Fox <tfox@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors:
# Brent Fox <bfox@redhat.com>
# Tammy Fox <tfox@redhat.com>
# Nils Philippsen <nils@redhat.com>

import os
from slip.util.files import (linkorcopyfile, symlink_atomically,
        overwrite_safely)


class timezoneBackend(object):
    def writeConfig(self, timezone, utc=True):
        timezonefile = timezone.replace(' ', '_')
        fromFile = "/usr/share/zoneinfo/" + timezonefile

        if not isinstance(utc, bool):
            if utc == 0 or utc == 'false':
                utc = False
            else:
                utc = True

        symlink_atomically(fromFile, "/etc/localtime", force=True)

        # Check to see if /var/spool/postfix/etc/localtime exists
        if os.access("/var/spool/postfix/etc/localtime", os.F_OK) == 1:
            # If it does, copy the new time zone file into the chroot jail
            linkorcopyfile(fromFile, "/var/spool/postfix/etc/localtime")

        if self._adjtimeHasUTCInfo:
            try:
                f = open("/etc/adjtime", "r")
                l = f.readlines()
                f.close()
            except:
                l = []

            if len(l) >= 2:
                adjtime_content = l[0] + l[1]
            else:
                # broken /etc/adjtime, fall back to no drift
                adjtime_content = "0.0 0 0.0\n0\n"

            if utc:
                adjtime_content += "UTC\n"
            else:
                adjtime_content += "LOCAL\n"

            overwrite_safely("/etc/adjtime", adjtime_content)

    def getTimezoneInfo(self):
        return (self.tz, self.utc)

    def setTimezoneInfo(self, timezone, utc=True):
        self.tz = timezone
        self.utc = utc

    def __init__(self):
        self.tz = None
        self.utc = "false"
        localtime = "/etc/localtime"
        zoneinfo = "/usr/share/zoneinfo/"    # must end with "/"
        legacy_path = "/etc/sysconfig/clock"
        lines = []
        self._canHwClock = None
        self._adjtimeHasUTCInfo = None

        if os.path.exists(localtime) and os.path.islink(localtime):
            tzfile = os.path.realpath(localtime)
            if tzfile.startswith(zoneinfo):
                self.tz = tzfile[len(zoneinfo):].replace('_', ' ')

        if not self.tz and os.access(legacy_path, os.R_OK):
            fd = open(legacy_path, 'r')
            lines = fd.readlines()
            fd.close()

            try:
                for line in lines:
                    line = line.strip()
                    if len(line) and line[0] == '#':
                        continue
                    try:
                        tokens = line.split("=")
                        if tokens[0] == "ZONE":
                            self.tz = tokens[1].replace('"', '')
                            self.tz = self.tz.replace('_', ' ')
                    except:
                        pass
            except:
                pass

        if not self.tz:
            self.tz = "America/New York"

        if os.access("/etc/adjtime", os.R_OK):
            fd = open("/etc/adjtime", 'r')
            lines = fd.readlines()
            fd.close()
            try:
                line = lines[2].strip()
                self._adjtimeHasUTCInfo = True
            except IndexError:
                line = 'UTC'
                self._adjtimeHasUTCInfo = False
            if line == 'UTC':
                self.utc = 'true'
            else:
                self.utc = 'false'

    @property
    def canHwClock(self):
        if self._canHwClock is None:
            if os.system("/sbin/hwclock > /dev/null 2>&1") == 0:
                self._canHwClock = True
            else:
                self._canHwClock = False

        return self._canHwClock
