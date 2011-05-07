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

from xl import event

DOUBANFM_INTERFACE_NAME="info.sunng.ExaileDoubanfm"

class DoubanFMDBusService(dbus.service.Object):
    def __init__(self, dbfm_plugin, bus):
        dbus.service.Object.__init__(self, bus, '/info/sunng/ExaileDoubanfm')
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
    def Favorite(self):
        self.dbfm_plugin.mark_as_like(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def Unfavorite(self):
        self.dbfm_plugin.mark_as_dislike(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def ToggleFavorite(self):
        current_track = self.__get_current_track()
        if current_track.get_tag_raw('fav')[0] == '0':
            self.dbfm_plugin.mark_as_like(current_track)
        else:
            self.dbfm_plugin.mark_as_dislike(current_track)

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def Skip(self):
        self.dbfm_plugin.mark_as_skip(self.__get_current_track())

    @dbus.service.method(DOUBANFM_INTERFACE_NAME)
    def Delete(self):
        self.dbfm_plugin.mark_as_skip(self.__get_current_track())

    #### dbus properties to expose

    def Metadata(self):
        metadata = {}
        current_track = self.__get_current_track()
        metadata['title'] = current_track.get_tag_raw('title')[0]
        metadata['artist'] = current_track.get_tag_raw('artist')[0]
        metadata['channel_id'] = self.dbfm_plugin.get_current_channel()

        for k,v in self.dbfm_plugin.channels.items():
            if v == metadata['channel_id']:
                metadata['channel_name'] = k
                break

        metadata['cover_url'] = current_track.get_tag_raw('cover_url')[0]
        metadata['link']  = current_track.get_tag_raw('fav')[0]
        return dbus.types.Dictionary(metadata, signature='sv', variant_level=1)

    def Status(self):
        return self.status

    ### helpers
    def __get_current_track(self):
        return self.dbfm_plugin.get_current_track()

class DoubanFMDBusController(object):
    DBUS_OBJECT_NAME = 'info.sunng.ExaileDoubanfm.instance'
    def __init__(self, dbfm_plugin):
        self.dbfm_plugin = dbfm_plugin
        self.bus = None

    def acquire_dbus(self):
        if self.bus:
            self.bus.get_bus().request_name(self.DBUS_OBJECT_NAME)
        else:
            self.bus = dbus.service.BusName(self.DBUS_OBJECT_NAME, bus=dbus.SessionBus())
        self.adapter = DoubanFMDBusService(self.dbfm_plugin, self.bus)

    def release_dbus(self):
        if self.adapter is not None:
            self.adapter.remove_from_connection()
        if self.bus is not None:
            self.bus.get_bus().release_name(self.bus.get_name())

    def register_events(self):
        event.add_callback(self.playback_started, 'playback_track_start')
        event.add_callback(self.playback_stopped, 'playback_track_stop')

    def unregister_events(self):
        event.remove_callback(self.playback_started, 'playback_track_start')
        event.remove_callback(self.playback_stopped, 'playback_track_stop')

    def playback_started(self, *e):
        self.adapter.status = "Playing"
        self.adapter.populate(*['Status', 'Metadata'])

    def playback_stopped(self, *e):
        self.adapter.status = "Playing"
        self.adapter.populate(*['Status'])



