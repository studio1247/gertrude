# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import wx, wx.lib.stattext

class GPanel(wx.Panel):
    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent, style=wx.LB_DEFAULT)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == 'win32':
            st = wx.StaticText(self, -1, title, size=(-1, 24), style=wx.BORDER_SUNKEN|wx.ST_NO_AUTORESIZE)
            font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        else:
            st = wx.lib.stattext.GenStaticText(self, -1, title, size=(-1, 28), style=wx.BORDER_SUNKEN|wx.ST_NO_AUTORESIZE)
            font = st.GetFont()
            font.SetPointSize(12)
        st.SetFont(font)
        st.SetBackgroundColour(wx.Colour(10, 36, 106))
        st.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        st.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(st, 1, wx.EXPAND)
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, 5)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def UpdateContents(self):
        pass
