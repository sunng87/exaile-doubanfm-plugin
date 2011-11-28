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

from libdoubanfm import DoubanFM, DoubanTrack, DoubanLoginException
from doubanfm_mode import DoubanFMMode
from doubanfm_cover import DoubanFMCover
from doubanfm_dbus import DoubanFMDBusController

import dbfm_pref

import gtk
import time
import urllib
from string import Template

from xl import common, event, main, playlist, xdg, settings, trax, providers
from xl.radio import *
from xl.nls import gettext as _
from xl.trax import Track
from xlgui import guiutil


DOUBANFM = None

def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, "exaile_loaded")
    else:
        _enable(None, exaile, None)

def _enable(device, exaile, nothing):
    global DOUBANFM

    DOUBANFM = DoubanRadioPlugin(exaile)

def disable(exaile):
    global DOUBANFM
    DOUBANFM.destroy(exaile)

def get_preferences_pane():
    return dbfm_pref

SHARE_TEMPLATE = {'kaixin001': "http://www.kaixin001.com/repaste/bshare.php?rurl=%s&rcontent=&rtitle=%s",
        'renren': "http://www.connect.renren.com/share/sharer?title=%s&url=%s",
        'sina': "http://v.t.sina.com.cn/share/share.php?appkey=3015934887&url=%s&title=%s&source=&sourceUrl=&content=utf-8&pic=%s",
        'twitter': "http://twitter.com/share?text=%s&url=%s",
        'fanfou': "http://fanfou.com/sharer?u=%s&t=%s&d=&s=bm",
        'douban': "http://www.douban.com/recommend/?url=%s"}

class DoubanRadioPlugin(object):
    @common.threaded
    def __init__(self, exaile):
        self.exaile = exaile        
        ## mark if a track is skipped instead of end normally
        self.skipped = False
        self.pre_init()

    def pre_init(self):
        self.__create_pre_init_menu_item()

    def do_init(self, *args):
        username = settings.get_option("plugin/douban_radio/username")  
        password = settings.get_option("plugin/douban_radio/password")
        try:
            self.doubanfm = DoubanFM(username, password)
        except DoubanLoginException as e:
            self.exaile.gui.main.message.show_error(
                _('Douban FM Error'),
                _('Failed to login to douban.fm with your credential'))
            return
        self.channels = self.doubanfm.channels

        self.__create_menu_item__()

        self.check_to_enable_dbus()

        self.__register_events()
        self.doubanfm_mode = DoubanFMMode(self.exaile, self)
        self.doubanfm_cover = DoubanFMCover()
        providers.register('covers', self.doubanfm_cover)

    @staticmethod
    def __translate_channels():
        d = {}
        for k in DoubanFMChannels.keys():
            d[_(k)] = DoubanFMChannels[k]
        return d

    def __register_events(self):
        event.add_callback(self.check_to_load_more, 'playback_track_start')
        event.add_callback(self.close_playlist, 'quit_application')
        event.add_callback(self.play_feedback, 'playback_track_end')

        if self.dbus_controller:
            self.dbus_controller.register_events()

    def __unregister_events(self):
        event.remove_callback(self.check_to_load_more, 'playback_track_start')
        event.remove_callback(self.close_playlist, 'quit_application')
        event.remove_callback(self.play_feedback, 'playback_track_end')

        if self.dbus_controller:
            self.dbus_controller.unregister_events()

    @common.threaded
    def mark_as_skip(self, track):
        self.skipped = True
        playlist = self.get_current_playlist()

        rest_sids = self.get_rest_sids(playlist)

        ## play next song
        self.exaile.gui.main.queue.next()

        sid = track.get_tag_raw('sid')[0]
        aid = track.get_tag_raw('aid')[0]
        songs = self.doubanfm.skip_song(sid, aid, history=self.get_history_sids(playlist))
        self.load_more_tracks(songs)

    def load_more_tracks(self, songs):
        tracks = map(self.create_track_from_douban_song, songs)
        playlist = self.get_current_playlist()

#        if self.get_tracks_remain() > 15:
#            for i in range(len(tracks)):
#                ## just a walk around
#                time.sleep(1)
#
#                playlist.remove(len(playlist)-1)

        if self.get_tracks_remain() < 15:
            playlist.add_tracks(tracks)
            

    @common.threaded
    def mark_as_like(self, track):
        sid = track.get_tag_raw('sid')[0]
        aid = track.get_tag_raw('aid')[0]
        self.doubanfm.fav_song(sid, aid)
        track.set_tag_raw('fav', '1')

    @common.threaded
    def mark_as_dislike(self, track):
        sid = track.get_tag_raw('sid')[0]
        aid = track.get_tag_raw('aid')[0]

        track.set_tag_raw('fav', '0')
        self.doubanfm.unfav_song(sid, aid)

    @common.threaded
    def mark_as_recycle(self, track):
        self.skipped = True
        playlist = self.get_current_playlist()

        rest_sids = self.get_rest_sids(playlist)

        ## play next song
        self.exaile.gui.main.queue.next()

        ## remove the track
        self.remove_current_track()

        sid = track.get_tag_raw('sid')[0]
        aid = track.get_tag_raw('aid')[0]
        songs = self.doubanfm.del_song(sid, aid, rest=rest_sids)

        self.load_more_tracks(songs)

    def get_rest_sids(self, playlist):
        playlist = self.get_current_playlist()

        current_tracks = playlist.get_tracks()
        rest_tracks = current_tracks[playlist.get_current_pos()+1:]
        rest_sids = self.tracks_to_sids(rest_tracks)
        return rest_sids
        
    def share(self, target, track):
        if target not in SHARE_TEMPLATE:
            return None

        templ = SHARE_TEMPLATE[target]
        data = {}
        data['title'] = track.get_tag_raw('title')[0]
        data['artist'] = track.get_tag_raw('artist')[0]
        data['sid'] = track.get_tag_raw('sid')[0]
        data['ssid'] = track.get_tag_raw('ssid')[0]
        data['picture'] = track.get_tag_raw('cover_url')[0]

        track = DoubanTrack(**data)

        if target == 'renren':
            title = track.title + ", " + track.artist
            p = templ % tuple(map(urllib.quote_plus, [title.encode('utf8'), track.get_uri()]))
            return p
        if target == 'kaixin001':
            title = track.title + ", " + track.artist
            p = templ % tuple(map(urllib.quote_plus, [track.get_uri(), title.encode('utf8')]))
            return p
        if target == 'sina':
            title = track.title + ", " + track.artist
            p = templ % tuple(map(urllib.quote_plus, [track.get_uri(), title.encode('utf8'), track.picture]))
            return p
        if target == 'twitter':
            title = track.title + ", " + track.artist
            p = templ % tuple(map(urllib.quote_plus, [title.encode('utf8'), track.get_uri()]))
            return p
        if target == 'fanfou':
            title = track.title + ", " + track.artist
            p = templ % tuple(map(urllib.quote_plus, [track.get_uri(), title.encode('utf8')]))
            return p
        if target == 'douban':
            p = templ % tuple(map(urllib.quote_plus, [track.get_uri()]))
            return p

    def get_tracks_remain(self):
        pl = self.get_current_playlist()
        total = len(pl.get_tracks())
        cursor = pl.get_current_pos()
        return total-cursor-1

    def get_current_track(self):
        pl = self.get_current_playlist()
        if isinstance(pl, DoubanFMPlaylist):
            return pl.get_tracks()[pl.get_current_pos()]
        else:
            return None

    def remove_current_track(self):
        self.exaile.gui.main.get_current_playlist().remove_selected_tracks()

    def tracks_to_sids(self, tracks):
        return map(lambda t: t.get_tag_raw('sid')[0], tracks)

    @common.threaded
    def play_feedback(self, type, player, current_track):
        if self.skipped:
            self.skipped = False
            return
        track = current_track
        if track.get_tag_raw('sid'):
            sid = track.get_tag_raw('sid')[0]
            aid = track.get_tag_raw('aid')[0]
            if sid is not None and aid is not None:
                self.doubanfm.played_song(sid, aid)

    def get_current_playlist(self):
        return self.exaile.gui.main.get_selected_playlist().playlist

    def close_playlist(self, type, exaile, data=None):
        removed = 0
        for i,page in enumerate(exaile.gui.main.playlist_notebook):
            if isinstance(page.playlist, DoubanFMPlaylist):
                exaile.gui.main.close_playlist_tab(i-removed)
                removed += 1

    def check_to_load_more(self, type, player, track):
        playlist = self.get_current_playlist()
        if isinstance(playlist, DoubanFMPlaylist):
            ## check if last one
            ## playlist.index(track), len(playlist.get_tracks())
            if self.get_tracks_remain() <= 1:
                self.load_more(playlist)

    def get_history_sids(self, playlist):
        current_tracks = playlist.get_ordered_tracks()
        sids = self.tracks_to_sids(current_tracks)
        return sids

    def load_more(self, playlist):
        sids = self.get_history_sids(playlist)
        current_sid = self.get_current_track().get_tag_raw('sid')[0]
        retry = 0
        while retry < 1:
            try:
                songs = self.doubanfm.played_list(current_sid, sids)
            except:
                retry += 1
                continue
            
            if len(songs) > 0:
                tracks = map(self.create_track_from_douban_song, songs)
                playlist.add_tracks(tracks)
                break
            else:
                retry += 1

    def __create_menu_item__(self):
        exaile = self.exaile

        if self.preInitMenuItem is not None:
            exaile.gui.builder.get_object('file_menu').remove(self.preInitMenuItem)
        
        self.menuItem = gtk.MenuItem(_('Open Douban.fm'))
        menu = gtk.Menu()
        self.menuItem.set_submenu(menu)

        for channel_name  in self.channels.keys():
            menuItem = gtk.MenuItem(_(channel_name))

            menuItem.connect('activate', self.active_douban_radio, self.channels[channel_name])
            
            menu.prepend(menuItem)
            menuItem.show()

#       self.menu.connect('activate', self.active_douban_radio, self.exaile)

        exaile.gui.builder.get_object('file_menu').insert(self.menuItem, 5)

        self.menuItem.show()

        self.modeMenuItem = gtk.MenuItem(_('DoubanFM mode'))
        key, modifier = gtk.accelerator_parse('<Control>D')
        self.accels = gtk.AccelGroup()
        self.modeMenuItem.add_accelerator('activate', self.accels, key, modifier, gtk.ACCEL_VISIBLE)
        self.exaile.gui.main.window.add_accel_group(self.accels)
        self.modeMenuItem.connect('activate', self.show_mode)
        exaile.gui.builder.get_object('view_menu').append(self.modeMenuItem)
        self.modeMenuItem.show()

    def __create_pre_init_menu_item(self):
        self.preInitMenuItem = gtk.MenuItem(_('Connect to Douban.fm'))
        self.preInitMenuItem.connect('activate', self.do_init)
        self.preInitMenuItem.show()
        self.exaile.gui.builder.get_object('file_menu').insert(self.preInitMenuItem, 5)
    
    def create_track_from_douban_song(self, song):
        track = Track(song.url)
        track.set_tag_raw('sid', song.sid)
        track.set_tag_raw('aid', song.aid)
        track.set_tag_raw('ssid', song.ssid or '')

        track.set_tag_raw('uri', song.url)
        track.set_tag_raw('cover_url', song.picture)
        track.set_tag_raw('title', song.title)
        track.set_tag_raw('artist', song.artist)
        track.set_tag_raw('album', song.albumtitle)
        track.set_tag_raw('fav', str(song.like) or '0')

        return track

    def show_mode(self, *e):
        self.doubanfm_mode.show()

    def create_playlist(self, name, channel, initial_tracks=[]):
        plist = DoubanFMPlaylist(name, channel)
        plist.set_ordered_tracks(initial_tracks)

        plist.set_repeat(False)
        plist.set_random(False)
        plist.set_dynamic(False)

        return plist

    def get_current_channel(self):
        return self.get_current_playlist().channel

    def active_douban_radio(self, type, channel_id, auto=False):
        self.doubanfm.channel = channel_id
        try:
            songs = self.doubanfm.new_playlist()
        except:
            dialog = gtk.MessageDialog(self.exaile.gui.main.window, 0,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    _('Failed to retrieve playlist, try again.'))
            dialog.run()
            dialog.destroy()
            return

        tracks = map(self.create_track_from_douban_song, songs)
        channel_name = self.channel_id_to_name(channel_id)
        plist = self.create_playlist(
                'DoubanFM %s' % channel_name, channel_id, tracks)
        
        self.exaile.gui.main.add_playlist(plist)

        if auto: 
            self._stop()
            self._play()            

    def _stop(self):
        self.exaile.player.stop()

    def _play(self):
        ## ref xlgui.main.on_playpause_button_clicked
        guimain = self.exaile.gui.main
        pl = guimain.get_selected_playlist()
        guimain.queue.set_current_playlist(pl.playlist)
        if pl:
            track = pl.get_selected_track()
            if track:
                pl.playlist.set_current_pos((pl.playlist.index(track)))
        guimain.queue.play()

    def destroy(self, exaile):
        try:
            providers.unregister('covers', self.doubanfm_cover)
            if self.menuItem :
                exaile.gui.builder.get_object('file_menu').remove(self.menuItem)
            if self.modeMenuItem:
                exaile.gui.builder.get_object('view_menu').remove(self.modeMenuItem)
                exaile.gui.main.remove_accel_group(self.accels)
            self.__unregister_events()

            self.doubanfm_mode.destroy()

            if self.dbus_controller:
                self.dbus_controller.on_exit()
                self.dbus_controller.unregister_events()
                self.dbus_controller.release_dbus()
        except:
            pass

    def check_to_enable_dbus(self):
        if settings.get_option('plugin/douban_radio/dbus_indicator'):
            self.dbus_controller = DoubanFMDBusController(self)
            self.dbus_controller.acquire_dbus()
            self.dbus_controller.on_init()
        else:
            self.dbus_controller = None

    def channel_id_to_name(self, channel_id):
        for k,v in self.channels.items():
            if v == channel_id:
                return k
        return None
       
class DoubanFMPlaylist(playlist.Playlist):
    def __init__(self, name, channel):
        playlist.Playlist.__init__(self, name)
        self.channel = channel
       
