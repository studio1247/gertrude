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
import os.path
import sys
import string
import datetime
import wx
import wx.lib.scrolledpanel
import wx.html
from constants import *
from controls import *
from ooffice import *
from planning_presences import PlanningModifications
from coordonnees_parents import CoordonneesModifications
from etats_trimestriels import EtatsTrimestrielsModifications
from planning_detaille import PlanningDetailleModifications
from facture import FactureFinMois

class RelevesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        today = datetime.date.today()
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Les coordonnees des parents
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Coordonnées des parents'), wx.HORIZONTAL)
        self.coords_date = wx.TextCtrl(self)
        self.coords_date.SetValue("Aujourd'hui")
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationCoordonnees, button)
        box_sizer.AddMany([(self.coords_date, 1, wx.EXPAND|wx.ALL, 5), (button, 0, wx.ALL, 5)])
        self.sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        # Les releves trimestriels
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Relevés trimestriels'), wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        button = wx.Button(self, -1, u'Génération')
        for year in range(first_date.year, last_date.year + 1):
            self.choice.Append(u'Année %d' % year, year)
        self.choice.SetSelection(today.year - first_date.year)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationEtatsTrimestriels, button)
        box_sizer.AddMany([(self.choice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        self.sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les plannings de presence enfants
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Planning des présences'), wx.HORIZONTAL)
        self.weekchoice = wx.Choice(self)
        day = getFirstMonday()
        semaine = 1
        while day < last_date:
            string = 'Semaines %d et %d (%d %s %d)' % (semaine, semaine+1, day.day, months[day.month - 1], day.year)
            self.weekchoice.Append(string, day)
            if (day.year == (day + datetime.timedelta(14)).year):
                semaine += 2
            else:
                semaine = 1
            day += datetime.timedelta(14)
        self.weekchoice.SetSelection((today - getFirstMonday()).days / 14 + 1)
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningPresences, button)
        box_sizer.AddMany([(self.weekchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        self.sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les plannings détaillés
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Planning détaillé'), wx.HORIZONTAL)
        self.detail_start_date = DateCtrl(self)
        self.detail_end_date = DateCtrl(self)
        day = today
        while day in creche.jours_fermeture:
            day += datetime.timedelta(1)
        self.detail_start_date.SetValue(day)
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningDetaille, button)
        box_sizer.AddMany([(self.detail_start_date, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5), (wx.StaticText(self, -1, "-"), 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5), (self.detail_end_date, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5), (button, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5)])
        self.sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        self.SetSizer(self.sizer)

    def EvtGenerationCoordonnees(self, evt):
        date = str2date(self.coords_date.GetValue())
        DocumentDialog(self, CoordonneesModifications(date)).ShowModal()

    def EvtGenerationEtatsTrimestriels(self, evt):
        annee = self.choice.GetClientData(self.choice.GetSelection())
        DocumentDialog(self, EtatsTrimestrielsModifications(annee)).ShowModal()

    def EvtGenerationPlanningPresences(self, evt):
        date = self.weekchoice.GetClientData(self.weekchoice.GetSelection())
        DocumentDialog(self, PlanningModifications(date)).ShowModal()
            
    def EvtGenerationPlanningDetaille(self, evt):
        start = self.detail_start_date.GetValue()
        end = self.detail_end_date.GetValue()
        if end is None:
            end = start
        DocumentDialog(self, PlanningDetailleModifications((start, end))).ShowModal()

class EtatsPresenceTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.anneechoice = wx.Choice(self)
        for annee in range(first_date.year, last_date.year+1):
            self.anneechoice.Append(str(annee), annee)
        self.anneechoice.SetStringSelection(str(today.year))
        self.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.anneechoice)
        self.periodechoice = wx.Choice(self)
        for index, month in enumerate(months):
            self.periodechoice.Append(month, [index])
        self.periodechoice.Append("----") # TODO changer ça 
        for index, trimestre in enumerate(trimestres):
            self.periodechoice.Append("%s trimestre" % trimestre, [3*index, 3*index+1, 3*index+2])
        self.periodechoice.SetStringSelection(months[today.month-1])
        self.periodechoice.Append("----") # TODO changer ça 
        self.periodechoice.Append(u"Année complète", range(0, 12))
        self.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        sizer.AddMany([(self.anneechoice, 0, 0), (self.periodechoice, 0, wx.LEFT, 5)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 10)
        
        sizer = wx.FlexGridSizer(0, 3, 5, 10)
        self.presences_contrat_heures = wx.TextCtrl(self)
        self.presences_contrat_heures.Disable()
        self.presences_contrat_euros = wx.TextCtrl(self)
        self.presences_contrat_euros.Disable()
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences contractualisées :'), 0, 0), (self.presences_contrat_heures, 0, wx.EXPAND), (self.presences_contrat_euros, 0, wx.EXPAND)])
        self.presences_realisees_heures = wx.TextCtrl(self)
        self.presences_realisees_heures.Disable()
        self.presences_realisees_euros = wx.TextCtrl(self)
        self.presences_realisees_euros.Disable()
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences réalisées :'), 0, 0), (self.presences_realisees_heures, 0, wx.EXPAND), (self.presences_realisees_euros, 0, wx.EXPAND)])
        self.presences_facturees_heures = wx.TextCtrl(self)
        self.presences_facturees_heures.Disable()
        self.presences_facturees_euros = wx.TextCtrl(self)
        self.presences_facturees_euros.Disable()
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences facturées :'), 0, 0), (self.presences_facturees_heures, 0, wx.EXPAND), (self.presences_facturees_euros, 0, wx.EXPAND)])       
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 10)
        
        self.SetSizer(self.sizer)
        
    def EvtPeriodeChoice(self, evt):
        annee = self.anneechoice.GetClientData(self.anneechoice.GetSelection())
        periode = self.periodechoice.GetClientData(self.periodechoice.GetSelection())
        heures_contractualisees = 0.0
        heures_realisees = 0.0
        heures_facturees = 0.0
        for mois in periode:
            debut = datetime.date(annee, mois+1, 1)
            fin = getMonthEnd(debut)
            for inscrit in creche.inscrits:
                if inscrit.getInscriptions(debut, fin):
                    facture = FactureFinMois(inscrit, annee, mois+1)
                    heures_contractualisees += facture.heures_contractualisees
                    heures_realisees += facture.heures_realisees
                    # print inscrit.prenom, facture.heures_contrat, facture.heures_realisees
                    heures_facturees += sum(facture.heures_facturees)
                    
        self.presences_contrat_heures.SetValue("%.2f heures" % heures_contractualisees)
        self.presences_realisees_heures.SetValue("%.2f heures" % heures_realisees)
        self.presences_facturees_heures.SetValue("%.2f heures" % heures_facturees)
        
        
class RelevesNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(EtatsPresenceTab(self), u'Statistiques de fréquentation')
        self.AddPage(RelevesTab(self), u'Edition de relevés')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
        
class RelevesPanel(GPanel):
    bitmap = './bitmaps/releves.png'
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Tableaux de bord')
        self.notebook = RelevesNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()