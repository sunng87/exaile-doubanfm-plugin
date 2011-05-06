# Copyright (C) 2008-2011 Sun Ning <classicning@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.

import dbus

DOUBANFM_INTERFACE_NAME="info.sunng.ExaileDoubanfm"

class DoubanFMDBusController(dbus.service.Object):
    def __init__(self, dbfm_plugin, bus):
        dbus.service.Object.__(self, bus, DOUBANFM_INTERFACE_NAME)
        self.dbfm_plugin = dbfm_plugin

    def populate(self, *prop_names):
        props = {}
        for p in prop_names:
            props[p] = getattr(self, p)()
        self.PropertiesChanged(DOUBANFM_INTERFACE_NAME, props, [])

    @dbus.service.method(dbus.PROPERTIES_IFACE, in_signature='ss', out_signature='v')
    def Get(self, interface, prop):
        if hasattr(self, prop):
            result = getattr(self, prop)()
            return result
        return None

    @dbus.service.signal(dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(self, interface, updated, invalid):
        #logger.info("fired")
        pass

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def favorite(self):
        self.dbfm_plugin.mark_as_like(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def unfavorite(self):
        self.dbfm_plugin.mark_as_dislike(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def skip(self):
        self.dbfm_plugin.mark_as_skip(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def delete(self):
        self.dbfm_plugin.mark_as_skip(self.__get_current_track())

    #### dbus properties to expose

    def title(self):
        current_track = self.__get_current_track()
        return current_track.get_tag_raw('title')[0]

    def artist(self):
        current_track = self.__get_current_track()
        return current_track.get_tag_raw('artist')[0]

    def channel(self):
        return self.dbfm_plugin.get_current_channel()

    def channel_name(self):
        channel_id = self.dbfm_plugin.get_current_channel()
        for k,v in self.dbfm_plugin.channels.items():
            if v == channel_id:
                return k

    def art_url(self):
        current_track = self.__get_current_track()
        return current_track.get_tag_raw('cover_url')[0]

    def is_favorite(self):
        current_track = self.__get_current_track()
        return current_track.get_tag_raw('fav')[0]

    ### helpers
    def __get_current_track(self):
        return self.dbfm_plugin.get_current_track()

