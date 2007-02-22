# -*- coding: cp1252 -*-

import os.path
import datetime
from common import *
from planning import GPanel
from Controls import *

profiles = [("Administrateur", PROFIL_ALL),
            ("Bureau", PROFIL_BUREAU),
            (u"Trésorier", PROFIL_TRESORIER),
            ("Inscriptions", PROFIL_INSCRIPTIONS),
            (u"Saisie présences", PROFIL_SAISIE_PRESENCES),
            ]
            
class UsersPanel(AutoTab):
    def __init__(self, parent, creche):
        AutoTab.__init__(self, parent)
        self.creche = creche
        sizer = wx.BoxSizer(wx.VERTICAL)
        button_add = wx.Button(self, -1, 'Nouvel utilisateur')
        sizer.Add(button_add, 0, wx.EXPAND)
        self.Bind(wx.EVT_BUTTON, self.user_add, button_add)
        self.sizer = wx.FlexGridSizer(4, 6, 5, 5)
        for i, user in enumerate(self.creche.users):
            self.display_user(i)
        sizer.Add(self.sizer)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def display_user(self, index):
        self.sizer.AddMany([wx.StaticText(self, -1, 'Login :'), AutoTextCtrl(self, self.creche, 'users[%d].login' % index)])
        self.sizer.AddMany([wx.StaticText(self, -1, 'Mot de passe :'), AutoTextCtrl(self, self.creche, 'users[%d].password' % index)])
        self.sizer.AddMany([wx.StaticText(self, -1, 'Profil :'), AutoChoiceCtrl(self, self.creche, 'users[%d].profile' % index, items=profiles)])

    def user_add(self, event):
        self.creche.users.append(User())
        self.display_user(len(self.creche.users) - 1)
        self.sizer.Layout()
        
class AdminNotebook(wx.Notebook):
    def __init__(self, parent, creche):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(UsersPanel(self, creche), u'Utilisateurs')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
     
class AdminPanel(GPanel):
    def __init__(self, parent, creche):
        GPanel.__init__(self, parent, 'Administration')
        self.notebook = AdminNotebook(self, creche)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()
