# -*- coding: utf8 -*-
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
import pango
import cairo
import os

from xl import xdg, event, settings
from xlgui import cover, guiutil, tray
from xlgui.main import PlaybackProgressBar
from xlgui.widgets import info

from doubanfm_track import DoubanFMTrack

def get_resource_path(filename):
    basedir = os.path.dirname(os.path.realpath(__file__))
    resource = os.path.join(basedir, filename)
    return resource

class DoubanFMMode():
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
            'on_item_setting_clicked': self.on_button_setting_clicked,
            'on_item_album_clicked': self.on_button_album_clicked,
            'on_item_report_clicked': self.on_button_report_clicked,
            'on_menu_toggle': self.on_menu_toggle,
        })

        self.window = self.builder.get_object('doubanfm_mode_window')
        self.window.connect('destroy', self.hide)

        volume = settings.get_option('player/volume', 1)

        self.volume_control = guiutil.VolumeControl()
        self.builder.get_object('hbox2').pack_start(self.volume_control)

        self.cover_box = self.builder.get_object('cover_eventbox1')
        self.info_area = info.TrackInfoPane(auto_update=True)
        self.cover = cover.CoverWidget(self.cover_box)
#        self.cover_box.add(self.cover)

        self.track_title_label = self.builder.get_object('track_title_label')
        attr = pango.AttrList()
        attr.change(pango.AttrWeight(pango.WEIGHT_BOLD, 0, 800))
        attr.change(pango.AttrSize(12500, 0, 600))
        self.track_title_label.set_attributes(attr)
        self.track_info_label = self.builder.get_object('track_info_label')

        self.bookmark_button = self.builder.get_object('bookmark_button')
        self.trash_button = self.builder.get_object('delete_button')

        self.popup_menu = self.builder.get_object('moremenu')

        progress_box = self.builder.get_object('playback_progressbar')
        self.progress_bar = PlaybackProgressBar(
            progress_box, self.exaile.player
        )

        self.visible = False
        self.active = False

        event.add_callback(self.on_playback_start, 'playback_track_start', self.exaile.player)
        self._toggle_id = self.exaile.gui.main.connect('main-visible-toggle', self.toggle_visible)

        ## added for 0.3.2
        self._init_alpha()

    def _init_alpha(self):
        if settings.get_option('gui/use_alpha', False):
            screen = self.window.get_screen()
            colormap = screen.get_rgba_colormap()

            if colormap is not None:
                self.window.set_app_paintable(True)
                self.window.set_colormap(colormap)

                self.window.connect('expose-event', self.on_expose_event)
                self.window.connect('screen-changed', self.on_screen_changed)

    def on_expose_event(self, widget, event):
        """
            Paints the window alpha transparency
        """
        opacity = 1 - settings.get_option('gui/transparency', 0.3)
        context = widget.window.cairo_create()
        background = widget.style.bg[gtk.STATE_NORMAL]
        context.set_source_rgba(
            float(background.red) / 256**2,
            float(background.green) / 256**2,
            float(background.blue) / 256**2,
            opacity
        )
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.paint()

    def on_screen_changed(self, widget, event):
        """
            Updates the colormap on screen change
        """
        screen = widget.get_screen()
        colormap = screen.get_rgba_colormap() or screen.get_rgb_colormap()
        self.window.set_colormap(rgbamap)

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
        if not DoubanFMTrack.is_douban_track(track):
            return

        if track.get_tag_raw("fav")[0] == "1":
            self.dbfm_plugin.mark_as_dislike(track)
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('bookmark-new', gtk.ICON_SIZE_BUTTON))
        else :
            self.dbfm_plugin.mark_as_like(track)
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('emblem-favorite', gtk.ICON_SIZE_BUTTON))

    def on_skip_button_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if not DoubanFMTrack.is_douban_track(track):
            return
        self.dbfm_plugin.mark_as_skip(track)

    def on_delete_button_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if not DoubanFMTrack.is_douban_track(track):
            return
        self.dbfm_plugin.mark_as_recycle(track)

    def on_go_home_button_clicked(self, *e):
        self.hide(e)

    def on_playback_start(self, type, player, data):
        track = player.current
        artist = track.get_tag_raw('artist')[0]
        album = track.get_tag_raw('album')[0]
        title = track.get_tag_raw('title')[0]

        self.window.set_title(u"\u8c46\u74e3\u7535\u53f0 %s - %s Exaile" % (title, artist))
        self.track_title_label.set_label("%s - %s" %(title, artist))
        self.track_info_label.set_label(album)
        
        if track.get_tag_raw('fav')[0] == "1":
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('emblem-favorite', gtk.ICON_SIZE_BUTTON))
        else:
            self.bookmark_button.set_image(
                    gtk.image_new_from_icon_name('bookmark-new', gtk.ICON_SIZE_BUTTON))

        ## recent change from official client, you can only trash 
        ## song in personal channel
        self.trash_button.set_sensitive(self.dbfm_plugin.get_current_channel() == 0)

    def on_button_setting_clicked(self, *e):
        os.popen(' '.join(['xdg-open', 'http://douban.fm/mine']))	

    def on_button_album_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if track is not None:
            aid = track.get_tag_raw('aid')[0]
            url = "http://music.douban.com/subject/%s/" % aid
            os.popen(' '.join(['xdg-open', url]))

    def on_button_report_clicked(self, *e):
        track = self.dbfm_plugin.get_current_track()
        if track is not None:
            aid = track.get_tag_raw('aid')[0]
            sid = track.get_tag_raw('sid')[0]
            url = "http://music.douban.com/subject/%s/report?song_id=%s" % (aid, sid)
            os.popen(' '.join(['xdg-open', url]))

    def destroy(self):
        self.window.destroy()
        event.remove_callback(self.on_playback_start, 'playback_track_start')
        self.exaile.gui.main.disconnect(self._toggle_id)

    def on_menu_toggle(self, widget, e):
        self.popup_menu.popup(None, None, None, e.button, e.time)
        return True


