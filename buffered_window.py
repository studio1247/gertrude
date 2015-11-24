import wx

class BufferedWindow(wx.Window):
    def __init__(self, parent,
                 id = -1,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE):
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
