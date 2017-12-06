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

from __future__ import unicode_literals

import shutil
import traceback
import bcrypt
import requests
import wx.lib.newevent
from config import CONFIG_FILENAME, DEFAULT_DATABASE, DEMO_DATABASE
from functions import *
from mainwindow import GertrudeFrame
from connection import get_connection_from_config
from progress import *


class StartDialog(wx.Dialog):
    def __init__(self):
        self.loaded = False
        wx.Dialog.__init__(self, None, -1, "Gertrude")
        
        icon = wx.Icon(GetBitmapFile("gertrude.ico"), wx.BITMAP_TYPE_ICO )
        self.SetIcon(icon)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        bmp = wx.StaticBitmap(self, -1, wx.Bitmap(GetBitmapFile("splash_gertrude.png"), wx.BITMAP_TYPE_PNG), style=wx.SUNKEN_BORDER)
        self.sizer.Add(bmp, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.info = wx.TextCtrl(self, -1, "Démarrage ...\n", size=(-1, 70), style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.sizer.Add(self.info, 0, wx.EXPAND | wx.ALL, 5)
        self.gauge = wx.Gauge(self, -1, 100, style=wx.GA_SMOOTH)
        self.sizer.Add(self.gauge, 0, wx.EXPAND | wx.ALL, 5)
        
        self.creche_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.creche_sizer.AddGrowableCol(1, 1)
        self.creche_ctrl = wx.Choice(self)
        self.creche_sizer.AddMany([(wx.StaticText(self, -1, "Structure :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.creche_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.creche_ctrl)
        self.sizer.Add(self.creche_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Hide(self.creche_sizer)
        
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.login_ctrl = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.login_ctrl)
        self.login_ctrl.SetHelpText("Entrez votre identifiant")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Identifiant :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.login_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.passwd_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnOk, self.passwd_ctrl)
        self.passwd_ctrl.SetHelpText("Entrez votre mot de passe")
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Mot de passe :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.passwd_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Hide(self.fields_sizer)
        
        self.btnsizer = wx.StdDialogButtonSizer()
        self.ok_button = wx.Button(self, wx.ID_OK)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.ok_button)
        self.btnsizer.AddButton(self.ok_button)
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

        if sys.platform != "darwin" and not os.path.isfile(CONFIG_FILENAME) and not os.path.isfile(DEFAULT_DATABASE) and os.path.isfile(DEMO_DATABASE):
            dlg = wx.MessageDialog(self,
                                   "Vous utilisez Gertrude pour la première fois, voulez-vous installer une base de démonstration ?",
                                   'Gertrude',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_YES:
                shutil.copy(DEMO_DATABASE, DEFAULT_DATABASE)
                
        self.MessageEvent, EVT_MESSAGE_EVENT = wx.lib.newevent.NewEvent()
        self.Bind(EVT_MESSAGE_EVENT, self.OnMessage)
        wx.CallAfter(self.Load, None)

    def OnLoaded(self, result):
        if result is False:
            self.info.AppendText("Erreur lors du chargement !\n")
            self.SetGauge(100)
            return
                
        if result is None:
            self.sizer.Hide(self.gauge)
            self.info.AppendText("Choix de la structure ...\n")
            self.sizer.Show(self.creche_sizer)
            for name in config.sections_names:
                self.creche_ctrl.Append(name)
            if config.default_section:
                self.creche_ctrl.SetStringSelection(config.default_section.name)
            else:
                self.creche_ctrl.SetSelection(0)
            self.sizer.Show(self.btnsizer)
            self.ok_button.SetFocus()
            self.sizer.Layout()
            self.sizer.Fit(self)
            return

        if config.connection.is_token_already_used():
            dlg = wx.MessageDialog(self,
                                   "Le jeton n'a pas pu être pris. Gertrude sera accessible en lecture seule. Voulez-vous forcer la prise du jeton ?",
                                   "Gertrude",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_YES or not config.connection.get_token(force=True):
                config.readonly = True

        self.loaded = True
        database.load()
        if (config.options & NO_PASSWORD) or len(database.creche.users) == 0:
            config.profil = PROFIL_ALL | PROFIL_ADMIN
            self.StartFrame()
        else:
            self.sizer.Hide(self.gauge)
            self.info.AppendText("Identification ...\n")
            self.sizer.Show(self.fields_sizer)
            self.sizer.Show(self.btnsizer)
            self.login_ctrl.SetFocus()
            self.sizer.Layout()
            self.sizer.Fit(self)
    
    def AppendMessage(self, message):
        wx.PostEvent(self, self.MessageEvent(message=message, gauge=None))
        wx.Yield()
        
    def SetGauge(self, gauge):
        wx.PostEvent(self, self.MessageEvent(message=None, gauge=gauge))
        wx.Yield()

    def OnMessage(self, event):
        if event.message is not None:
            self.info.AppendText(event.message)
        if event.gauge is not None:
            self.gauge.SetValue(event.gauge)
                
    def Load(self, section=None):
        if sys.platform != "darwin":
            time.sleep(0.5)
        try:
            if section is None:
                config.load(progress_handler=ProgressHandler(self.AppendMessage, self.SetGauge, 0, 5))
                if config.current_section is None:
                    wx.CallAfter(self.OnLoaded, None)
                    return
            config.readonly = bool(config.options & READONLY)
            config.connection = get_connection_from_config()
            result = config.connection.Load(ProgressHandler(self.AppendMessage, self.SetGauge, 5, 10))
            database.init(config.database)
        except requests.ConnectionError:
            traceback.print_exc()
            self.info.AppendText("Erreur de connection avec le serveur\n")
            result = False
        except Exception as e:
            print("Exception", e)
            traceback.print_exc()
            self.info.AppendText(str(e) + "\n")
            result = False
        wx.CallAfter(self.OnLoaded, result)

    def StartFrame(self):
        frame = GertrudeFrame(ProgressHandler(self.info.AppendText, self.SetGauge, 50, 100))
        frame.Show()
        self.SetGauge(100)
        self.Destroy()
        if sys.platform == "darwin":
            frame.Show()

    def OnOk(self, _):
        if config.current_section is None:
            self.sizer.Hide(self.creche_sizer)
            self.sizer.Hide(self.btnsizer)
            self.sizer.Show(self.gauge)
            self.sizer.Layout()
            self.sizer.Fit(self)
            section = self.creche_ctrl.GetStringSelection()
            self.info.AppendText("Structure %s sélectionnée.\n" % section)
            config.set_current_section(section)
            wx.CallAfter(self.Load, section)
            return
            
        login = self.login_ctrl.GetValue()
        password = self.passwd_ctrl.GetValue().encode("utf-8")

        for user in database.creche.users:
            hashed = user.password.encode("utf-8")
            if login == user.login and bcrypt.checkpw(password, hashed):
                config.profil = user.profile
                if user.profile & PROFIL_LECTURE_SEULE:
                    if config.server:
                        config.server.close()
                    config.readonly = True
                self.StartFrame()
                return
        else:
            self.login_ctrl.Clear()
            self.passwd_ctrl.Clear()
            self.login_ctrl.SetFocus()

    def OnExit(self, _):
        self.info.AppendText("\nFermeture ...\n")
        if self.loaded:
            config.connection.Exit(ProgressHandler(self.info.AppendText, self.SetGauge, 5, 100))
        self.Destroy()
