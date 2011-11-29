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

import gtk
import gtk.glade

import urllib

from doubanfm_mode import get_resource_path

class CaptchaDialog():
    def __init__(self, doubanfm_plugin):
        self.dbfm_plugin = doubanfm_plugin

        self.builder = gtk.Builder()
        self.builder.add_from_file(get_resource_path('captcha.ui'))

        self.builder.connect_signals({
            'on_ok_button_clicked': self.on_ok_button_clicked})
        self.dialog = self.builder.get_object('dialog1')
        self.image = self.builder.get_object('image1')
        self.text = self.builder.get_object('entry1')

    def show(self):
        self.text.set_text('')
        self.dialog.show_all()

    def hide(self):
        self.dialog.hide()
    
    def on_ok_button_clicked(self, *e):
        solution = self.text.get_text()
        self.hide()
        self.dbfm_plugin.do_init(self.captcha_id, solution)

    def set_captcha(self, captcha_id, captcha_url):
        self.captcha_id = captcha_id
        self.captcha_url = captcha_url
        self.show_image(captcha_url)

    def show_image(self, captcha_url):
        response = urllib.urlopen(captcha_url)
        loader = gtk.gdk.PixbufLoader()
        loader.write(response.read())
        loader.close()        
        self.image.set_from_pixbuf(loader.get_pixbuf())


        
