# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import __builtin__
import time, thread
import wx, wx.lib, wx.lib.newevent
from constants import *
from functions import *
from config import LoadConfig, Load, Exit

class StartDialog(wx.Dialog):
    def __init__(self, frame):
        self.loaded = False
        self.frame = frame
        wx.Dialog.__init__(self, None, -1, "Gertrude")
        
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO )
        self.SetIcon(icon)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        bmp = wx.StaticBitmap(self, -1, wx.Bitmap("./bitmaps/splash_gertrude.png", wx.BITMAP_TYPE_PNG), style=wx.SUNKEN_BORDER)
        self.sizer.Add(bmp, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.info = wx.TextCtrl(self, -1, u"Démarrage ...\n", size=(-1, 50), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.sizer.Add(self.info, 0, wx.EXPAND|wx.ALL, 5)
        self.gauge = wx.Gauge(self, -1, 100, style=wx.GA_SMOOTH)
        self.sizer.Add(self.gauge, 0, wx.EXPAND|wx.ALL, 5)
        
        self.creche_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.creche_sizer.AddGrowableCol(1, 1)
        self.creche_ctrl = wx.Choice(self)
        self.creche_sizer.AddMany([(wx.StaticText(self, -1, "Structure :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.creche_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.creche_ctrl)
        self.sizer.Add(self.creche_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Hide(self.creche_sizer)
        
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.login_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.login_ctrl)
        self.login_ctrl.SetHelpText("Entrez votre identifiant")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Identifiant :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.login_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.passwd_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD|wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.passwd_ctrl)
        self.passwd_ctrl.SetHelpText("Entrez votre mot de passe")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Mot de passe :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.passwd_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Hide(self.fields_sizer)
        
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, btn)
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL, "Annuler")
        self.btnsizer.AddButton(btn)
        self.Bind(wx.EVT_BUTTON, self.OnExit, btn)
        self.btnsizer.Realize()       
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        self.sizer.Hide(self.btnsizer)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
        W, H = wx.ScreenDC().GetSizeTuple()
        w, h = self.sizer.GetSize()
        self.SetPosition(((W-w)/2, (H-h)/2 - 50))

        __builtin__.force_token = False
        self.LoadedEvent, EVT_PROGRESS_EVENT = wx.lib.newevent.NewEvent()
        self.Bind(EVT_PROGRESS_EVENT, self.OnLoaded)
        thread.start_new_thread(self.Load, ())

    def OnLoaded(self, event):
        if event.result is False:
            self.info.AppendText("Erreur lors du chargement !\n")
            self.gauge.SetValue(100)
            return
        
        if event.result is None:
            self.sizer.Hide(self.gauge)
            self.info.AppendText("Choix de la structure ...\n")
            self.sizer.Show(self.creche_sizer)
            for section in config.databases.keys():
                self.creche_ctrl.Append(section)
            if config.default_database:
                self.creche_ctrl.SetStringSelection(config.default_database)
            else:
                self.creche_ctrl.SetSelection(0)
            self.sizer.Show(self.btnsizer)
            self.creche_ctrl.SetFocus()
            self.sizer.Layout()
            self.sizer.Fit(self)
            return

        if readonly:
            dlg = wx.MessageDialog(self,
                                   u"Le jeton n'a pas pu être pris. Gertrude sera accessible en lecture seule. Voulez-vous forcer la prise du jeton ?",
                                   'Gertrude',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                __builtin__.force_token = True
                thread.start_new_thread(self.Load, ())
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
            self.login_ctrl.SetFocus()
            self.sizer.Layout()
            self.sizer.Fit(self)
    
    def Load(self, section=None):
        time.sleep(1)
        try:
            if section is None:
                LoadConfig(ProgressHandler(self.info.AppendText, self.gauge, 5))
                if config.connection is None:
                    wx.PostEvent(self, self.LoadedEvent(result=None))
                    return
            result = Load(ProgressHandler(self.info.AppendText, self.gauge, 95))
        except Exception, e:
            try:
                self.info.AppendText(str(e) + u'\n')
            except:
                self.info.AppendText(u'Erreur : %s\n' % unicode(e))
            result = False
        # we close database since it's opened from an other thread
        try:
            sql_connection.close()
        except:
            pass
        time.sleep(1)
        self.gauge.SetValue(100)
        wx.PostEvent(self, self.LoadedEvent(result=result))

    def StartFrame(self):
        self.frame(self.info).Show()
        self.Destroy()

    def OnOk(self, evt):
        if config.connection is None:
            self.sizer.Hide(self.creche_sizer)
            self.sizer.Hide(self.btnsizer)
            self.sizer.Show(self.gauge)
            self.sizer.Layout()
            self.sizer.Fit(self)
            section = self.creche_ctrl.GetStringSelection()
            self.info.AppendText(u"Structure %s sélectionnée...\n" % section)
            config.default_database = section
            
            config.connection = config.databases[section].connection
            thread.start_new_thread(self.Load, (section, ))
            return
            
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
            Exit(ProgressHandler(self.info.AppendText, self.gauge, 100))
        self.Destroy()
