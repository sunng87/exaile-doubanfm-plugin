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

import glib
import gio
from xl import covers

class DoubanFMCover(covers.CoverSearchMethod):
    name = 'doubanfm'
    type = 'remote'

    def __init__(self):
        super(DoubanFMCover, self).__init__()
        
    def find_covers(self, track, limit=-1):
        if track.get_tag_raw('cover_url') is not None :
            return track.get_tag_raw('cover_url')
        else:
            return []

    def get_cover_data(self, url):
        try:
            handler = gio.File(url).read()
            data = handler.read()
            return data
        except glib.GError:
            return None      
        

