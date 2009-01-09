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
            self.Disable(u"Crèche fermée")
        else:
            lines = []
            for inscrit in creche.inscrits:
                if inscrit.getInscription(self.date) is not None:
                    # print inscrit.prenom, 
                    if self.date in inscrit.journees:
                        line = inscrit.journees[self.date]
                        line.insert = None
                    else:
                        line = inscrit.getJourneeFromSemaineType(self.date)
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
    index = 20
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Présences enfants')

        # La combobox pour la selection de la semaine
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.week_choice = wx.Choice(self, -1)
        sizer.Add(self.week_choice, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        day = first_monday = getFirstMonday()
        semaine = getNumeroSemaine(day)
        while day < last_date:
            string = 'Semaine %d (%d %s %d)' % (semaine, day.day, months[day.month - 1], day.year)
            self.week_choice.Append(string, day)
            if day.year == (day + datetime.timedelta(7)).year:
                semaine += 1
            else:
                semaine = 1
            day += datetime.timedelta(7)
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        self.week_choice.SetSelection(semaine)
        self.Bind(wx.EVT_CHOICE, self.OnChangeWeek, self.week_choice)
        
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
            title = days[week_day] + " " + str(date.day) + " " + months[date.month - 1] + " " + str(date.year)
            planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
            planning_panel.SetDate(date)
            self.notebook.AddPage(planning_panel, title)

        self.sizer.Layout()

    def OnChangeWeek(self, evt):
        cb = evt.GetEventObject()
        monday = cb.GetClientData(cb.GetSelection())
        for week_day in range(self.count):
            day = monday + datetime.timedelta(week_day)
            note = self.notebook.GetPage(week_day)
            self.notebook.SetPageText(week_day, days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year))
            note = self.notebook.GetPage(week_day)
            note.SetDate(day)
            self.notebook.SetSelection(0)
        self.sizer.Layout()

    def UpdateContents(self):
        self.activity_choice.Clear()
        tmp = Activite(creation=False)
        tmp.value = 0
        self.activity_choice.Append(u'Présences', tmp)
        selected = 0
        if len(creche.activites) > 0:
            self.activity_choice.Enable()
            for i, activity in enumerate(creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                try:
                    if self.activity_choice.activity.value == activity.value:
                        selected = i+1
                except:
                    pass
        else:
            self.activity_choice.Disable()
        self.activity_choice.SetSelection(selected)
        for week_day in range(self.count):
            note = self.notebook.GetPage(week_day)
            note.UpdateContents()
        self.sizer.Layout()

panels = [PlanningPanel]
