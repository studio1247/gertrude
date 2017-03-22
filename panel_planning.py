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

import datetime
from globals import *
from constants import *
from parameters import *
from functions import *
from sqlobjects import *
from controls import *
from planning import PlanningWidget, GetPlanningLinesChildren, GetPlanningLinesSalaries
from ooffice import *
from doc_planning_detaille import PlanningDetailleModifications
import tablette


class DayPlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_combobox):
        PlanningWidget.__init__(self, parent, activity_combobox, COMMENTS | ACTIVITES | TWO_PARTS | DEPASSEMENT_CAPACITE, self.CheckLine)

    def CheckLine(self, line, plages_selectionnees):
        lines = self.GetSummaryLines()
        activites, activites_sans_horaires = GetActivitiesSummary(creche, lines)
        for start, end in plages_selectionnees:
            for i in range(start, end):
                if activites[0][i][0] > creche.GetCapacite(line.day):
                    dlg = wx.MessageDialog(None, u"Dépassement de la capacité sur ce créneau horaire !", u"Attention", wx.OK|wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()
                    self.state = None
                    return

    def UpdateContents(self):
        if self.date in creche.jours_fermeture:
            conge = creche.jours_fermeture[self.date]
            if conge.options == ACCUEIL_NON_FACTURE:
                self.SetInfo(conge.label)
            else:
                if conge.label:
                    self.Disable(conge.label)
                else:
                    self.Disable(u"Etablissement fermé")
                return
        else:
            self.SetInfo("")

        self.lignes_enfants = GetPlanningLinesChildren(self.date, self.site, self.groupe)
        if creche.groupes and (creche.tri_planning & TRI_GROUPE):
            groupe = 0
            lines = []
            for line in self.lignes_enfants:
                if groupe != line.inscription.groupe:
                    groupe = line.inscription.groupe
                    lines.append(groupe.nom if groupe else "")
                lines.append(line)
        else:
            lines = self.lignes_enfants[:]

        self.lignes_salaries = GetPlanningLinesSalaries(self.date, self.site)
        if self.lignes_salaries:
            lines.append(u"Salariés")
            lines += self.lignes_salaries
        self.SetLines(lines)

    def GetSummaryDynamicText(self):
        heures = 0.0
        for line in self.lignes_enfants:
            heures += line.GetNombreHeures()
            day = line.day

        if heures > 0:
            text = GetHeureString(heures)
            if self.site:
                den = self.site.capacite * creche.GetAmplitudeHoraire()
            else:
                den = creche.GetHeuresAccueil(day)
            if den > 0:
                text += " /  %.1f%%" % (heures * 100 / den)
            return text
        else:
            return None

    def SetData(self, site, groupe, date):
        self.site = site
        self.groupe = groupe
        self.date = date
        self.UpdateContents()


class PlanningBasePanel(GPanel):
    name = "Planning"
    bitmap = GetBitmapFile("planning.png")
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Planning')
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_site = 0

        # La combobox pour la selection du site
        self.site_choice = wx.Choice(self, -1)
        for site in creche.sites:
            self.site_choice.Append(site.nom, site)
        self.topsizer.Add(self.site_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.RIGHT, 5)
        if len(creche.sites) < 2:
            self.site_choice.Show(False)
        self.site_choice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChangementSemaine, self.site_choice)

        # Les raccourcis pour semaine précédente / suivante
        self.previous_button = wx.Button(self, -1, '<', size=(20,0), style=wx.NO_BORDER)
        self.next_button = wx.Button(self, -1, '>', size=(20,0), style=wx.NO_BORDER)
        self.Bind(wx.EVT_BUTTON, self.OnPreviousWeek, self.previous_button)
        self.Bind(wx.EVT_BUTTON, self.OnNextWeek, self.next_button)
        self.topsizer.Add(self.previous_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        self.topsizer.Add(self.next_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)

        # La combobox pour la selection de la semaine
        self.week_choice = wx.Choice(self, -1)
        self.topsizer.Add(self.week_choice, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.LEFT, 5)
        AddWeeksToChoice(self.week_choice)
        self.Bind(wx.EVT_CHOICE, self.OnChangementSemaine, self.week_choice)

        # La combobox pour la selection du groupe (si groupes)
        self.groupe_choice = wx.Choice(self, -1)
        self.topsizer.Add(self.groupe_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_CHOICE, self.OnChangeGroupeDisplayed, self.groupe_choice)
        self.UpdateGroupeCombobox()

        self.sizer.Add(self.topsizer, 0, wx.EXPAND)

    def GetSelectionStart(self):
        selection = self.week_choice.GetSelection()
        return self.week_choice.GetClientData(selection)

    def UpdateGroupeCombobox(self):
        if len(creche.groupes) > 0:
            self.groupe_choice.Clear()
            for groupe, value in [("Tous groupes", None)] + [(groupe.nom, groupe) for groupe in creche.groupes]:
                self.groupe_choice.Append(groupe, value)
            self.groupe_choice.SetSelection(0)
            self.groupe_choice.Show(True)
        else:
            self.groupe_choice.Show(False)
        self.groupes_observer = counters['groupes']

    def OnPreviousWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.OnChangementSemaine()

    def OnNextWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.OnChangementSemaine()

    def OnChangeGroupeDisplayed(self, evt):
        self.OnChangementSemaine()

    def GetSelectedSite(self):
        if len(creche.sites) > 1:
            self.current_site = self.site_choice.GetSelection()
            return self.site_choice.GetClientData(self.current_site)
        else:
            return None

    def GetSelectedGroupe(self):
        if len(creche.groupes) > 1:
            selection = self.groupe_choice.GetSelection()
            return self.groupe_choice.GetClientData(selection)
        else:
            return None


class PlanningHorairePanel(PlanningBasePanel):
    def __init__(self, parent):
        PlanningBasePanel.__init__(self, parent)

        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self)
        self.topsizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)

        # Le bouton d'impression
        bmp = wx.Bitmap(GetBitmapFile("printer.png"), wx.BITMAP_TYPE_PNG)
        button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
        self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnPrintPlanning, button)

        # Le bouton de synchro tablette
        if config.options & TABLETTE:
            bmp = wx.Bitmap(GetBitmapFile("tablette.png"), wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
            self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnTabletteSynchro, button)

        # Le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        first_monday = GetFirstMonday()
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        for week_day in range(7):
            if IsJourSemaineTravaille(week_day):
                date = first_monday + datetime.timedelta(semaine * 7 + week_day)
                planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
                self.notebook.AddPage(planning_panel, GetDateString(date))
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChangementSemaineday, self.notebook)
        self.sizer.Layout()

    def OnPrintPlanning(self, evt):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()
        start = self.GetSelectionStart()
        end = start + datetime.timedelta(6)
        DocumentDialog(self, PlanningDetailleModifications((start, end), site, groupe)).ShowModal()

    def OnChangementSemaineday(self, evt=None):
        self.notebook.GetCurrentPage().UpdateContents()

    def OnChangementSemaine(self, evt=None):
        self.UpdateWeek()
        self.notebook.SetSelection(0)
        self.sizer.Layout()

    def UpdateWeek(self):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()

        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.week_choice.GetClientData(week_selection)
        page_index = 0
        for week_day in range(7):
            if IsJourSemaineTravaille(week_day):
                day = monday + datetime.timedelta(week_day)
                self.notebook.SetPageText(page_index, GetDateString(day))
                note = self.notebook.GetPage(page_index)
                note.SetData(site, groupe, day)
                page_index += 1

    def OnTabletteSynchro(self, _):
        errors = tablette.sync_tablette()

        if errors:
            dlg = wx.MessageDialog(None, u"\n".join(errors), u'Erreurs de saisie tablette', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        self.UpdateWeek()

    def UpdateContents(self):
        if len(creche.sites) > 1:
            self.site_choice.Show(True)
            self.site_choice.Clear()
            for site in creche.sites:
                self.site_choice.Append(site.nom, site)
            self.site_choice.SetSelection(self.current_site)
        else:
            self.site_choice.Show(False)

        self.activity_choice.Update()

        if counters['groupes'] > self.groupes_observer:
            self.UpdateGroupeCombobox()

        self.OnChangementSemaine()
        self.sizer.Layout()


class PlanningHebdomadairePanel(PlanningBasePanel):
    def __init__(self, parent):
        PlanningBasePanel.__init__(self, parent)
        self.activites = []
        self.inscrits = []
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.SetDefaultColSize(200)
        self.grid.SetRowLabelSize(250)
        self.grid.EnableEditing(not readonly)
        self.sizer.Add(self.grid, -1, wx.EXPAND|wx.RIGHT|wx.TOP, 5)
        self.sizer.Layout()
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.OnCellChange, self.grid)

    def UpdateContents(self):
        self.OnChangementSemaine()

    def OnChangementSemaine(self, evt=None):
        self.grid.ClearGrid()
        site = self.GetSelectedSite()
        # groupe = self.GetSelectedGroupe()

        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.GetSelectionStart()
        sunday = monday + datetime.timedelta(6)

        old_count = self.grid.GetNumberCols()
        self.activites = creche.activites.values()
        new_count = len(self.activites)
        if new_count > old_count:
            self.grid.AppendCols(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteCols(0, old_count - new_count)

        for i, activity in enumerate(self.activites):
            self.grid.SetColLabelValue(i, activity.label)
            self.grid.SetColFormatFloat(i, precision=(0 if activity.mode == MODE_SANS_HORAIRES or creche.mode_saisie_planning == SAISIE_JOURS_SEMAINE else 1))

        self.inscrits = [inscrit for inscrit in creche.inscrits if inscrit.IsPresent(monday, sunday, site)]
        self.inscrits = GetEnfantsTriesSelonParametreTriPlanning(self.inscrits)
        old_count = self.grid.GetNumberRows()
        new_count = len(self.inscrits)
        if new_count > old_count:
            self.grid.AppendRows(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteRows(0, old_count - new_count)
        for row, inscrit in enumerate(self.inscrits):
            self.grid.SetRowLabelValue(row, GetPrenomNom(inscrit))
            if monday in inscrit.semaines:
                semaine = inscrit.semaines[monday]
                for i, activity in enumerate(self.activites):
                    if activity.value in semaine.activities:
                        self.grid.SetCellValue(row, i, locale.format("%f", semaine.activities[activity.value].value))
        self.sizer.Layout()

    def OnCellChange(self, evt):
        date = self.GetSelectionStart()
        value = self.grid.GetCellValue(evt.GetRow(), evt.GetCol())
        inscrit = self.inscrits[evt.GetRow()]
        if date not in inscrit.semaines:
            inscrit.semaines[date] = WeekPlanning(inscrit, date)
        history.Append(None)
        inscrit.semaines[date].SetActivity(self.activites[evt.GetCol()].value, float(value.replace(',', '.')))


if creche.mode_saisie_planning == SAISIE_HORAIRE:
    PlanningPanel = PlanningHorairePanel
else:
    PlanningPanel = PlanningHebdomadairePanel
