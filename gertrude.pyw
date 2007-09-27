#!/usr/bin/env python
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

import __builtin__
import os, sys, time, shutil, glob, wx
from common import *
from data import Backup, Load, Save
from startdialog import StartDialog

VERSION = '0.37'

__builtin__.history = []

class HtmlListBox(wx.HtmlListBox):
    def __init__(self, parent, id, size, style):
        wx.HtmlListBox.__init__(self, parent, id, size=size, style=style)
        self.items = []

    def OnGetItem(self, n):
        return self.items[n]

    def Append(self, html):
        self.items.append(html)

    def Draw(self):
        self.SetItemCount(len(self.items))
        self.SetSelection(0)
        self.SetFocus()

class Listbook(wx.Panel):
    def __init__(self, parent, id, style, pos):
        wx.Panel.__init__(self, parent, id=id, pos=pos)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.list_box = HtmlListBox(self, -1, size=(155, 250), style=wx.BORDER_SUNKEN)
        self.sizer.Add(self.list_box, 0, wx.EXPAND)
        self.list_box.Bind(wx.EVT_LISTBOX, self.OnPageChanged)
        self.panels = []
        self.active_panel = None
        self.SetSizer(self.sizer)

    def AddPage(self, panel, bitmap):
        self.list_box.Append('<center><img src="%s"></center>' % bitmap)
        self.panels.append(panel)
        self.sizer.Add(panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        if len(self.panels) == 1:
            self.active_panel = panel
        else:
            self.sizer.Show(panel, False)

    def Draw(self):
        self.list_box.Draw()

    def OnPageChanged(self, event):
        if self.active_panel:
            self.sizer.Show(self.active_panel, False)
        self.active_panel = self.panels[event.GetSelection()]
        self.sizer.Show(self.active_panel, True)
        self.sizer.Layout()

    def GetPage(self, n):
        return self.panels[n]

class GertrudeListbook(Listbook):
    def __init__(self, parent, id=-1):
        Listbook.__init__(self, parent, id=-1, style=wx.LB_DEFAULT, pos=(10, 10))
        panels = []
        for filename in glob.glob('panel_*.py'):
            module_name = os.path.split(filename)[1][:-3]
            print 'importing panel %s' % module_name
            panels.extend([tmp(self) for tmp in __import__(module_name).panels])
        panels.sort(lambda a, b: a.index-b.index)
        for panel in panels:            
            if panel.profil & profil:
                self.AddPage(panel, panel.bitmap)
        self.Draw()

    def OnPageChanged(self, event):
        Listbook.OnPageChanged(self, event)
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def UpdateContents(self):
        self.GetPage(self.list_box.GetSelection()).UpdateContents()

class GertrudeFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Gertrude v%s" % VERSION, wx.DefaultPosition, wx.Size(1000, 750))

        # Icon
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Statusbar
        self.CreateStatusBar()

        # Toolbar
        tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        tb.SetToolBitmapSize(wx.Size(24, 24))
        tb.AddSimpleTool(ID_SYNCHRO, wx.BitmapFromImage(wx.Image("./bitmaps/reload.png", wx.BITMAP_TYPE_PNG)), "Synchroniser")
        tb.AddSimpleTool(ID_UNDO, wx.BitmapFromImage(wx.Image("./bitmaps/undo.png", wx.BITMAP_TYPE_PNG)), "Undo")
        self.Bind(wx.EVT_TOOL, self.onToolbarButton)
        tb.Realize()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self, -1)
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.listbook = GertrudeListbook(panel)
        sizer2.Add(self.listbook, 1, wx.EXPAND)
        panel.SetSizer(sizer2)

        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def OnExit(self, evt):
        self.SetStatusText("Fermeture en cours ....")
        Save()
        self.Destroy()

    def onToolbarButton(self, event):
        evtId = event.GetId()
        if evtId == ID_UNDO:
            if len(history) > 0:
                for obj, member, value in history.pop(-1):
                    exec('obj.%s = value' % member)
                self.listbook.UpdateContents()
        elif evtId == ID_SYNCHRO:
            dlg = SynchroDialog(self, creche.server_url)
            dlg.CenterOnScreen()
            val = dlg.ShowModal()
            dlg.Destroy()
            if val == ID_SYNCHRO:
                __builtin__.creche = Load()
                self.listbook.UpdateContents()


class MyApp(wx.App):
    def OnInit(self):
        start_dialog = StartDialog(GertrudeFrame)
        start_dialog.Show(True)
        return True

if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()

