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

	def __create_menu_item__(self):
		exaile = self.exaile
		
		self.menuItem = gtk.MenuItem(_('Open Douban.fm'))
		menu = gtk.Menu()
		self.menuItem.set_submenu(menu)

		for channel_name  in self.channels.keys():
			menuItem = gtk.MenuItem(_(channel_name))
			##TODO bind events here

			menuItem.connect('activate', self.active_douban_radio, channel_name)
			
			menu.prepend(menuItem)
			menuItem.show()

#		self.menu.connect('activate', self.active_douban_radio, self.exaile)

		exaile.gui.builder.get_object('file_menu').insert(self.menuItem, 5)

		self.menuItem.show()
	
	def create_track_from_douban_song(self, song):
		uri = song['url']

		tracks= trax.get_tracks_from_uri(uri)
		if tracks is not None and len(tracks) > 0:
			track = tracks[0]
			track.set_tag_raw('title', song['title'])
			track.set_tag_raw('artist', song['artist'])
			track.set_tag_raw('album', song['albumtitle'])
			track.set_tag_raw('track', song['sid'])
			return track

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
			gtk.MessageDialog(self.exaile.gui.main.window, 0,
					gtk.MESSAFE_ERROR, 
					_('Failed to retrieve playlist, try again.'))
			return

		tracks = map(self.create_track_from_douban_song, songs)
		plist = self.create_playlist(
				_('DoubanFM')+" "+channel_name, tracks)
		
		self.exaile.gui.main.add_playlist(plist)
		self.exaile.player.play(plist.get_ordered_tracks()[0])
		
	def destroy(self, exaile):
		## TODO remove all opened tab
		exaile.gui.builder.get_object('file_menu').remove(self.menuItem)
		pass
		


class DoubanFMPlaylist(playlist.Playlist):
	def __init__(self, name):
		playlist.Playlist.__init__(self, name)
		pass

