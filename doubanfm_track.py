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

from xl import trax

class DoubanFMTrack(object):
    def __init__(self, uri, aid, sid, fav):
        self._track = trax.Track(uri)
        self._sid = sid
        self._aid = aid
        self._fav = fav

        self.bind_douban_tags(self._track, aid, sid, uri, fav)

    @classmethod
    def is_douban_track(self, track):
        return track.get_tag_raw('_DoubanFM_') is not None

    @property
    def sid(self):
        return self._sid

    @property
    def aid(self):
        return self._aid

    @property
    def fav(self):
        return self._fav

    @property
    def track(self):
        return self._track

    def bind_douban_tags(self, track, aid, sid, uri, fav):
        self._track.set_tag_raw('aid', aid)
        self._track.set_tag_raw('sid', sid)
        self._track.set_tag_raw('uri', uri)
        self._track.set_tag_raw('fav', fav or '0')
        self._track.set_tag_raw('_DoubanFM_', True)

    def set_tag_raw(self, name, value):
        self._track.set_tag_raw(name, value)

    def get_tag_raw(self, name):
        self._track.get_tag_raw(name)[0]
 
