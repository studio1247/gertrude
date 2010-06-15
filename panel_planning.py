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

import datetime
from constants import *
from parameters import *
from functions import *
from sqlobjects import *
from controls import *
from planning import PlanningWidget

class DayPlanningPanel(PlanningWidget):
    def UpdateContents(self):
        if self.date in creche.jours_fermeture:
            conge = creche.jours_fermeture[self.date]
            if conge.options == ACCUEIL_NON_FACTURE:
                self.SetInfo(conge.label)
            else:
                if conge.label:
                    self.Disable(conge.label)
                else:
                    self.Disable(u"Crèche fermée")
                return
        
        lines = []
        for inscrit in creche.inscrits:
            if inscrit.getInscription(self.date) is not None:
                # print inscrit.prenom, 
                if self.date in inscrit.journees:
                    line = inscrit.journees[self.date]
                    line.insert = None
                else:
                    line = inscrit.getReferenceDayCopy(self.date)
                    line.insert = inscrit.journees
                    line.key = self.date
                line.label = GetInscritId(inscrit, creche.inscrits)
                line.reference = inscrit.getReferenceDay(self.date)
                lines.append(line)
        self.SetLines(lines)

    def SetDate(self, date):
        self.date = date
        self.UpdateContents()

class PlanningPanel(GPanel):
    bitmap = './bitmaps/presences.png'
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Plannings')
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Les raccourcis pour semaine précédente / suivante
        self.previous_button = wx.Button(self, -1, '<', size=(20,0), style=wx.NO_BORDER)
        self.next_button = wx.Button(self, -1, '>', size=(20,0), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.onPreviousWeek, self.previous_button)
        self.Bind(wx.EVT_BUTTON, self.onNextWeek, self.next_button)
        sizer.Add(self.previous_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        sizer.Add(self.next_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        
        # La combobox pour la selection de la semaine
        self.week_choice = wx.Choice(self, -1)
        sizer.Add(self.week_choice, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        day = first_monday = getFirstMonday()
        while day < last_date:
            string = 'Semaine %d (%d %s %d)' % (day.isocalendar()[1], day.day, months[day.month - 1], day.year)
            self.week_choice.Append(string, day)
            day += datetime.timedelta(7)
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        self.week_choice.SetSelection(semaine)
        self.Bind(wx.EVT_CHOICE, self.onChangeWeek, self.week_choice)
        
        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self)
        sizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(sizer, 0, wx.EXPAND)
        
        # le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        if "Week-end" in creche.feries:
            self.count = 5
        else:
            self.count = 7
        for week_day in range(self.count):
            date = first_monday + datetime.timedelta(semaine * 7 + week_day)
            planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
            planning_panel.SetDate(date)
            self.notebook.AddPage(planning_panel, getDateStr(date))

        self.sizer.Layout()

    def onChangeWeek(self, evt=None):
        selection = self.week_choice.GetSelection()
        self.previous_button.Enable(selection is not 0)
        self.next_button.Enable(selection is not self.week_choice.GetCount() - 1)
        monday = self.week_choice.GetClientData(selection)
        for week_day in range(self.count):
            day = monday + datetime.timedelta(week_day)
            note = self.notebook.GetPage(week_day)
            self.notebook.SetPageText(week_day, getDateStr(day))
            note = self.notebook.GetPage(week_day)
            note.SetDate(day)
            self.notebook.SetSelection(0)
        self.sizer.Layout()
        
    def onPreviousWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.onChangeWeek()
    
    def onNextWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.onChangeWeek()

    def UpdateContents(self):
        self.activity_choice.Clear()
        selected = 0
        if len(creche.activites) > 1:
            self.activity_choice.Enable()
            for i, activity in enumerate(creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                try:
                    if self.activity_choice.activity.value == activity.value:
                        selected = i
                except:
                    pass
        else:
            self.activity_choice.Disable()
            self.activity_choice.Append(creche.activites[0].label, creche.activites[0])
        self.activity_choice.SetSelection(selected)
        for week_day in range(self.count):
            note = self.notebook.GetPage(week_day)
            note.UpdateContents()
        self.sizer.Layout()

