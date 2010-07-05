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

import gtk
import gtk.glade
import os

from xl import xdg, event, settings
from xlgui import cover, guiutil, tray
from xlgui.main import PlaybackProgressBar

def get_resource_path(filename):
    basedir = os.path.dirname(os.path.realpath(__file__))
    resource = os.path.join(basedir, filename)
    return resource

class DoubanfmMode():
    def __init__(self, exaile, doubanfm_plugin):
        self.exaile = exaile
        self.dbfm_plugin = doubanfm_plugin

        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource_path('doubanfm_mode.ui'))

        self.builder.connect_signals({
            'on_bookmark_button_clicked': self.on_bookmark_button_clicked,
            'on_skip_button_clicked': self.on_skip_button_clicked,
            'on_delete_button_clicked': self.on_delete_button_clicked,
            'on_go_home_button_clicked': self.on_go_home_button_clicked,
            'on_volume_slider_value_changed': self.on_volume_slider_value_changed,
            'on_volume_mute_button_toggled': self.on_volume_mute_button_toggled
        })

        self.window = self.builder.get_object('doubanfm_mode_window')
        self.window.connect('destroy', self.hide)

        volume = settings.get_option('player/volume', 1)
        self.volume_scale = self.builder.get_object('volume_scale')
        self.volume_scale.set_value(volume)

        self.mute_button = guiutil.MuteButton(self.builder.get_object('volume_mute_button'))
        self.mute_button.update_volume_icon(volume)

        self.cover_box = self.builder.get_object('cover_eventbox1')
        self.cover = cover.CoverWidget(self.window, self.exaile.covers, self.exaile.player)
        self.cover_box.add(self.cover)

        self.track_title_label = self.builder.get_object('track_title_label')
        self.track_info_label = self.builder.get_object('track_info_label')

        self.bookmark_button = self.builder.get_object('bookmark_button')

        progress_box = self.builder.get_object('playback_progressbar')
        self.progress_bar = PlaybackProgressBar(
            progress_box, self.exaile.player
        )

        self.visible = False
        self.active = False

        event.add_callback(self.on_playback_start, 'playback_track_start', self.exaile.player)
        self._toggle_id = self.exaile.gui.main.connect('main-visible-toggle', self.toggle_visible)

    def toggle_visible(self, *e):
        if not self.active:
            return False

        if self.visible:
            self.window.hide()
        else:
            self.window.show_all()
        self.visible = not self.visible
        return True

    def show(self, *e):
        if not self.visible:
            self.exaile.gui.main.window.hide()

            self.window.show_all()
            self.visible = True
            self.active = True

    def hide(self, *e):
        if self.visible:
            self.window.hide()
            self.exaile.gui.main.window.show()
            self.visible = False
            self.active = False

    def on_bookmark_button_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if not self.dbfm_plugin.is_douban_track(track):
            return

        if track.get_rating() == 5:
            self.dbfm_plugin.mark_as_dislike(track)
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('bookmark-new', gtk.ICON_SIZE_BUTTON))
        else :
            self.dbfm_plugin.mark_as_like(track)
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('emblem-favorite', gtk.ICON_SIZE_BUTTON))

    def on_skip_button_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if not self.dbfm_plugin.is_douban_track(track):
            return
        self.dbfm_plugin.mark_as_skip(track)

    def on_delete_button_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if not self.dbfm_plugin.is_douban_track(track):
            return
        self.dbfm_plugin.mark_as_recycle(track)

    def on_go_home_button_clicked(self, *e):
        self.hide(e)

    def on_volume_mute_button_toggled(self, *e):
        pass

    def on_volume_slider_value_changed(self, widget):
        settings.set_option('player/volume', widget.get_value())
        pass

    def on_playback_start(self, type, player, data):
        track = player.current
        artist = track.get_tag_raw('artist')[0]
        album = track.get_tag_raw('album')[0]
        title = track.get_tag_raw('title')[0]

        self.window.set_title("%s - %s Exaile" % (title, artist))
        self.track_title_label.set_label("<big><b>%s - %s</b></big>" %(title, artist))
        self.track_info_label.set_label(album)
        
        if track.get_rating() == 5:
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('emblem-favorite', gtk.ICON_SIZE_BUTTON))
        else:
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('bookmark-new', gtk.ICON_SIZE_BUTTON))

    def destroy(self):
        self.window.destroy()
        event.remove_callback(self.on_playback_start, 'playback_track_start')
        self.exaile.gui.main.disconnect(self._toggle_id)


