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
import wx, wx.lib, wx.lib.delayedresult
from common import *
from data import Backup, Load, Save

class StartDialog(wx.Dialog):
    def __init__(self, frame):
        self.loaded = False
        self.frame = frame
        wx.Dialog.__init__(self, None, -1, "Gertrude", wx.DefaultPosition, wx.DefaultSize)

        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO )
        self.SetIcon(icon)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        bmp = wx.StaticBitmap(self, -1, wx.Bitmap("./bitmaps/splash_gertrude.png", wx.BITMAP_TYPE_PNG), style=wx.SUNKEN_BORDER)
        self.sizer.Add(bmp, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.info = wx.TextCtrl(self, -1, u"Démarrage ...\n", size=(-1, 50), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.sizer.Add(self.info, 0, wx.EXPAND|wx.ALL, 5)
        self.gauge_intervals = [(0, 100)]
        self.gauge = wx.Gauge(self, -1, 100, style=wx.GA_SMOOTH)
        self.sizer.Add(self.gauge, 0, wx.EXPAND|wx.ALL, 5)
        
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.login_ctrl = wx.TextCtrl(self)
        self.login_ctrl.SetHelpText("Entrez votre identifiant")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Identifiant :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.login_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.passwd_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.passwd_ctrl.SetHelpText("Entrez votre mot de passe")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Mot de passe :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.passwd_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Hide(self.fields_sizer)
        
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, btn)
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        self.btnsizer.AddButton(btn)
        self.Bind(wx.EVT_BUTTON, self.OnExit, btn)
        self.btnsizer.Realize()       
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.sizer.Hide(self.btnsizer)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

        wx.lib.delayedresult.startWorker(self.OnLoaded, self.Load)
   
    def handler(self, count=None, msg=None, max=None):
        if msg:
            self.info.AppendText(msg + "\n")
        if max is not None:
            self.gauge_intervals.append((self.gauge.GetValue(), self.gauge.GetValue() + (self.gauge_intervals[-1][1]-self.gauge_intervals[-1][0]) * max / 100))
            return self.handler
        if count:
            interval = self.gauge_intervals[-1]
            self.gauge.SetValue(interval[0] + (interval[1]-interval[0]) * count / 100)
            if count == 100:
                self.gauge_intervals.pop(-1)

    def OnLoaded(self, event):
        try:
            result = event.get()
        except Exception, e:
            self.info.AppendText(str(e))
            self.gauge.SetValue(100)
            return

        if not result:
            self.info.AppendText("Erreur lors du chargement !\n")
            self.gauge.SetValue(100)
            return

        self.loaded = True
        sql_connection.open()
        if len(creche.users) == 0:
            __builtin__.profil = PROFIL_ALL
            self.StartFrame()
        else:
            self.sizer.Hide(self.gauge)
            self.info.AppendText("Identification ...\n")
            self.sizer.Show(self.fields_sizer)
            self.sizer.Show(self.btnsizer)

            self.sizer.Layout()
            self.sizer.Fit(self)
        
    def Load(self):
        Backup(self.handler(max=10))
        if not Load(self.handler(max=80)):
            return False
        # we close database since it's opened from an other thread
        sql_connection.close()
        return True

    def StartFrame(self):
        self.Destroy()
        self.frame().Show()

    def OnOk(self, evt):
        login = self.login_ctrl.GetValue()
        password = self.passwd_ctrl.GetValue()

        for user in creche.users:
            if login == user.login and password == user.password:
                __builtin__.profil = user.profile
                self.StartFrame()
                return
        else:
            self.login_ctrl.Clear()
            self.passwd_ctrl.Clear()
            self.login_ctrl.SetFocus()

    def OnExit(self, evt):
        self.info.AppendText("\nFermeture ...\n")
        if self.loaded:
            Save(self.handler(max=100))
        self.Destroy()
