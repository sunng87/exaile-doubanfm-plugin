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

from dbradioapi import DoubanRadio

import gtk

from xl import common, event, main, playlist, xdg, settings
from xl.radio import *
from xl.nls import gettext as _
from xlgui import guiutil
from xlgui.widgets import dialogs


def enable(exaile):
	if exaile.loading:
		exaile.add_callback(_enable, "exaile_loaded")
	else:
		_enable(None, exaile, None)

def _enable(device, exaile, nothing):
	username = settings.get_option("plugin/douban_radio/username")	
	password = settings.get_option("plugin/douban_radio/password")
	drp = DoubanRadioPlugin(exaile, username, password)
	pass


def disable(exaile):
	pass

def get_preferences_pane():
	return doubanfm_settings


class DoubanRadioPlugin(object):
	def __init__(self, exaile, username ,password):
		
		self.doubanfm = DoubanRadio(username, password)
		self.exaile = exaile
		self.__create_menu_item__()

	def __create_menu_item__(self):
		self.menuItem = gtk.MenuItem(_('Douban Radio'))
		self.menuItem.connect('activate', self.active_douban_radio, exaile)

		exaile.gui.builder.get_object('files_menu').insert(self.menuItem, 4)

		self.menuItem.show()

	def active_douban_radio(exaile):
		pass
		
		



