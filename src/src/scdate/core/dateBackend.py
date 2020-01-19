# -*- coding: utf-8 -*-
#
# dateBackend.py - provides the backend for system date calls
#
# Copyright © 2001-2011 Red Hat, Inc.
# Copyright © 2001-2003 Brent Fox <bfox@redhat.com>
#                       Tammy Fox <tfox@redhat.com>
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
# Miroslav Lichvár <mlichvar@redhat.com>

import os
import sys
import time
import shlex

from slip.util.files import overwrite_safely

import servicesBackend


class NTPProvider(object):

    def __init__(self, daemon, service_name, unit_name, config_file):
        self.daemon = daemon
        self.service_name = service_name
        self.unit_name = unit_name
        self.config_file = config_file


class dateBackend(object):

    ntpProviders = (
            NTPProvider("chronyd", "chronyd", "chronyd.service",
                "/etc/chrony.conf"),
            NTPProvider("ntpd", "ntpd", "ntpd.service", "/etc/ntp.conf")
            )

    def __init__(self):
        self.ntpProvider = None
        self.ntpFile = None
        self.ntpServers = None
        self.ntpBroadcastClient = False
        self.ntpLocalTimeSource = False
        self.services = servicesBackend.Services()
        self.selectNtpService()
        self.readNtpConf()
        self.getNtpServers()
        pass

    def getDate(self):
        times = time.localtime(time.time())
        return times

    def writeDateConfig(self, sysDate, sysTime):
        year, month, day = sysDate
        hour, min, sec = sysTime

        # cal.get_date starts counting months at 0 for Jan. We need to start
        # counting at 1
        month = month + 1
        cmd = '/bin/date -s %d/%d/%d\ %s:%s:%s' % (year, month, day, hour,
                min, sec)
        fd = os.popen(cmd, 'r')
        fd.readlines()
        return not fd.close()

    def syncHardwareClock(self):
        # sync hardware clock.  Will use either localtime or utc
        # according to value in /etc/adjtime (recorded last time hwclock
        # was run).
        if os.access("/sbin/hwclock", os.F_OK) == 1:
            # The S390 has no hwclock binary, so don't try to run it if it
            # isn't there
            return not os.system("/sbin/hwclock --systohc")
        return True

    def writeNtpConfig(self, ntpServers, ntpBroadcastClient,
            ntpLocalTimeSource, ntpIburst):
        broadcastclientFound = False
        localstratumFound = False
        ntpFileList = []

        servers = []
        for server in ntpServers:
            if server not in servers:
                servers.append(server)
        if (ntpLocalTimeSource and
                self.ntpProvider.daemon == "ntpd" and
                "127.127.1.0" not in servers):
            servers.append("127.127.1.0")

        serversfound = []

        # Write /etc/ntp.conf file, default to template if it was missing or
        # empty
        if self.ntpFile and len(self.ntpFile) > 0:
            lines = self.ntpFile
        elif self.ntpProvider.daemon == "ntpd":
            fd = open("/usr/share/system-config-date/ntp.conf.template", "r")
            lines = fd.readlines()
            fd.close()
        else:
            lines = []

        for line in lines:
            tokens = line.split()
            if len(tokens) == 0:
                # empty line, copy verbatim
                ntpFileList.append(line)

            elif tokens[0] == "server":
                # server line
                if len(tokens) > 1:
                    host = tokens[1]
                    if host in servers:
                        line = self.addRemoveIburst(line, ntpIburst)
                        ntpFileList.append(line)
                        serversfound.append(host)
                else:
                    # What do we do here? server without an address isn't
                    # described in the documentation. Barring any problems
                    # we'll leave the line as it is.
                    ntpFileList.append(line)
            elif (tokens[0] in ("broadcastclient", "#broadcastclient") or
                    len(tokens) > 1 and tokens[0] == "#" and
                    tokens[1] == "broadcastclient"):
                # if 'broadcastclient' is found in the line
                if not broadcastclientFound:
                    if not ntpBroadcastClient:
                        ntpFileList.append("#")
                    ntpFileList.append("broadcastclient\n")
                    broadcastclientFound = 1
                else:
                    ntpFileList.append(line)
            elif (tokens[0] in ("local", "#local") and len(tokens) > 1 and
                    tokens[1] == "stratum"):
                localstratumFound = 1
                if ntpLocalTimeSource:
                    tokens[0] = "local"
                else:
                    tokens[0] = "#local"
                ntpFileList.append(" ".join(tokens) + "\n")
            else:
                #This is not the server line, so just add it to the list
                ntpFileList.append(line)

        for server in servers:
            if not server in serversfound:
                if ntpIburst:
                    ntpFileList.append("server %s iburst\n" % (server))
                else:
                    ntpFileList.append("server %s\n" % (server))

        if not broadcastclientFound and ntpBroadcastClient:
            ntpFileList.append("broadcastclient\n")

        if (ntpLocalTimeSource and
                self.ntpProvider.daemon == "chronyd" and
                not localstratumFound):
            ntpFileList.append("local stratum 10")

        # Now that we've got the list of data, open the file and write it out
        try:
            overwrite_safely(self.ntpProvider.config_file,
                    "".join(ntpFileList))
        except Exception, e:
            print >>sys.stderr, e
            return

        self.ntpFile = ntpFileList

        # Add iburst to or remove it from to NTPSERVERARGS in
        # /etc/sysconfig/network. This is used to specify options for servers
        # which are dynamically added by dhclient.
        try:
            f = open("/etc/sysconfig/network", "r")
            lines = f.readlines()
            f.close()
        except:
            lines = []

        lines_new = []
        found = False
        for line in lines:
            # parsing shell is hard
            start, x, end = line.partition("=")
            if start.lstrip() == "NTPSERVERARGS" and end == end.lstrip() and \
                    len(end) > 0:
                end_tokens = shlex.split(end)
                tokens = end_tokens[0].split()
                if "iburst" in tokens:
                    found = True
                    if not ntpIburst:
                        # rebuild changed NTPSERVERARGS line, not optimal
                        tokens = filter(lambda x: x != "iburst", tokens)
                        if len(tokens) > 0:
                            if len(tokens) > 1:
                                end_tokens[0] = "\"%s\"" % (" ".join(tokens))
                            elif len(tokens) == 1:
                                end_tokens[0] = tokens[0]
                            line = start + x + " ".join(end_tokens) + "\n"
                        else:
                            line = ""

            lines_new.append(line)
        if ntpIburst and not found:
            lines_new.append("NTPSERVERARGS=iburst\n")

        try:
            overwrite_safely("/etc/sysconfig/network", "".join(lines_new))
        except Exception, e:
            print e
            return

        return 0

    def selectNtpService(self):
        # select chronyd or ntpd service, based on which is enabled or
        # installed, prefer chronyd if both are installed and disabled

        for method in (self.services.service_is_enabled,
                self.services.service_exists):

            for provider in self.ntpProviders:
                if method(provider.service_name):
                    self.ntpProvider = provider
                    return

    def _handleOtherNTPProviders(self, what):
        for p in self.ntpProviders:
            if p is not self.ntpProvider:
                # other providers may not even exist, we really don't care if
                # this works or not
                try:
                    what(p.service_name)
                except:
                    pass

    def startNtpService(self, wait):
        if self.ntpProvider is None:
            return None

        self._handleOtherNTPProviders(self.services.service_stop)
        if self.isNtpRunning() == 1:
            return self.services.service_restart(self.ntpProvider.service_name)
        else:
            return self.services.service_start(self.ntpProvider.service_name)

    def chkconfigOn(self):
        self._handleOtherNTPProviders(self.services.service_disable)
        if self.ntpProvider is not None:
            return self.services.service_enable(self.ntpProvider.service_name)

    def chkconfigOff(self):
        self._handleOtherNTPProviders(self.services.service_disable)
        if self.ntpProvider is not None:
            return self.services.service_disable(self.ntpProvider.service_name)

    def stopNtpService(self):
        self._handleOtherNTPProviders(self.services.service_stop)
        if self.isNtpRunning():
            self.services.service_stop(self.ntpProvider.service_name)
            self.chkconfigOff()

    def isNtpRunning(self):
        if (self.ntpProvider is None or
                not os.access(self.ntpProvider.config_file, os.R_OK)):
            # if there is no NTP service installed or its configuration is
            # missing, return
            return None

        return self.services.service_is_active(self.ntpProvider.service_name)

    def getNtpServers(self):
        self.ntpServers = []
        self.ntpLocalTimeSource = False

        if self.ntpFile:
            for line in self.ntpFile:
                tokens = line.split()

                if len(tokens) == 0:
                    continue

                elif tokens[0] == "server":
                    try:
                        server = tokens[1]
                        if server == "127.127.1.0":
                            self.ntpLocalTimeSource = True
                        else:
                            self.ntpServers.append(server)
                    except IndexError:
                        # They have a server line in /etc/ntp.conf with no
                        # server specified
                        pass
                elif (tokens[0] == "local" and len(tokens) > 1 and
                        tokens[1] == "stratum"):
                    self.ntpLocalTimeSource = True

        return (self.ntpServers, self.ntpLocalTimeSource)

    def getNtpBroadcastClient(self):
        broadcastclient = False

        if self.ntpFile:
            for line in self.ntpFile:
                location = line.find('broadcastclient')
                if location == 0:
                    tokens = line.split()

                    if tokens[0][0] != "#" and tokens[0] == "broadcastclient":
                        broadcastclient = True

        self.ntpBroadcastClient = broadcastclient

        return broadcastclient

    def getIburst(self):
        for line in self.ntpFile:
            directive, hash, comment = line.partition("#")
            tokens = directive.split()
            if (len(tokens) > 0 and tokens[0] == "server" and
                    "iburst" in tokens):
                return True
        return False

    def readNtpConf(self):
        try:
            fd = open(self.ntpProvider.config_file, 'r')
            self.ntpFile = fd.readlines()
            fd.close()
        except:
            return

    def addRemoveIburst(self, line, addIburst):
        precomment, x, comment = line.rstrip("\n").partition("#")

        tokens = precomment.split()

        if "iburst" in tokens:
            if not addIburst:
                tokens.remove("iburst")
                return " ".join(tokens) + x + comment + "\n"
        else:
            if addIburst:
                tokens.append("iburst")
                return " ".join(tokens) + x + comment + "\n"

        # unchanged
        return line

# vim: et ts=4
