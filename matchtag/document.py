# -*- coding: utf-8 -*-
# Copyright (C) 2013 Giedrius Slavinskas (giedrius.slavinskas@gmail.com)
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
# Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA 02111-1307, USA.

import os
from gi.repository import GObject, Gdk, Gtk, Gedit, PeasGtk
from matcher import Matcher

SUPPORTED_LANGUAGES = ('xml', 'html')
TAG_BACKGROUND = 'blue'

class MatchTagViewActivatable(GObject.Object, Gedit.ViewActivatable):
    __gtype_name__ = "MatchTagViewActivatable"

    view = GObject.property(type=Gedit.View)

    def __init__(self):
        GObject.Object.__init__(self)
        self.lang = None
        self.handler_cursor_moved = None
        self.handler_notify_lang = None
        self.matcher = None
        self.tag_match = None

    def do_activate(self):
        buf = self.view.get_buffer()
        self.tag_match = buf.create_tag('tag-match', background=TAG_BACKGROUND)
        self.matcher = Matcher(self.view, self.tag_match)
        self.update_language()
        self.handler_notify_lang = buf.connect('notify::language',
                                               self.on_notify_language)

    def do_deactivate(self):
        buf = self.view.get_buffer()
        buf.disconnect(self.handler_notify_lang)
        if self.handler_cursor_moved:
            buf.disconnect(self.handler_cursor_moved)
        matcher = None

    def do_update_state(self):
        pass

    def update_language(self):
        buf = self.view.get_buffer()
        lang = buf.get_language()
        self.lang = lang.get_id() if lang else None
        if not self.lang or self.lang not in SUPPORTED_LANGUAGES:
            if self.handler_cursor_moved:
                buf.disconnect(self.handler_cursor_moved)
            return
        self.handler_cursor_moved = buf.connect('cursor-moved',
                                                self.on_cursor_moved)

    def on_cursor_moved(self, buf):
        if self.matcher:
            self.matcher.cursor_moved()

    def on_notify_language(self, buf, spec):
        self.update_language()
