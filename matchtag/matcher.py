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


class Matcher(object):

    def __init__(self, view, tag):
        self.view = view
        self.textbuffer = view.get_buffer()
        self.tag = tag
        self.tag_name = tag.get_property('name')

    def cursor_moved(self):
        buf = self.view.get_buffer()
        piter = buf.get_iter_at_mark(buf.get_insert())

        start, end = buf.get_bounds()
        if buf.get_tag_table().lookup(self.tag_name):
            buf.remove_tag_by_name(self.tag_name, start, end)

        left = piter.backward_search('<', 0, None)
        if not left or left[1].get_char() in ('!', '?'):
            return False
        if self.is_comment_area(piter, left):
            return False
        right = piter.backward_search('>', 0, None)
        if right and right[0].compare(left[0]) != -1:
            return False
        # We are on the tag
        closing = piter.forward_search('>', 0, None)
        if not closing:
            return False
        closing[1].backward_chars(2)

        if closing[1].get_char() == '/': # Self closing tag
            return False

        if left[1].get_char() == '/': # Closing Tag
            left[1].forward_char()
            tag_name = self.textbuffer.get_text(left[1], closing[0], False)
            pos = self.find_opening_tag(tag_name, left[0], limit=None)
            if not pos:
                return False
            left[1].backward_chars(2)
            closing[0].forward_char()
            self.textbuffer.apply_tag(self.tag, left[1], closing[0])
            self.textbuffer.apply_tag(self.tag, pos[0], pos[1])

        else: # Opening Tag
            tag_name = self.textbuffer.get_text(left[1], closing[0],
                                                     False)
            tag_name = tag_name.split(' ')[0]
            pos = self.find_closing_tag(tag_name, closing[0], limit=None)

            if not pos:
                return False
            left[1].backward_char()
            closing[0].forward_char()
            self.textbuffer.apply_tag(self.tag, left[1], closing[0])
            self.textbuffer.apply_tag(self.tag, pos[0], pos[1])

        return True

    def _iter_opening_tags(self, tag, textiter, limit=None):
        pos = textiter.backward_search(tag, 0, limit)
        if not (pos and pos[1].get_char() in (' ', '>')):
            return None
        pos[1].backward_char()
        return pos

    def find_closing_tag(self, tag_name, textiter, limit=None):
        closing_tag = '</%s>' % (tag_name,)
        opening_tag = '<%s' % (tag_name,)
        pos = textiter.forward_search(closing_tag, 0, limit)
        if not pos:
            return None
        opening_tags = 0
        pos_ = (pos[0], pos[0])
        while True:
            pos_ = self._iter_opening_tags(opening_tag, pos_[0], textiter)
            if not pos_:
                break
            opening_tags += 1

        while opening_tags:
            pos = pos[1].forward_search(closing_tag, 0, limit)
            if not pos:
                break
            opening_tags -= 1
        if opening_tags > 0:
            return None
        return pos

    def find_opening_tag(self, tag_name, textiter, limit=None):
        piter = textiter.copy()
        closing_tag = '</%s>' % (tag_name,)
        opening_tag = '<%s' % (tag_name,)

        pos = textiter.backward_search(opening_tag, 0, limit)
        if not pos:
            return None
        closing_tags = 0
        pos_ = (textiter, textiter)
        while True:
            pos_ = pos_[0].backward_search(closing_tag, 0, pos[1])
            if not pos_:
                break
            closing_tags += 1

        while closing_tags:
            pos = self._iter_opening_tags(opening_tag, pos[0], limit)
            if not pos:
                break
            closing_tags -= 1
        if closing_tags > 0:
            return None
        pos_ = pos[1].forward_search('>', 0, textiter)
        if not pos_:
            return None
        return (pos[0], pos_[1])

    def is_comment_area(self, textiter, left):
        opening = None
        if left and left[1].get_char() == '!':
            piter = left[0].copy()
            piter.forward_chars(4)
            if self.textbuffer.get_text(left[0], piter, False) == '<!--':
                opening = (left[0], piter)
        if not opening:
            opening = textiter.backward_search('<!--', 0, None)
        if opening:
            closing = textiter.backward_search('-->', 0, None)
            if not closing or closing[0].compare(opening[0]) == -1:
                return True
        return False
