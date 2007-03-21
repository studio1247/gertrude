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

import os.path
import datetime
from common import *
from planning import GPanel
from controls import *

profiles = [("Administrateur", PROFIL_ALL),
            ("Bureau", PROFIL_BUREAU),
            (u"Trésorier", PROFIL_TRESORIER),
            ("Inscriptions", PROFIL_INSCRIPTIONS),
            (u"Saisie présences", PROFIL_SAISIE_PRESENCES),
            ]

class UsersPanel(AutoTab):
    def __init__(self, parent, creche):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.creche = creche
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.users_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, user in enumerate(self.creche.users):
            self.display_user(i)
        self.sizer.Add(self.users_sizer)
        button_add = wx.Button(self, -1, 'Nouvel utilisateur')
        self.sizer.Add(button_add, 0, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.user_add, button_add)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

    def display_user(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Login :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.creche, 'users[%d].login' % index)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Mot de passe :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.creche, 'users[%d].password' % index)])
        profile_choice = AutoChoiceCtrl(self, self.creche, 'users[%d].profile' % index, items=profiles)
        profile_choice.index = index
        self.Bind(wx.EVT_CHOICE, self.user_modify_profile, profile_choice)
        sizer.AddMany([(wx.StaticText(self, -1, 'Profil :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), profile_choice])
        delbutton = wx.BitmapButton(self, -1, delbmp, size=(delbmp.GetWidth(), delbmp.GetHeight()))
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.user_del, delbutton)
        self.users_sizer.Add(sizer)

    def user_add(self, event):
        self.creche.users.append(User())
        self.display_user(len(self.creche.users) - 1)
        self.sizer.Layout()

    def user_del(self, event):
        index = event.GetEventObject().index
        nb_admins = len([user for i, user in enumerate(self.creche.users) if (i != index and user.profile == PROFIL_ALL)])
        if len(self.creche.users) == 1 or nb_admins > 0:
            sizer = self.users_sizer.GetItem(len(self.creche.users)-1)
            sizer.DeleteWindows()
            self.users_sizer.Detach(len(self.creche.users)-1)
            self.creche.users[index].delete()
            del self.creche.users[index]
            self.sizer.Layout()
            self.UpdateContents()
        else:
            dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", 'Message', wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def user_modify_profile(self, event):
        obj = event.GetEventObject()
        index = obj.index
        if self.creche.users[index].profile == PROFIL_ALL and event.GetClientData() != PROFIL_ALL:
            nb_admins = len([user for i, user in enumerate(self.creche.users) if (i != index and user.profile == PROFIL_ALL)])
            if nb_admins == 0:
                dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", "Message", wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                event.Skip(False)
                obj.SetSelection(0) # PROFIL_ALL
            else:
                event.Skip(True)
        else:
            event.Skip(True)

class ConnectionPanel(AutoTab):
    def __init__(self, parent, creche):
        AutoTab.__init__(self, parent)
        self.creche = creche
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Serveur HTTP :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.creche, 'server_url', size=(200, 21))])
        self.sizer.Add(sizer)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

class CongesPanel(AutoTab):
    def __init__(self, parent, creche):
        AutoTab.__init__(self, parent)
        self.creche = creche
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        for text in [j[0] for j in jours_feries]:
            textctrl = wx.TextCtrl(self, -1, text, style=wx.TE_READONLY)
            textctrl.Disable()
            self.sizer.Add(textctrl, 0, wx.EXPAND)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(self.creche.conges):
            self.display_conge(i)
        self.sizer.Add(self.conges_sizer)
        button_add = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(button_add, 0, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.conges_add, button_add)
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

    def display_conge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.creche, 'conges[%d].debut' % index)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.creche, 'conges[%d].fin' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp, size=(delbmp.GetWidth(), delbmp.GetHeight()))
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.conges_del, delbutton)
        self.conges_sizer.Add(sizer)
        
    def conges_add(self, event):
        self.creche.add_conge(Conge())
        self.display_conge(len(self.creche.conges) - 1)
        self.sizer.Layout()

    def conges_del(self, event):
        index = event.GetEventObject().index
        sizer = self.conges_sizer.GetItem(len(self.creche.conges)-1)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(len(self.creche.conges)-1)
        self.creche.conges[index].delete()
        del self.creche.conges[index]
        self.sizer.Layout()
        self.UpdateContents()

class AdminNotebook(wx.Notebook):
    def __init__(self, parent, creche):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(UsersPanel(self, creche), 'Utilisateurs')
        self.AddPage(ConnectionPanel(self, creche), 'Connection')
        self.AddPage(CongesPanel(self, creche), u'Congés')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
     
class AdminPanel(GPanel):
    def __init__(self, parent):
        GPanel.__init__(self, parent, 'Administration')
        self.notebook = AdminNotebook(self, creche)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()
