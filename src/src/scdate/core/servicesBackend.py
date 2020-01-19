# -*- coding: utf-8 -*-
#
# servicesBackend.py - abstract init flavors (SysV, systemd) a bit to check for
#                      services, very much tailored to s-c-date needs, doesn't
#                      care for xinetd services
#
# Copyright © 2011 Red Hat, Inc.
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
# Nils Philippsen <nils@redhat.com>

import subprocess
import os


class AbstractServices(object):

    executables = ()

    @classmethod
    def check_flavor(cls):
        for exe in cls.executables:
            if not os.access(exe, os.X_OK):
                return False
        return True

    @classmethod
    def call(cls, *command):
        return subprocess.call(command, stdin=open("/dev/null", 'r'),
                stdout=open("/dev/null", 'w'), stderr=subprocess.STDOUT)

    @classmethod
    def service_exists(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_is_enabled(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_is_active(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_enable(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_disable(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_start(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_restart(cls, service):
        raise NotImplementedError()

    @classmethod
    def service_stop(cls, service):
        raise NotImplementedError()


class SysVServices(AbstractServices):

    chkconfig = "/sbin/chkconfig"
    service = "/sbin/service"

    executables = (chkconfig, service)

    @classmethod
    def check_flavor(cls):
        # TODO: any other checks to determine if SysV init/upstart is active?
        return super(SysVServices, cls).check_flavor()

    @classmethod
    def service_exists(cls, service):
        return cls.call(cls.chkconfig, "--type=sysv", "--list", service) == 0

    @classmethod
    def service_is_enabled(cls, service):
        return cls.call(cls.chkconfig, "--type=sysv", service) == 0

    @classmethod
    def service_is_active(cls, service):
        return cls.call(cls.service, service, "status") == 0

    @classmethod
    def service_enable(cls, service):
        return cls.call(cls.chkconfig, "--type=sysv", service, "on")

    @classmethod
    def service_disable(cls, service):
        return cls.call(cls.chkconfig, "--type=sysv", service, "off")

    @classmethod
    def service_start(cls, service):
        return cls.call(cls.service, service, "start")

    @classmethod
    def service_restart(cls, service):
        return cls.call(cls.service, service, "restart")

    @classmethod
    def service_stop(cls, service):
        return cls.call(cls.service, service, "stop")


class SystemDServices(AbstractServices):

    systemctl = "/bin/systemctl"
    systemd = "/bin/systemd"
    cgroups_mount = "/sys/fs/cgroup"
    systemd_cgroups_mount = cgroups_mount + "/systemd"
    units_basedir = "/lib/systemd/system/"

    executables = (systemctl, systemd)

    @classmethod
    def check_flavor(cls):
        return (super(SystemDServices, cls).check_flavor() and
                os.path.ismount(cls.cgroups_mount) and
                os.path.ismount(cls.systemd_cgroups_mount))

    @classmethod
    def _unitname(cls, service):
        return service + ".service"

    @classmethod
    def _unitfile(cls, service):
        return cls.units_basedir + cls._unitname(service)

    @classmethod
    def service_exists(cls, service):
        return (os.path.exists(cls._unitfile(service)) or
                SysVServices.service_exists(service))

    @classmethod
    def service_is_enabled(cls, service):
        return (cls.call(cls.systemctl, "is-enabled",
                            cls._unitname(service)) == 0)

    @classmethod
    def service_is_active(cls, service):
        return (cls.call(cls.systemctl, "-q", "is-active",
                            cls._unitname(service)) == 0)

    @classmethod
    def service_enable(cls, service):
        return cls.call(cls.systemctl, "enable", cls._unitname(service))

    @classmethod
    def service_disable(cls, service):
        return cls.call(cls.systemctl, "disable", cls._unitname(service))

    @classmethod
    def service_start(cls, service):
        return cls.call(cls.systemctl, "start", cls._unitname(service))

    @classmethod
    def service_restart(cls, service):
        return cls.call(cls.systemctl, "restart", cls._unitname(service))

    @classmethod
    def service_stop(cls, service):
        return cls.call(cls.systemctl, "stop", cls._unitname(service))

__services = None


def Services():
    global __services
    if __services is None:
        for candidate in SystemDServices, SysVServices:
            if candidate.check_flavor():
                __services = candidate
                break
    return __services
