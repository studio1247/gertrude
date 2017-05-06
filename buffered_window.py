# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import wx


class BufferedWindow(wx.Window):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Window.__init__(self, parent, id, pos, size, style)
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.ForceRefresh()

    def Draw(self, dc):
        pass

    def OnSize(self, event):
        self.width, self.height = self.GetClientSizeTuple()
        self.bufferDC = wx.EmptyBitmap(self.width, self.height)
        self.needs_drawing = True
        self.Refresh()

    def OnPaint(self, event):
        if self.needs_drawing:
            self.UpdateDrawing()
            self.needs_drawing = False
        dc = wx.BufferedPaintDC(self, self.bufferDC)
            
    def ForceRefresh(self):
        self.OnSize(None)
        
    def UpdateDrawing(self):
        dc = wx.BufferedDC(wx.ClientDC(self), self.bufferDC)
        self.Draw(dc)
