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

import os.path
import datetime
from constants import *
from parameters import *
from sqlobjects import *
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
            self.line_add(i)
        self.sizer.Add(self.users_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, 'Nouvel utilisateur')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.user_add, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.users_sizer.GetChildren()), len(creche.users)):
            self.line_add(i)
        for i in range(len(creche.users), len(self.users_sizer.GetChildren())):
            self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def line_add(self, index):
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

    def line_del(self):
        index = len(self.users_sizer.GetChildren()) - 1
        sizer = self.users_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.users_sizer.Detach(index)

    def user_add(self, event):
        history.Append(Delete(creche.users, -1))
        creche.users.append(User())
        self.line_add(len(creche.users) - 1)
        self.sizer.Layout()

    def user_del(self, event):
        index = event.GetEventObject().index
        nb_admins = len([user for i, user in enumerate(creche.users) if (i != index and user.profile == PROFIL_ALL)])
        if len(creche.users) == 1 or nb_admins > 0:
            history.Append(Insert(creche.users, index, creche.users[index]))
            self.line_del()
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

class JoursFermeturePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            if text in creche.feries:
                checkbox.SetValue(True)
            self.sizer.Add(checkbox, 0, wx.EXPAND)
            self.Bind(wx.EVT_CHECKBOX, self.feries_check, checkbox)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(creche.conges):
            self.line_add(i)
        self.sizer.Add(self.conges_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(button_add, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.conges_add, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        for i in range(len(self.conges_sizer.GetChildren()), len(creche.conges)):
            self.line_add(i)
        for i in range(len(creche.conges), len(self.conges_sizer.GetChildren())):
            self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].debut' % index)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].fin' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.conges_del, delbutton)
        self.conges_sizer.Add(sizer)

    def line_del(self):
        index = len(self.conges_sizer.GetChildren()) - 1
        sizer = self.conges_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(index)

    def conges_add(self, event):
        history.Append(Delete(creche.conges, -1))
        creche.add_conge(Conge())
        self.line_add(len(creche.conges) - 1)
        self.sizer.Layout()

    def conges_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(creche.conges, index, creche.conges[index]))
        self.line_del()
        creche.conges[index].delete()
        del creche.conges[index]
        self.sizer.Layout()
        self.UpdateContents()

    def feries_check(self, event):
        label = event.GetEventObject().GetLabelText()
        if event.IsChecked():
            conge = Conge(creation=False)
            conge.debut = label
            conge.create()
            creche.add_conge(conge)
        else:
            conge = creche.feries[label]
            conge.delete()
            del creche.feries[label]
            creche.calcule_jours_fermeture()
        history.Append(None)

class ParametersPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.FlexGridSizer(0, 2, 5, 5)
        sizer.AddGrowableCol(1, 1)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(AutoChoiceCtrl(self, creche, 'ouverture', [('7h30', 7.5), ('7h45', 7.75), ('8h', 8), ('8h30', 8.5), ('9h', 9)]), 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'fermeture', [('18h', 18), ('18h30', 18.5), ('18h45', 18.75), ('19h', 19)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures d\'ouverture :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(AutoChoiceCtrl(self, creche, 'affichage_min', [('7h30', 7.5), ('7h45', 7.75), ('8h', 8), ('8h30', 8.5), ('9h', 9)]), 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'affichage_max', [('18h', 18), ('18h30', 18.5), ('18h45', 18.75), ('19h', 19)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures affichées sur le planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Granularité du planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'granularite', [('1/4 heure', 4), ('1/2 heure', 2), ('1 heure', 1)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nombre de mois payés :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'mois_payes', [('12 mois', 12), ('11 mois', 11)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences prévisionnelles :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'presences_previsionnelles', [(u'Géré', True), (u'Non géré', False)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Modes d'inscription :"), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'modes_inscription', [(u'Crèche à plein-temps uniquement', MODE_5_5), ('Tous modes', MODE_5_5+MODE_4_5+MODE_3_5+MODE_HALTE_GARDERIE)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Minimum de jours de maladie pour déduction :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'minimum_maladie', min=0, precision=0), 0, wx.EXPAND)])
        facturation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        facturation_sizer.Add(AutoCheckBox(self, creche, 'mode_facturation', u'PSU', FACTURATION_PSU), 0, wx.EXPAND|wx.RIGHT, 5)
        facturation_sizer.Add(AutoCheckBox(self, creche, 'mode_facturation', u'Déduction de jours pour maladie avec carence', DEDUCTION_MALADIE_AVEC_CARENCE), 0, wx.EXPAND)
        sizer.AddMany([(wx.StaticText(self, -1, u'Mode de facturation :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (facturation_sizer, 0, wx.EXPAND)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)

class AdminNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(UsersPanel(self), 'Utilisateurs')
        self.AddPage(JoursFermeturePanel(self), u'Congés')
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
    bitmap = './bitmaps/administration.png'
    index = 60
    profil = PROFIL_ADMIN
    def __init__(self, parent):
        GPanel.__init__(self, parent, 'Administration')
        self.notebook = AdminNotebook(self)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()

panels = [AdminPanel]
