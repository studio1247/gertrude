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

class RelevesPanel(GPanel):
    bitmap = './bitmaps/releves.png'
    index = 40
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Relevés')

        today = datetime.date.today()
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Les coordonnees des parents
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Coordonnées des parents'), wx.HORIZONTAL)
        self.coords_date = wx.TextCtrl(self)
        self.coords_date.SetValue("Aujourd'hui")
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationCoordonnees, button)
        box_sizer.AddMany([(self.coords_date, 1, wx.EXPAND|wx.ALL, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        # Les releves trimestriels
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Relevés trimestriels'), wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        button = wx.Button(self, -1, u'Génération')
        for year in range(first_date.year, last_date.year + 1):
            self.choice.Append(u'Année %d' % year, year)
        self.choice.SetSelection(today.year - first_date.year)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationEtatsTrimestriels, button)
        box_sizer.AddMany([(self.choice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

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
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

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
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        self.sizer.Add(sizer, 1, wx.EXPAND)

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
        
panels = [RelevesPanel]