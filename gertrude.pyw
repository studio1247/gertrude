#!/usr/bin/env python

# -*- coding: cp1252 -*-

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
import wx, datetime, sys, shutil
from planning import PlanningPanel
from inscriptions import InscriptionsPanel
from cotisations import CotisationsPanel
from releves import RelevesPanel
from general import GeneralPanel
from admin import AdminPanel
from common import *
from data import Backup, Load, Save

VERSION = '0.36'

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
        self.AddPage(InscriptionsPanel(self), './bitmaps/inscriptions.png')
        self.AddPage(PlanningPanel(self), './bitmaps/presences.png')
        if profil & PROFIL_TRESORIER:
            self.AddPage(CotisationsPanel(self), './bitmaps/facturation.png')
        self.AddPage(RelevesPanel(self), './bitmaps/releves.png')
        if profil & PROFIL_BUREAU:
            self.AddPage(GeneralPanel(self), './bitmaps/creche.png')
        if profil & PROFIL_ADMIN:
            self.AddPage(AdminPanel(self), './bitmaps/administration.png')
        self.Draw()

    def OnPageChanged(self, event):
        Listbook.OnPageChanged(self, event)
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def UpdateContents(self):
        self.GetPage(self.list_box.GetSelection()).UpdateContents()

class GertrudeFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(1000, 750))

        # Icone
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Statusbar
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")

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

class LoginDialog(wx.Dialog):
    def __init__(self):
        wx.Dialog.__init__(self, None, -1, "Identification", wx.DefaultPosition, wx.DefaultSize)

        # Icone
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO )
        self.SetIcon(icon)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        bmp = wx.Bitmap("./bitmaps/splash_gertrude.png", wx.BITMAP_TYPE_PNG)
        bmp32 = wx.StaticBitmap(self, -1, bmp, style=wx.SUNKEN_BORDER)
        sizer.Add(bmp32, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        fields_sizer.AddGrowableCol(1, 1)
        sizer.Add(fields_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.login_ctrl = wx.TextCtrl(self, -1, "", size=(80,-1))
        self.login_ctrl.SetHelpText("Entrez votre identifiant")
        fields_sizer.AddMany([(wx.StaticText(self, -1, "Identifiant :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.login_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        self.passwd_ctrl = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD)
        self.passwd_ctrl.SetHelpText("Entrez votre mot de passe")
        fields_sizer.AddMany([(wx.StaticText(self, -1, "Mot de passe :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.passwd_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.onOkButton, btn)
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        self.Bind(wx.EVT_BUTTON, self.OnExit, btn)
        btnsizer.Realize()       
        sizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def onOkButton(self, evt):
        login = self.login_ctrl.GetValue()
        password = self.passwd_ctrl.GetValue()

        for user in creche.users:
            if login == user.login and password == user.password:
                self.Destroy()
                __builtin__.profil = user.profile
                frame = GertrudeFrame(None, -1, "Gertrude v%s" % VERSION)
                frame.Show()
                return

        self.login_ctrl.Clear()
        self.passwd_ctrl.Clear()
        self.login_ctrl.SetFocus()

    def OnExit(self, evt):
        self.Destroy()
        evt.Skip()

class MyApp(wx.App):
    def OnInit(self):
        if len(creche.users) > 0:
            login_dialog = LoginDialog()
            login_dialog.Show(True)
        else:
            __builtin__.profil = PROFIL_ALL
            frame = GertrudeFrame(None, -1, "Gertrude v%s" % VERSION)
            frame.Show()
        return True

Backup()
Load()
app = MyApp(0)
app.MainLoop()
Save()
