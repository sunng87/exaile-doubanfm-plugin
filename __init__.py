# Copyright (C) 2008-2010 Sun Ning <classicning@gmail.com>
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

from libdbfm import DoubanRadio
from doubanfm_mode import DoubanfmMode
import dbfm_pref

import gtk

from xl import common, event, main, playlist, xdg, settings, trax
from xl.radio import *
from xl.nls import gettext as _
from xlgui import guiutil

DOUBANFM = None

def enable(exaile):
    if exaile.loading:
        event.add_callback(_enable, "exaile_loaded")
    else:
        _enable(None, exaile, None)

def _enable(device, exaile, nothing):
    global DOUBANFM
    username = settings.get_option("plugin/douban_radio/username")  
    password = settings.get_option("plugin/douban_radio/password")
    DOUBANFM = DoubanRadioPlugin(exaile, username, password)


def disable(exaile):
    global DOUBANFM
    DOUBANFM.destroy(exaile)
    pass

def get_prefs_pane():
    return dbfm_pref


class DoubanRadioPlugin(object):
    channels = {_('Personalized'):0, _('Mandarin'):1, _('Western'):2, 
            _('Cantonese'): 6, _('70s'): 3, _('80s'): 4, _('90s'): 5}

    @common.threaded
    def __init__(self, exaile, username ,password):
        
        self.doubanfm = DoubanRadio(username, password)
        self.exaile = exaile
        self.__create_menu_item__()

        self.__register_events()
        self.doubanfm_mode = DoubanfmMode(self.exaile, self)


    def __register_events(self):
        event.add_callback(self.check_to_load_more, 'playback_player_start')
        event.add_callback(self.close_playlist, 'quit_application')
        event.add_callback(self.play_feedback, 'playlist_current_changed')
        event.add_callback(self.user_feedback, 'doubanfm_track_rating_change')

    def __unregister_events(self):
        event.remove_callback(self.check_to_load_more, 'playback_player_start')
        event.remove_callback(self.close_playlist, 'quit_application')
        event.remove_callback(self.play_feedback, 'playlist_current_changed')
        event.remove_callback(self.user_feedback, 'doubanfm_track_rating_change')

    def user_feedback(self, type, track, rating_pair) :
        prev_rating, rating = rating_pair
        if rating == 1:
            ## mark to recycle
            self.mark_as_recycle(track)
        if rating == 2 and prev_rating != 2:
            self.mark_as_skip(track)
        if prev_rating == 5 and rating < 5:
            ## mark to dislike
            self.mark_as_dislike(track)
        if rating == 5 and prev_rating < 5:
            ## mark to like
            self.mark_as_like(track)

    def is_douban_track(self, track):
        return isinstance(track, DoubanFMTrack)

    @common.threaded
    def mark_as_skip(self, track):
        playlist = self.get_current_playlist()

        rest_sids = self.get_rest_sids(playlist)

        ## play next song
        self.exaile.gui.main.queue.next()

        sid = track.sid
        aid = track.aid
        songs = self.doubanfm.skip_song(sid, aid, history=self.get_history_sids(playlist))
        if self.get_tracks_remain() < 15:
            tracks = map(self.create_track_from_douban_song, songs)

            playlist.add_tracks(tracks)
        track.set_rating2(2)

    @common.threaded
    def mark_as_like(self, track):
        sid = track.sid
        aid = track.aid
        self.doubanfm.fav_song(sid, aid)
        track.set_rating2(5)

    @common.threaded
    def mark_as_dislike(self, track):
        sid = track.sid
        aid = track.aid

        self.doubanfm.unfav_song(sid, aid)
        track.set_rating2(3)

    @common.threaded
    def mark_as_recycle(self, track):
        playlist = self.get_current_playlist()

        rest_sids = self.get_rest_sids(playlist)

        ## play next song
        self.exaile.gui.main.queue.next()

        ## remove the track
        self.remove_current_track()

        sid = track.sid
        aid = track.aid
        songs = self.doubanfm.del_song(sid, aid, rest=rest_sids)
        if self.get_tracks_remain() < 15:
            tracks = map(self.create_track_from_douban_song, songs)

            playlist.add_tracks(tracks)
        track.set_rating2(1)

    def get_rest_sids(self, playlist):
        playlist = self.get_current_playlist()

        current_tracks = playlist.get_tracks()
        rest_tracks = current_tracks[playlist.get_current_pos()+1:]
        rest_sids = self.tracks_to_sids(rest_tracks)
        return rest_sids

    def get_tracks_remain(self):
        pl = self.exaile.gui.main.get_current_playlist().playlist
        total = len(pl.get_tracks())
        cursor = pl.get_current_pos()
        return total-cursor

    def get_selected_track(self):
        self.exaile.gui.main.get_current_playlist().get_selected_track()

    def get_current_track(self):
        pl = self.exaile.gui.main.get_current_playlist().playlist
        return pl.get_tracks()[pl.get_current_pos()]

    def remove_current_track(self):
        self.exaile.gui.main.get_current_playlist().remove_selected_tracks()

    def tracks_to_sids(self, tracks):
        return map(lambda t: t.sid, tracks)

    @common.threaded
    def play_feedback(self, type, playlist, current_track):
        if isinstance(playlist, DoubanFMPlaylist) and isinstance(self.last_track, DoubanFMTrack):
            track = self.last_track
            sid = track.sid
            aid = track.aid
            if sid is not None and aid is not None:
                self.doubanfm.played_song(sid, aid)
            self.last_track = current_track

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
            if playlist.index(track) == len(playlist.get_tracks())-1:
                self.load_more(playlist)

    def get_history_sids(self, playlist):
        current_tracks = playlist.get_ordered_tracks()
        sids = self.tracks_to_sids(current_tracks)
        return sids

    def load_more(self, playlist):
        sids = self.get_history_sids(playlist)
        retry = 0
        while retry < 3:
            try:
                songs = self.doubanfm.played_list(sids)
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
        
        self.menuItem = gtk.MenuItem(_('Open Douban.fm'))
        menu = gtk.Menu()
        self.menuItem.set_submenu(menu)

        for channel_name  in self.channels.keys():
            menuItem = gtk.MenuItem(_(channel_name))

            menuItem.connect('activate', self.active_douban_radio, channel_name)
            
            menu.prepend(menuItem)
            menuItem.show()

#       self.menu.connect('activate', self.active_douban_radio, self.exaile)

        exaile.gui.builder.get_object('file_menu').insert(self.menuItem, 5)

        self.menuItem.show()

        self.modeMenuItem = gtk.MenuItem(_('DoubanFM mode'))
        key, modifier = gtk.accelerator_parse('<Control><Alt>D')
        self.accels = gtk.AccelGroup()
        self.modeMenuItem.add_accelerator('activate', self.accels, key, modifier, gtk.ACCEL_VISIBLE)
        self.exaile.gui.main.window.add_accel_group(self.accels)
        self.modeMenuItem.connect('activate', self.show_mode)
        exaile.gui.builder.get_object('view_menu').append(self.modeMenuItem)
        self.modeMenuItem.show()
    
    def create_track_from_douban_song(self, song):
        uri = song['url']

        track = DoubanFMTrack(uri, song['sid'], song['aid'], song['like'])
        track.set_tag_raw('title', song['title'])
        track.set_tag_raw('artist', song['artist'])
        track.set_tag_raw('album', song['albumtitle'])
        track.set_tag_raw('cover_url', song['picture'])

        return track

    def show_mode(self, *e):
        self.doubanfm_mode.show()

    def create_playlist(self, name, initial_tracks=[]):
        ## to update in 0.3.2 
        ## plist = DoubanFMPlaylist(name, initial_tracks)
        plist = DoubanFMPlaylist(name)
        plist.set_ordered_tracks(initial_tracks)

        ## set_shuffle_mode('disabled')
        plist.set_random(False)
        ## set_repeat_mode('disabled')
        plist.set_repeat(False)
        ## set_dynamic_mode('disabled')
        plist.set_dynamic(False)

        return plist

    def active_douban_radio(self, type, channel_name):
        channel_id = self.channels[channel_name]    

        self.doubanfm.set_channel(channel_id)
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
        plist = self.create_playlist(
                _('DoubanFM')+" "+channel_name, tracks)
        
        self.exaile.gui.main.add_playlist(plist)
#       self.play(plist)

        self.last_track = plist.get_ordered_tracks()[0]

#       self.doubanfm_mode.show()

    def destroy(self, exaile):
        if self.menuItem :
            exaile.gui.builder.get_object('file_menu').remove(self.menuItem)
        if self.modeMenuItem:
            exaile.gui.builder.get_object('view_menu').remove(self.modeMenuItem)
            exaile.gui.main.remove_accel_group(self.accels)
        self.__unregister_events()

        self.doubanfm_mode.destroy()
        pass
        
class DoubanFMPlaylist(playlist.Playlist):
    def __init__(self, name):
        playlist.Playlist.__init__(self, name)
        pass

class DoubanFMTrack(trax.Track):
    def __init__(self, uri, sid, aid, fav):
        trax.Track.__init__(self, uri)
        self.sid = sid
        self.aid = aid

        if fav == "1":
            trax.Track.set_rating(self, 5)
        else:
            trax.Track.set_rating(self, 3)

    def set_rating(self, rating):
        prev_rating = trax.Track.get_rating(self)
        trax.Track.set_rating(self, rating)
        
        event.log_event('doubanfm_track_rating_change', 
                self, (prev_rating, rating))

    def set_rating2(self, rating):
        trax.Track.set_rating(self, rating)
    
        
