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
from gpanel import GPanel
from controls import *

profiles = [("Administrateur", PROFIL_ALL),
            ("Bureau", PROFIL_BUREAU),
            (u"Trésorier", PROFIL_TRESORIER),
            ("Inscriptions", PROFIL_INSCRIPTIONS),
            (u"Saisie présences", PROFIL_SAISIE_PRESENCES),
            ]

class UsersPanel(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.users_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, user in enumerate(creche.users):
            self.display_user(i)
        self.sizer.Add(self.users_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, 'Nouvel utilisateur')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.user_add, button_add)
        self.SetSizer(self.sizer)

    def display_user(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Login :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'users[%d].login' % index), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Mot de passe :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'users[%d].password' % index), 0, wx.ALIGN_CENTER_VERTICAL)])
        profile_choice = AutoChoiceCtrl(self, creche, 'users[%d].profile' % index, items=profiles)
        profile_choice.index = index
        self.Bind(wx.EVT_CHOICE, self.user_modify_profile, profile_choice)
        sizer.AddMany([(wx.StaticText(self, -1, 'Profil :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), profile_choice])
        delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.NO_BORDER)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.user_del, delbutton)
        self.users_sizer.Add(sizer)

    def user_add(self, event):
        creche.users.append(User())
        self.display_user(len(creche.users) - 1)
        self.sizer.Layout()

    def user_del(self, event):
        index = event.GetEventObject().index
        nb_admins = len([user for i, user in enumerate(creche.users) if (i != index and user.profile == PROFIL_ALL)])
        if len(creche.users) == 1 or nb_admins > 0:
            sizer = self.users_sizer.GetItem(len(creche.users)-1)
            sizer.DeleteWindows()
            self.users_sizer.Detach(len(creche.users)-1)
            creche.users[index].delete()
            del creche.users[index]
            self.sizer.Layout()
            self.UpdateContents()
        else:
            dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", 'Message', wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def user_modify_profile(self, event):
        obj = event.GetEventObject()
        index = obj.index
        if creche.users[index].profile == PROFIL_ALL and event.GetClientData() != PROFIL_ALL:
            nb_admins = len([user for i, user in enumerate(creche.users) if (i != index and user.profile == PROFIL_ALL)])
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

class CongesPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)       
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        for text in [j[0] for j in jours_feries]:
            textctrl = wx.TextCtrl(self, -1, text, style=wx.TE_READONLY)
            textctrl.Disable()
            self.sizer.Add(textctrl, 0, wx.EXPAND)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(creche.conges):
            self.display_conge(i)
        self.sizer.Add(self.conges_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(button_add, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.conges_add, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(sizer)

    def display_conge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].debut' % index)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].fin' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.conges_del, delbutton)
        self.conges_sizer.Add(sizer)
        
    def conges_add(self, event):
        creche.add_conge(Conge())
        self.display_conge(len(creche.conges) - 1)
        self.sizer.Layout()

    def conges_del(self, event):
        index = event.GetEventObject().index
        sizer = self.conges_sizer.GetItem(len(creche.conges)-1)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(len(creche.conges)-1)
        creche.conges[index].delete()
        del creche.conges[index]
        self.sizer.Layout()
        self.UpdateContents()

class ParametersPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.FlexGridSizer(0, 2, 5, 5)
        sizer.AddGrowableCol(1, 1)
        sizer.AddMany([(wx.StaticText(self, -1, 'Serveur HTTP :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'server_url'), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nombre de mois payés :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'mois_payes', [('12 mois', 12), ('11 mois', 11)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences prévisionnelles :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'presences_previsionnelles', [(u'Géré', True), (u'Non géré', False)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Modes d'inscription :"), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'modes_inscription', [(u'Crèche à plein-temps uniquement', 0), (u'Crèche (5/5 4/5 3/5) et halte-garderie', MODE_HALTE_GARDERIE+MODE_4_5+MODE_3_5)]), 0, wx.EXPAND)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)
        
class AdminNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(UsersPanel(self), 'Utilisateurs')
        self.AddPage(CongesPanel(self), u'Congés')
        self.AddPage(ParametersPanel(self), u'Paramètres')
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
        self.notebook = AdminNotebook(self)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()
