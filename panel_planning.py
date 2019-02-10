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

from __future__ import unicode_literals
from __future__ import print_function

from controls import *
from generation.planning_hebdomadaire import PlanningHebdomadaireSalariesModifications
from planning import PlanningWidget, BaseWxPythonLine, WxPlanningSeparator
from planning_line import *
from document_dialog import *
from generation.planning_detaille import PlanningDetailleModifications
import tablette


class WxChildPlanningLine(ChildPlanningLine, BaseWxPythonLine):
    pass


class WxSalariePlanningLine(SalariePlanningLine, BaseWxPythonLine):
    pass


# TODO make those function names consistent
def timeslots_intersection(timeslot1, timeslot2):
    min_ts, max_ts = (timeslot1, timeslot2) if timeslot1.debut < timeslot2.debut else (timeslot2, timeslot1)
    if min_ts.fin <= max_ts.debut:
        return None
    else:
        return Timeslot(max_ts.debut, min_ts.fin if min_ts.fin < max_ts.fin else max_ts.fin, timeslot1.activity, value=timeslot1.value)


def check_timeslot(timeslot, max_timeslots, check_function):
    result = []
    for max_timeslot in max_timeslots:
        intersection = timeslots_intersection(timeslot, max_timeslot)
        if intersection:
            result = []
            if intersection.debut != timeslot.debut:
                result.extend(check_timeslot(Timeslot(timeslot.debut, intersection.debut, None, value=timeslot.value), max_timeslots, check_function))
            result.append(Timeslot(intersection.debut, intersection.fin, timeslot.activity, value=timeslot.value, overflow=not check_function(timeslot.value, max_timeslot.value)))
            if intersection.fin != timeslot.fin:
                result.extend(check_timeslot(Timeslot(intersection.fin, timeslot.fin, None, value=timeslot.value), max_timeslots, check_function))
            break
    else:
        timeslot.overflow = not check_function(timeslot.value, 0)
        result.append(timeslot)
    result.sort(key=lambda timeslot: timeslot.debut)
    i = 0
    while i < len(result) - 1:
        timeslot1 = result[i]
        timeslot2 = result[i+1]
        if timeslot1.fin == timeslot2.debut and timeslot1.value == timeslot2.value and timeslot1.overflow == timeslot2.overflow:
            timeslot1.fin = timeslot2.fin
            del result[i+1]
        else:
            i += 1
    return result


def fill_timeslots_with_zero(timeslots, debut, fin):
    if timeslots:
        timeslots.sort(key=lambda timeslot: timeslot.debut)
        if timeslots[0].debut > debut:
            timeslots.insert(0, Timeslot(debut, timeslots[0].debut, None, value=0))
        if timeslots[-1].fin < fin:
            timeslots.append(Timeslot(timeslots[-1].fin, fin, None, value=0))
        i = 0
        while i < len(timeslots) - 1:
            if timeslots[i].fin < timeslots[i + 1].debut:
                timeslots.insert(i + 1, Timeslot(timeslots[i].fin, timeslots[i + 1].debut, None, value=0))
            i += 1
    else:
        timeslots.append(Timeslot(debut, fin, None, value=0))


def filter_zero_and_not_overflow_timeslots(timeslots):
    return [timeslot for timeslot in timeslots if timeslot.value or timeslot.overflow]


class DayPlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_combobox):
        PlanningWidget.__init__(self, parent, activity_combobox, COMMENTS | ACTIVITES | TWO_PARTS | DEPASSEMENT_CAPACITE)

    def get_summary(self):
        activites, activites_sans_horaires = PlanningWidget.get_summary(self)
        activite_presence_enfants = database.creche.states[0]
        if activite_presence_enfants in activites:
            children_presence = activites[activite_presence_enfants]
            revised_children_presence = []
            for timeslot in children_presence:
                revised_children_presence.extend(check_timeslot(timeslot, database.creche.tranches_capacite.get(self.date.weekday(), Day()).timeslots, lambda timeslot, capacite_timeslot: timeslot <= capacite_timeslot))
            activites[activite_presence_enfants] = revised_children_presence
            if database.creche.salaries:
                debut, fin = revised_children_presence[0].debut, revised_children_presence[-1].fin
                activite_presence_salaries = database.creche.states[PRESENCE_SALARIE]
                if activite_presence_salaries in activites:
                    salaries_presence = activites[activite_presence_salaries]
                    fill_timeslots_with_zero(salaries_presence, debut, fin)
                    revised_salaries_presence = []
                    for timeslot in salaries_presence:
                        revised_salaries_presence.extend(check_timeslot(timeslot, children_presence, lambda timeslot, children_timeslot: timeslot * 6.5 >= children_timeslot))
                    activites[activite_presence_salaries] = filter_zero_and_not_overflow_timeslots(revised_salaries_presence)
        return activites, activites_sans_horaires

    print("TODO CheckLine / CheckDate pas appelé")
    def CheckLine(self, line, plages_selectionnees):
        lines = self.GetSummaryLines()
        activites, activites_sans_horaires = GetActivitiesSummary(lines)
        for start, end in plages_selectionnees:
            for i in range(start, end):
                if activites[0][i][0] > database.creche.get_capacite(line.day):
                    dlg = wx.MessageDialog(None, "Dépassement de la capacité sur ce créneau horaire !", "Attention", wx.OK|wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()
                    self.state = None
                    return

    def UpdateContents(self):
        if self.date in database.creche.jours_fermeture:
            conge = database.creche.jours_fermeture[self.date]
            if conge.options == ACCUEIL_NON_FACTURE:
                self.SetInfo(conge.label)
            else:
                if conge.label:
                    self.Disable(conge.label)
                else:
                    self.Disable("Etablissement fermé")
                return
        else:
            self.SetInfo("")

        self.lignes_enfants = WxChildPlanningLine.select(self.date, self.site, self.groupe)
        if database.creche.groupes and (database.creche.tri_planning & TRI_GROUPE):
            groupe = 0
            lines = []
            for line in self.lignes_enfants:
                if groupe != line.inscription.groupe:
                    groupe = line.inscription.groupe
                    lines.append(WxPlanningSeparator(groupe.nom if groupe else ""))
                lines.append(line)
        else:
            lines = self.lignes_enfants[:]

        self.lignes_salaries = WxSalariePlanningLine.select(self.date, self.site)
        if self.lignes_salaries:
            lines.append(WxPlanningSeparator("Salariés"))
            lines += self.lignes_salaries
        self.SetLines(lines)

    def GetSummaryDynamicText(self):
        heures = 0.0
        for line in self.lignes_enfants:
            heures += line.day.get_duration() if line.day else line.reference.get_duration()
            # day = line.day

        if heures > 0:
            text = GetHeureString(heures)
            if self.site:
                den = self.site.capacite * database.creche.get_amplitude_horaire()
            else:
                den = database.creche.GetHeuresAccueil(self.date.weekday())
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
    profil = PROFIL_PLANNING

    def __init__(self, parent):
        GPanel.__init__(self, parent, 'Planning')
        self.topsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_site = 0

        # La combobox pour la selection du site
        self.site_choice = wx.Choice(self, -1)
        for site in database.creche.sites:
            self.site_choice.Append(site.get_name(), site)
        self.topsizer.Add(self.site_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.RIGHT, 5)
        if len(database.creche.sites) < 2:
            self.site_choice.Show(False)
        self.site_choice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.OnChangementSemaine, self.site_choice)

        # Les raccourcis pour semaine précédente / suivante
        self.previous_button = wx.Button(self, -1, '<', size=(20, 0), style=wx.NO_BORDER)
        self.next_button = wx.Button(self, -1, '>', size=(20, 0), style=wx.NO_BORDER)
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
        if len(database.creche.groupes) > 0:
            self.groupe_choice.Clear()
            for groupe, value in [("Tous groupes", None)] + [(groupe.nom, groupe) for groupe in database.creche.groupes]:
                self.groupe_choice.Append(groupe, value)
            self.groupe_choice.SetSelection(0)
            self.groupe_choice.Show(True)
        else:
            self.groupe_choice.Show(False)
        self.groupes_observer = counters['groupes']

    def OnPreviousWeek(self, _):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.OnChangementSemaine()

    def OnNextWeek(self, _):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.OnChangementSemaine()

    def OnChangeGroupeDisplayed(self, _):
        self.OnChangementSemaine()

    def GetSelectedSite(self):
        if len(database.creche.sites) > 1:
            self.current_site = self.site_choice.GetSelection()
            return self.site_choice.GetClientData(self.current_site)
        else:
            return None

    def GetSelectedGroupe(self):
        if len(database.creche.groupes) > 1:
            selection = self.groupe_choice.GetSelection()
            return self.groupe_choice.GetClientData(selection)
        else:
            return None


class PlanningHorairePanel(PlanningBasePanel):
    def __init__(self, parent):
        PlanningBasePanel.__init__(self, parent)

        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self)
        self.topsizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        # Les boutons d'impression
        bmp = wx.Bitmap(GetBitmapFile("printer.png"), wx.BITMAP_TYPE_PNG)
        button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
        self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.OnPrintPlanning, button)
        if IsTemplateFile("Planning hebdomadaire salaries.ods"):
            button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
            self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnPrintPlanningSalaries, button)

        # Le bouton de synchro tablette
        if config.options & TABLETTE:
            bmp = wx.Bitmap(GetBitmapFile("tablette.png"), wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
            self.topsizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnTabletteSynchro, button)

        # Le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        first_monday = config.get_first_monday()
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        for week_day in range(7):
            if database.creche.is_jour_semaine_travaille(week_day):
                date = first_monday + datetime.timedelta(semaine * 7 + week_day)
                planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
                self.notebook.AddPage(planning_panel, GetDateString(date))
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChangementSemaineday, self.notebook)
        self.sizer.Layout()

    def OnPrintPlanning(self, _):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()
        start = self.GetSelectionStart()
        end = start + datetime.timedelta(6)
        DocumentDialog(self, PlanningDetailleModifications((start, end), site, groupe)).ShowModal()

    def OnPrintPlanningSalaries(self, _):
        start = self.GetSelectionStart()
        DocumentDialog(self, PlanningHebdomadaireSalariesModifications(start)).ShowModal()

    def OnChangementSemaineday(self, _):
        self.notebook.GetCurrentPage().UpdateContents()

    def OnChangementSemaine(self, _=None):
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
            if database.creche.is_jour_semaine_travaille(week_day):
                day = monday + datetime.timedelta(week_day)
                self.notebook.SetPageText(page_index, GetDateString(day))
                note = self.notebook.GetPage(page_index)
                note.SetData(site, groupe, day)
                page_index += 1
            else:
                print("TODO desactiver la page si elle existe")

    def OnTabletteSynchro(self, _):
        errors = tablette.sync_tablette()

        if errors:
            dlg = wx.MessageDialog(None, "\n".join(errors), 'Erreurs de saisie tablette', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

        self.UpdateWeek()

    def UpdateContents(self):
        if len(database.creche.sites) > 1:
            self.site_choice.Show(True)
            self.site_choice.Clear()
            for site in database.creche.sites:
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
        self.grid.EnableEditing(not config.readonly)
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
        self.activites = database.creche.activites
        new_count = len(self.activites)
        if new_count > old_count:
            self.grid.AppendCols(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteCols(0, old_count - new_count)

        for i, activity in enumerate(self.activites):
            self.grid.SetColLabelValue(i, activity.label)
            self.grid.SetColFormatFloat(i, precision=(0 if activity.mode == MODE_SANS_HORAIRES or database.creche.mode_saisie_planning == SAISIE_JOURS_SEMAINE else 1))

        self.inscrits = [inscrit for inscrit in database.creche.inscrits if inscrit.is_present(monday, sunday, site)]
        self.inscrits = GetEnfantsTriesSelonParametreTriPlanning(self.inscrits)
        old_count = self.grid.GetNumberRows()
        new_count = len(self.inscrits)
        if new_count > old_count:
            self.grid.AppendRows(new_count - old_count)
        elif old_count > new_count:
            self.grid.DeleteRows(0, old_count - new_count)
        for row, inscrit in enumerate(self.inscrits):
            self.grid.SetRowLabelValue(row, GetPrenomNom(inscrit))
            for i, activity in enumerate(self.activites):
                # print(activity)
                activity_slot = inscrit.get_week_activity_slot(monday, activity)
                if activity_slot:
                    self.grid.SetCellValue(row, i, locale.format("%f", activity_slot.value if activity_slot.value else 0))
        self.sizer.Layout()

    def OnCellChange(self, evt):
        date = self.GetSelectionStart()
        value = self.grid.GetCellValue(evt.GetRow(), evt.GetCol())
        # print("HEHEHE", value.replace(',', '.'))
        value_str = value.replace(',', '.').strip()
        if value_str:
            value = float(value_str)
        else:
            value = None
        inscrit = self.inscrits[evt.GetRow()]
        activity_value = self.activites[evt.GetCol()]
        history.Append(None)
        week_slot = inscrit.get_week_activity_slot(date, activity_value)
        if week_slot:
            week_slot.value = value
        else:
            inscrit.weekslots.append(WeekSlotInscrit(inscrit=inscrit, date=date, activity=activity_value, value=value))


def get_planning_class():
    if database.creche.mode_saisie_planning == SAISIE_HORAIRE:
        return PlanningHorairePanel
    else:
        return PlanningHebdomadairePanel
