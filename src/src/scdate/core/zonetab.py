# -*- coding: utf-8 -*-
#
# zonetab.py: time zone classes
#
# Copyright © 2001 - 2003, 2005 - 2007 , 2009 Red Hat, Inc.
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
# Matt Wilson <msw@redhat.com>
# Brent Fox <bfox@redhat.com>
# Nils Philippsen <nphilipp@redhat.com>

import re
import math
import locale
import warnings

from util import ugettext, dltrans

__all__ = ("ZoneTabEntry", "ZoneTab")

class ZoneTabEntry(object):

    __instances = []
    __lang_change_cb_registered = False

    __tz_seen = set()
    __tz_translations = {}

    _slash_lookalikes = (
            u"\u2044",      # FRACTION SLASH
            u"\u2215",      # DIVISION SLASH
            u"\u29F8",      # BIG SOLIDUS
            u"\uFF0F",      # FULLWIDTH SOLIDUS
            )

    def __init__ (self, code=None, lat=None, long=None, tz=None, comments=None):
        # register class callback for language changes
        if not ZoneTabEntry.__lang_change_cb_registered:
            dltrans.register_lang_change_callback(ZoneTabEntry.__lang_changed)
            ZoneTabEntry.__lang_change_cb_registered = True

        self.code = code
        self.lat = lat
        self.long = long
        self.tz = tz.replace ('_', ' ')
        self.comments = comments
        self.__instances.append(self)

    def __del__(self):
        self.__instances.remove(self)

    @classmethod
    def __lang_changed(cls):
        # throw away previous translations and recreate them for the new
        # language (anaconda needs that)
        cls.__tz_seen = set()
        cls.__tz_translations = {}

        for i in cls.__instances:
            i.__translate_tz()

    def __translate_tz(self):
        if self._tz in ZoneTabEntry.__tz_translations:
            return

        # time zone msgid and msgstr have underscores instead of spaces
        translated = ugettext(self._tz.replace(" ", "_")).replace("_", " ")

        (lang, coding) = locale.getlocale()
        if lang is None:
            locale.setlocale(locale.LC_ALL, "")
            (lang, coding) = locale.getlocale()

        if not (lang in (None, "C", "POSIX", "en") or lang.startswith("en_")):
            warn_untranslated = True
        else:
            warn_untranslated = False

        if translated == self._tz:
            if warn_untranslated and self._tz not in self.__tz_seen and \
                not self._tz.startswith("Etc/"):
                    warnings.warn("Untranslated time zone: " + self._tz,
                                  RuntimeWarning, stacklevel=4)
            ZoneTabEntry.__tz_seen.add(self._tz)
            return
        else:
            # there is more than one slash character in Unicode, normalize
            # on SOLIDUS (U+002F) so that per component translations work
            translated = reduce(lambda x, y: x.replace(y, "/"),
                                self._slash_lookalikes,
                                translated)

        ZoneTabEntry.__tz_seen.add(self._tz)
        ZoneTabEntry.__tz_translations[self._tz] = translated

        # store translations of higher order parts of the time zone,
        # if possible
        if self._tz.count("/") == translated.count("/"):
            tz = self._tz

            while "/" in tz:
                (tz, sep, tail) = tz.rpartition("/")
                if tz in ZoneTabEntry.__tz_translations:
                    break
                (translated, sep, tail) = translated.rpartition("/")
                ZoneTabEntry.__tz_translations[tz] = translated

    def _get_tz(self):
        return self._tz

    def _set_tz(self, tz):
        self._tz = tz
        self.__translate_tz()

    tz = property(_get_tz, _set_tz)

    @property
    def translated_tz(self):
        if self.tz in ZoneTabEntry.__tz_translations:
            return ZoneTabEntry.__tz_translations[self.tz]

        # try to translate higher order parts
        parts = self.tz.split("/")

        split_at = max(len(parts) - 1, 0)

        while split_at > 0:
            head = "/".join(parts[:split_at])
            tail = "/".join(parts[split_at:])
            if head in ZoneTabEntry.__tz_translations:
                return ZoneTabEntry.__tz_translations[head] + "/" + tail
            split_at -= 1

        return self.tz

class ZoneTab(object):
    def __init__ (self, fn='/usr/share/zoneinfo/zone.tab'):
        self.entries = []
        self.readZoneTab (fn)
        self.addNoGeoZones ()

    def getEntries (self):
        return self.entries

    def findEntryByTZ (self, tz):
        for entry in self.entries:
            if entry.tz == tz:
                return entry
        return None

    def findNearest (self, long, lat, longmin, latmin, longmax, latmax, currentEntry):
        #print "findNearest: long:%.1f lat:%.1f longmin:%.1f longmax:%.1f latmin:%.1f latmax:%.1f currentEntry:%s" % (long, lat, longmin, longmax, longmax, latmax, currentEntry)
        nearestEntry = None
        if longmin <= long <= longmax and latmin <= lat <= latmax:
            min = -1
            for entry in filter (lambda x: x.tz != currentEntry.tz,
                                 self.entries):
                if not (entry.lat and entry.long and latmin <= entry.lat <= latmax and longmin <= entry.long <= longmax):
                    continue
                dx = entry.long - long
                dy = entry.lat - lat
                dist = (dy * dy) + (dx * dx)
                if dist < min or min == -1:
                    min = dist
                    nearestEntry = entry
        return nearestEntry

    def convertCoord (self, coord, type="lat"):
        if type != "lat" and type != "long":
            raise TypeError, "invalid coord type"
        if type == "lat":
            deg = 3
        else:
            deg = 4
        degrees = int (coord[0:deg])
        order = len (coord[deg:])
        minutes = int (coord[deg:])
        if degrees > 0:
            return degrees + minutes/math.pow (10, order)
        return degrees - minutes/math.pow (10, order)

    def readZoneTab (self, fn):
        f = open (fn, 'r')
        comment = re.compile ("^#")
        coordre = re.compile ("[\+-]")
        while 1:
            line = f.readline ()
            if not line:
                break
            if comment.search (line):
                continue
            fields = line.split ('\t')
            if len (fields) < 3:
                continue
            code = fields[0]
            split = coordre.search (fields[1], 1)
            lat = self.convertCoord (fields[1][:split.end () - 1], "lat")
            long = self.convertCoord (fields[1][split.end () - 1:], "long")
            tz = fields[2].strip ().replace ('_', ' ')
            if len (fields) > 3:
                comments = fields[3].strip ()
            else:
                comments = None
            entry = ZoneTabEntry (code, lat, long, tz, comments)
            self.entries.append (entry)

    def addNoGeoZones (self):
        nogeotzs = ['UTC']
        for offset in xrange (-14, 13):
            if offset < 0:
                tz = 'GMT%d' % offset
            elif offset > 0:
                tz = 'GMT+%d' % offset
            else:
                tz = 'GMT'
            nogeotzs.append (tz)
        for tz in nogeotzs:
            self.entries.append (ZoneTabEntry (None, None, None, "Etc/" + tz, None))

