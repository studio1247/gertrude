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

class CrechePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, u'Nom de la crèche :'), AutoTextCtrl(self, creche, 'nom', size=(200, 21))])
        sizer2.AddMany([wx.StaticText(self, -1, 'Adresse :'), AutoTextCtrl(self, creche, 'adresse', size=(200, 21))])
        sizer2.AddMany([wx.StaticText(self, -1, 'Code Postal :'), AutoNumericCtrl(self, creche, 'code_postal', precision=0, size=(200, 21))])
        sizer2.AddMany([wx.StaticText(self, -1, 'Ville :'), AutoTextCtrl(self, creche, 'ville', size=(200, 21))])       
        sizer.Add(sizer2)
        sizer.Fit(self)
        self.SetSizer(sizer)
        
class ResponsabilitesPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        parents = self.GetNomsParents()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, creche, 'bureaux', Bureau))
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        self.responsables_ctrls = []
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].president', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Président :'), self.responsables_ctrls[-1]])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].vice_president', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Vice président :'), self.responsables_ctrls[-1]])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].tresorier', items=parents))
        sizer2.AddMany([wx.StaticText(self, -1, u'Trésorier :'), self.responsables_ctrls[-1]])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, creche, 'bureaux[self.parent.periode].secretaire', items=parents))        
        sizer2.AddMany([wx.StaticText(self, -1, u'Secrétaire :'), self.responsables_ctrls[-1]])
        sizer.Add(sizer2)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def UpdateContents(self):
        parents = self.GetNomsParents()
        for ctrl in self.responsables_ctrls:
            ctrl.SetItems(parents)
        AutoTab.UpdateContents(self)

    def GetNomsParents(self):
        result = []
        parents = []
        for inscrit in creche.inscrits:
            for parent in (inscrit.papa, inscrit.maman):
                if parent.prenom and parent.nom:
                    tmp = parent.prenom + ' ' + parent.nom
                    if not tmp in parents:
                        parents.append(tmp)
                        result.append((tmp, parent))
        result.sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
        return result

class CafPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, creche, 'baremes_caf', BaremeCAF))
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, 'Plancher :'), AutoNumericCtrl(self, creche, 'baremes_caf[self.parent.periode].plancher', precision=2)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Plafond :'), AutoNumericCtrl(self, creche, 'baremes_caf[self.parent.periode].plafond', precision=2)])
        sizer.Add(sizer2)
        sizer.Fit(self)
        self.SetSizer(sizer)
        
class GeneralNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(CrechePanel(self), u'Crèche')
        self.AddPage(ResponsabilitesPanel(self), u'Responsabilités')
        self.AddPage(CafPanel(self), 'C.A.F.')        
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
     
class GeneralPanel(GPanel):
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Crèche')
        self.notebook = GeneralNotebook(self)
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
            
    def UpdateContents(self):
        self.notebook.UpdateContents()
