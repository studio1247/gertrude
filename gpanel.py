import sys
import wx, wx.lib.stattext

class GPanel(wx.Panel):
    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent, style=wx.LB_DEFAULT)
	self.sizer = wx.BoxSizer(wx.VERTICAL)
	sizer = wx.BoxSizer(wx.HORIZONTAL)
	if sys.platform == 'win32':
            st = wx.StaticText(self, -1, title, size=(-1, 24), style=wx.BORDER_SUNKEN|wx.ST_NO_AUTORESIZE)
        else:    
            st = wx.lib.stattext.GenStaticText(self, -1, title, size=(-1, 24), style=wx.BORDER_SUNKEN|wx.ST_NO_AUTORESIZE)
        st.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        st.SetBackgroundColour(wx.Colour(10, 36, 106))
        st.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        st.SetForegroundColour(wx.Colour(255, 255, 255))
	sizer.Add(st, 1, wx.EXPAND)
	self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM, 5)
	self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
    def UpdateContents(self):
        pass
