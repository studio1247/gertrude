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
import wx, wx.lib.scrolledpanel, wx.html, wx.grid, wx.lib.expando
from constants import *
from functions import *
from controls import *
from ooffice import *
from planning_presences import PlanningModifications
from coordonnees_parents import CoordonneesModifications
from etats_trimestriels import EtatsTrimestrielsModifications
from planning_detaille import PlanningDetailleModifications
from etats_presence import EtatsPresenceModifications
from facture import FactureFinMois
from planning import *
from sqlobjects import Day

class SitesPlanningPanel(PlanningWidget):
    def UpdateContents(self):
        if "Week-end" in creche.feries:
            self.count = 5
        else:
            self.count = 7
            
        first_monday = getFirstMonday()
        
        lines = []
        for week_day in range(self.count):
            date = first_monday + datetime.timedelta(self.semaine * 7 + week_day)
            if date in creche.jours_fermeture:
                continue
            
            day_lines = {}
            if len(creche.sites) > 1:
                lines.append(days[week_day])
                for site in creche.sites:
                    line = Day()
                    for i in range(int(creche.ouverture*60/BASE_GRANULARITY), int(creche.fermeture*60/BASE_GRANULARITY)):
                        line.values[i] = site.capacite
                    line.label = site.nom
                    day_lines[site] = line
                    lines.append(line)
            else:
                site_line = Day()
                for i in range(int(creche.ouverture*60/BASE_GRANULARITY), int(creche.fermeture*60/BASE_GRANULARITY)):
                    site_line.values[i] = creche.capacite
                site_line.reference = None
                site_line.label = days[week_day]
                lines.append(site_line)
            
            for inscrit in creche.inscrits:
                inscription = inscrit.getInscription(date)
                if inscription is not None:
                    if date in inscrit.journees:
                        line = inscrit.journees[date]
                    else:
                        line = inscrit.getReferenceDay(date)
                    if len(creche.sites) > 1:
                        if inscription.site and inscription.site in day_lines:
                            site_line = day_lines[inscription.site]
                        else:
                            continue
                    for i, value in enumerate(line.values):
                        if value > 0 and value & PRESENT:
                            site_line.values[i] -= 1

        self.SetLines(lines)

    def SetData(self, semaine):
        self.semaine = semaine
        self.UpdateContents()
        

class PlacesDisponiblesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_site = 0
        
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
        self.sizer.Add(sizer, 0, wx.EXPAND)
                
        self.planning_panel = SitesPlanningPanel(self, options=DRAW_NUMBERS|NO_ICONS|NO_BOTTOM_LINE|READ_ONLY)
        self.planning_panel.SetData(semaine)
            
        self.sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.sizer.Layout()
        self.SetSizer(self.sizer)

    def onChangeWeek(self, evt=None):   
        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.week_choice.GetClientData(week_selection)
        self.planning_panel.SetData(week_selection)
        self.sizer.Layout()
        
    def onPreviousWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.onChangeWeek()
    
    def onNextWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.onChangeWeek()
        
    def UpdateContents(self):            
        self.onChangeWeek()


class EtatsPresenceTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.search_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.debut_control = DateCtrl(self)
        wx.EVT_TEXT(self.debut_control, -1, self.onPeriodeChange)
        self.search_sizer.AddMany([(wx.StaticText(self, -1, u'Début :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.debut_control, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.fin_control = DateCtrl(self)
        wx.EVT_TEXT(self.fin_control, -1, self.onPeriodeChange)
        self.search_sizer.AddMany([(wx.StaticText(self, -1, u'Fin :'), 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5), (self.fin_control, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.ordered_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.unordered_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sites_choice = wx.Choice(self)
        self.sites_choice.fill_function = self.FillSites
        self.sites_choice.parameter = "site"
        self.inscrits_choice = wx.Choice(self)
        self.inscrits_choice.fill_function = self.FillInscrits
        self.inscrits_choice.parameter = "inscrit"
        self.unordered_sizer.AddMany([(self.sites_choice, 0, wx.LEFT, 5), (self.inscrits_choice, 0, wx.LEFT, 5)])
        self.search_sizer.AddMany([(self.ordered_sizer, 0, wx.ALIGN_CENTER_VERTICAL), (self.unordered_sizer, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(self.search_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.ordered = []
        self.unordered = [self.sites_choice, self.inscrits_choice]
        self.debut_value = None
        self.fin_value = None
        
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        ok = wx.Button(self, wx.ID_OK)
        sizer2.Add(ok, 0)
        export = wx.Button(self, -1, "Export")
        sizer2.Add(export)
        self.sizer.Add(sizer2, 0, wx.ALL, 5)
        
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 3)
        # self.grid.EnableScrolling(False, False)
        self.grid.SetRowLabelSize(1)
        self.grid.SetColLabelValue(0, "Date")
        self.site_col_displayed = False
        self.grid.SetColLabelValue(1, "Inscrit")
        self.grid.SetColLabelValue(2, "Heures")
        self.grid.SetColSize(0, 155)
        self.grid.SetColSize(1, 155)
        self.grid.SetColSize(2, 200)
        self.sizer.Add(self.grid, -1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.UpdateContents()
        
        self.Bind(wx.EVT_BUTTON, self.onOk, ok)
        self.Bind(wx.EVT_BUTTON, self.onExport, export)
        self.Bind(wx.EVT_CHOICE, self.onChoice, self.sites_choice)
        self.Bind(wx.EVT_CHOICE, self.onChoice, self.inscrits_choice)

    def FillSites(self, debut=None, fin=None, inscrit=None):
        if len(creche.sites) < 2:
            self.sites_choice.Show(False)
            return
        
        if debut is None and fin is None and inscrit is None:
            sites = creche.sites
        else:
            sites = set()
            if inscrit:
                inscrits = [inscrit]
            else:
                inscrits = creche.inscrits
            for inscrit in inscrits:
                for inscription in inscrit.getInscriptions(debut, fin):
                    if inscription.site and inscription.site not in sites:
                        sites.add(inscription.site)
        self.sites_choice.Show(True)
        self.sites_choice.Clear()
        self.sites_choice.Append("Tous les sites", None)
        for site in sites:
            self.sites_choice.Append(site.nom, site)
        self.sites_choice.Select(0)
    
    def FillInscrits(self, debut=None, fin=None, site=None):
        self.inscrits_choice.Clear()
        self.inscrits_choice.Append("Tous les inscrits", None)
        if debut is None and fin is None and site is None:
            inscrits = creche.inscrits
        else:
            inscrits = set()
            for inscrit in creche.inscrits:
                for inscription in inscrit.getInscriptions(debut, fin):
                    if site is None or inscription.site == site:
                        inscrits.add(inscrit)

        self.inscrits_choice.Clear()
        self.inscrits_choice.Append("Tous les inscrits", None)
        for inscrit in inscrits:
            self.inscrits_choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        self.inscrits_choice.Select(0)
        
    def UpdateContents(self):
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())
        if len(creche.sites) < 2:
            if self.site_col_displayed:
                self.grid.DeleteCols(1)
                self.site_col_displayed = False
        else:
            if not self.site_col_displayed:
                self.grid.InsertCols(1)
                self.grid.SetColLabelValue(1, "Site")
                self.grid.SetColSize(1, 100)
                self.site_col_displayed = True   
        self.grid.ForceRefresh()
        self.FillSites()
        self.FillInscrits()
        self.sizer.FitInside(self)
    
    def onPeriodeChange(self, event):
        debut_value = self.debut_control.GetValue()
        fin_value = self.fin_control.GetValue()
        if debut_value != self.debut_value or fin_value != self.fin_value:
            self.debut_value = debut_value
            self.fin_value = fin_value
            kwargs = {"debut": debut_value, "fin": fin_value}
            for ctrl in self.ordered:
                selection = ctrl.GetStringSelection()
                ctrl.fill_function(**kwargs)
                ctrl.SetStringSelection(selection)
                if ctrl.GetSelection() == 0:
                    self.move_to_unordered(ctrl)
                else:
                    kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
            for ctrl in self.unordered:
                ctrl.fill_function(**kwargs)
    
    def move_to_unordered(self, object):
        kwargs = {"debut": self.debut_control.GetValue(), "fin": self.fin_control.GetValue()}
        index = self.ordered.index(object)
        self.ordered.remove(object)
        self.ordered_sizer.Detach(object)
        self.unordered.insert(0, object)
        self.unordered_sizer.Insert(0, object, 0, wx.LEFT, 5)
        for ctrl in self.ordered[:index]:
            kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
        for ctrl in self.ordered[index:]:
            selection = ctrl.GetStringSelection()
            ctrl.fill_function(**kwargs)
            ctrl.SetStringSelection(selection)
            kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
        for ctrl in self.unordered:
            ctrl.fill_function(**kwargs)
        self.sizer.Layout()
            
    def onChoice(self, event):
        object = event.GetEventObject()
        selection = object.GetSelection()
        value = object.GetClientData(selection)
        if value is None:
            if object in self.ordered:
                self.move_to_unordered(object)
        else:
            kwargs = {"debut": self.debut_control.GetValue(), "fin": self.fin_control.GetValue()}
            if object in self.unordered:
                self.unordered.remove(object)
                self.unordered_sizer.Detach(object)
                self.ordered.append(object)
                self.ordered_sizer.Add(object, 0, wx.LEFT, 5)
                self.sizer.Layout()
                for ctrl in self.ordered:
                    kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
                for ctrl in self.unordered:
                    ctrl.fill_function(**kwargs)
            else:
                index = self.ordered.index(object)
                for ctrl in self.ordered[:index]:
                    kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
                for ctrl in self.ordered[index:]:
                    selection = ctrl.GetStringSelection()
                    ctrl.fill_function(**kwargs)
                    ctrl.SetStringSelection(selection)
                    kwargs[ctrl.parameter] = ctrl.GetClientData(ctrl.GetSelection())
                for ctrl in self.unordered:
                    ctrl.fill_function(**kwargs)
        event.Skip()
        
    def GetSelection(self):
        debut = self.debut_control.GetValue()
        fin = self.fin_control.GetValue()
        if len(creche.sites) < 2:
            site = None
        else:
            site = self.sites_choice.GetClientData(self.sites_choice.GetSelection())
        inscrit = self.inscrits_choice.GetClientData(self.inscrits_choice.GetSelection())

        if inscrit:
            inscrits = [inscrit]
        else:
            inscrits = creche.inscrits
        if not debut:
            debut = datetime.date(2004, 1, 1)
        if not fin:
            fin = last_date
        
        selection = {}
        for inscrit in inscrits:
            for inscription in inscrit.getInscriptions(debut, fin):
                if site is None or inscription.site == site:
                    date = max(debut, inscription.debut)
                    if inscription.fin:
                        date_fin = min(fin, inscription.fin)
                    else:
                        date_fin = fin
                    while date <= date_fin:
                        state, contrat, realise, supplementaire = inscrit.getState(date)
                        if state > 0 and state & PRESENT:
                            if date not in selection:
                                selection[date] = []
                            selection[date].append((inscription.site, inscrit, contrat+supplementaire))
                        date += datetime.timedelta(1)
        return selection
    
    def onOk(self, event):
        selection = self.GetSelection()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())
        row = 0
        dates = selection.keys()
        dates.sort()
        for date in dates:
            for site, inscrit, heures in selection[date]:
                self.grid.AppendRows(1)
                self.grid.SetCellValue(row, 0, date2str(date))
                inscrit_column = 1
                if self.site_col_displayed:
                    inscrit_column = 2
                    if site:
                        self.grid.SetCellValue(row, 1, site.nom)
                self.grid.SetCellValue(row, inscrit_column, "%s %s" % (inscrit.prenom, inscrit.nom))
                self.grid.SetCellValue(row, inscrit_column+1, str(heures))
                row += 1
        self.grid.ForceRefresh()
        
    def onExport(self, event):
        debut = self.debut_control.GetValue()
        fin = self.fin_control.GetValue()
        if len(creche.sites) < 2:
            site = None
        else:
            site = self.sites_choice.GetClientData(self.sites_choice.GetSelection())
        inscrit = self.inscrits_choice.GetClientData(self.inscrits_choice.GetSelection())
        
        selection = self.GetSelection()
        DocumentDialog(self, EtatsPresenceModifications(debut, fin, site, inscrit, selection)).ShowModal()
          
class StatistiquesFrequentationTab(AutoTab):
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
        
        self.message = wx.lib.expando.ExpandoTextCtrl(self)
        self.message.Disable()
        self.message.SetValue("")
        self.message.Show(False)
        self.sizer.Add(self.message, 0, wx.EXPAND|wx.ALL, 10)
        
        self.result_sizer = wx.FlexGridSizer(0, 3, 5, 10)
        self.presences_contrat_heures = wx.TextCtrl(self)
        self.presences_contrat_heures.Disable()
        self.presences_contrat_euros = wx.TextCtrl(self)
        self.presences_contrat_euros.Disable()
        self.result_sizer.AddMany([(wx.StaticText(self, -1, u'Présences contractualisées :'), 0, 0), (self.presences_contrat_heures, 0, wx.EXPAND), (self.presences_contrat_euros, 0, wx.EXPAND)])
        self.presences_realisees_heures = wx.TextCtrl(self)
        self.presences_realisees_heures.Disable()
        self.presences_realisees_euros = wx.TextCtrl(self)
        self.presences_realisees_euros.Disable()
        self.result_sizer.AddMany([(wx.StaticText(self, -1, u'Présences réalisées :'), 0, 0), (self.presences_realisees_heures, 0, wx.EXPAND), (self.presences_realisees_euros, 0, wx.EXPAND)])
        self.presences_facturees_heures = wx.TextCtrl(self)
        self.presences_facturees_heures.Disable()
        self.presences_facturees_euros = wx.TextCtrl(self)
        self.presences_facturees_euros.Disable()
        self.result_sizer.AddMany([(wx.StaticText(self, -1, u'Présences facturées :'), 0, 0), (self.presences_facturees_heures, 0, wx.EXPAND), (self.presences_facturees_euros, 0, wx.EXPAND)])       
        self.sizer.Add(self.result_sizer, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self.sizer)
        self.Layout()
        
    def UpdateContents(self):
        self.EvtPeriodeChoice(None)
        
    def EvtPeriodeChoice(self, evt):
        annee = self.anneechoice.GetClientData(self.anneechoice.GetSelection())
        periode = self.periodechoice.GetClientData(self.periodechoice.GetSelection())
        heures_contractualisees = 0.0
        heures_realisees = 0.0
        heures_facturees = 0.0
        cotisations_contractualisees = 0.0
        cotisations_realisees = 0.0
        cotisations_facturees = 0.0
        erreurs = []
        for mois in periode:
            debut = datetime.date(annee, mois+1, 1)
            fin = getMonthEnd(debut)
            for inscrit in creche.inscrits:
                try:
                    if inscrit.getInscriptions(debut, fin):
                        facture = FactureFinMois(inscrit, annee, mois+1)
                        # print inscrit.prenom, mois, facture.heures_contrat, facture.heures_realisees
                        heures_contractualisees += facture.heures_contractualisees
                        heures_realisees += facture.heures_realisees                       
                        heures_facturees += sum(facture.heures_facturees)
                        cotisations_contractualisees += facture.cotisation_mensuelle
                        cotisations_realisees += facture.total_realise
                        cotisations_facturees += facture.total
                except Exception, e:
                    erreurs.append((inscrit, e))
                              
        if erreurs:
            msg = "\n\n".join([u"%s %s:\n%s" % (inscrit.prenom, inscrit.nom, str(erreur)) for inscrit, erreur in erreurs])
            self.message.SetValue(msg)
            self.message.Show(True)
            self.presences_contrat_heures.SetValue("-")
            self.presences_realisees_heures.SetValue("-")
            self.presences_facturees_heures.SetValue("-")
            self.presences_contrat_euros.SetValue("-")
            self.presences_realisees_euros.SetValue("-")
            self.presences_facturees_euros.SetValue("-")
        else:
            self.message.Show(False)
            self.presences_contrat_heures.SetValue("%.2f heures" % heures_contractualisees)
            self.presences_realisees_heures.SetValue("%.2f heures" % heures_realisees)
            self.presences_facturees_heures.SetValue("%.2f heures" % heures_facturees)
            self.presences_contrat_euros.SetValue("%.2f €" % cotisations_contractualisees)
            self.presences_realisees_euros.SetValue("%.2f €" % cotisations_realisees)
            self.presences_facturees_euros.SetValue("%.2f €" % cotisations_facturees)
        self.Layout()       
        self.sizer.FitInside(self)

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
        
class RelevesNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(PlacesDisponiblesTab(self), "Places disponibles")
        self.AddPage(EtatsPresenceTab(self), u"Etats de présence")
        self.AddPage(StatistiquesFrequentationTab(self), u'Statistiques de fréquentation')
        self.AddPage(RelevesTab(self), u'Edition de relevés')

    def UpdateContents(self):
        for page in range(self.GetPageCount()):
            self.GetPage(page).UpdateContents()
        
class RelevesPanel(GPanel):
    bitmap = './bitmaps/releves.png'
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Tableaux de bord')
        self.notebook = RelevesNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()