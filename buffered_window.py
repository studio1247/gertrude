import wx

USE_BUFFERED_DC = 1

class BufferedWindow(wx.Window):
    def __init__(self, parent,
                 id = -1,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Window.__init__(self, parent, id, pos, size, style)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.OnSize(None)

    def Draw(self, dc):
        pass

    def OnSize(self, event):
        self.width, self.height = self.GetClientSizeTuple()
        self.bufferDC = wx.EmptyBitmap(self.width, self.height)
        self.UpdateDrawing()

    def OnPaint(self, event):
        if USE_BUFFERED_DC:
            dc = wx.BufferedPaintDC(self, self.bufferDC)
        else:
            dc = wx.PaintDC(self)
            dc.DrawBitmap(self.bufferDC, 0, 0)

    def UpdateDrawing(self):
        if USE_BUFFERED_DC:
            dc = wx.BufferedDC(wx.ClientDC(self), self.bufferDC)
            self.Draw(dc)
        else:
            dc = wx.MemoryDC()
            dc.SelectObject(self.bufferDC)
            self.Draw(dc)
            wx.ClientDC(self).Blit(0, 0, self.width, self.height, dc, 0, 0)
