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
from planning import PlanningWidget, LigneConge, COMMENTS, ACTIVITES, TWO_PARTS, SUMMARY_NUM, SUMMARY_DEN
from ooffice import *
from doc_planning_detaille import PlanningDetailleModifications

class DayPlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_combobox):
        PlanningWidget.__init__(self, parent, activity_combobox, COMMENTS|ACTIVITES|TWO_PARTS)
        
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
        else:
            self.SetInfo("")
        
        lignes_enfants = []
        for inscrit in creche.inscrits:
            inscription = inscrit.GetInscription(self.date)
            if inscription is not None and (len(creche.sites) <= 1 or inscription.site is self.site) and (self.groupe is None or inscription.groupe == self.groupe):
                if creche.conges_inscription == GESTION_CONGES_INSCRIPTION_SIMPLE and self.date in inscrit.jours_conges:
                    line = LigneConge(inscrit.jours_conges[self.date].label)
                elif self.date in inscrit.journees:
                    line = inscrit.journees[self.date]
                    if creche.conges_inscription == GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT and self.date in inscrit.jours_conges:
                        line.reference = JourneeReferenceInscription(None, 0)
                        if not line.commentaire:
                            line.commentaire = inscrit.jours_conges[self.date].label
                    else:
                        line.reference = inscription.getJourneeReference(self.date)
                    line.insert = None
                    line.key = self.date
                elif creche.conges_inscription == GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT and self.date in inscrit.jours_conges:
                    reference = JourneeReferenceInscription(None, 0)
                    line = Journee(inscrit, self.date, reference)
                    line.reference = reference
                    line.commentaire = inscrit.jours_conges[self.date].label
                    line.insert = inscrit.journees
                    line.key = self.date
                else:
                    line = inscription.getJourneeReferenceCopy(self.date)
                    line.reference = inscription.getJourneeReference(self.date)
                    line.insert = inscrit.journees
                    line.key = self.date

                line.label = GetPrenomNom(inscrit)
                line.inscription = inscription
                line.options |= COMMENTS|ACTIVITES
                line.summary = SUMMARY_NUM
                def GetHeuresEnfant(line):
                    heures = line.GetNombreHeures()
                    if heures > 0:
                        return GetHeureString(heures)
                    else:
                        return None
                line.GetDynamicText = GetHeuresEnfant
                if creche.temps_facturation == FACTURATION_FIN_MOIS:
                    date = getMonthStart(self.date)
                else:
                    date = getNextMonthStart(self.date)
                if date in inscrit.factures_cloturees:
                    line.readonly = True
                lignes_enfants.append(line)
                
        if creche.tri_planning == TRI_GROUPE:
            lignes_enfants = TrieParGroupes(lignes_enfants)
        else:
            lignes_enfants.sort(key=lambda line: line.label)    
                 
        lignes_salaries = []
        for salarie in creche.salaries:
            contrat = salarie.GetContrat(self.date)
            if contrat is not None and (len(creche.sites) <= 1 or contrat.site is self.site):
                if self.date in salarie.journees:
                    line = salarie.journees[self.date]
                    line.reference = contrat.getJourneeReference(self.date)
                    line.insert = None
                else:
                    line = contrat.getJourneeReferenceCopy(self.date)
                    line.insert = salarie.journees
                    line.key = self.date
                line.salarie = salarie
                line.label = GetPrenomNom(salarie)
                line.contrat = contrat
                def GetHeuresSalarie(line):
                    date = line.date - datetime.timedelta(line.date.weekday())
                    heures_semaine = 0
                    for i in range(7):
                        if date in line.salarie.journees:
                            heures = line.salarie.journees[date].GetNombreHeures()
                        else:
                            heures = line.contrat.getJourneeReference(date).GetNombreHeures()
                        heures_semaine += heures
                        if date == line.date:
                            heures_jour = heures
                        date += datetime.timedelta(1)
                    return GetHeureString(heures_jour) + '/' + GetHeureString(heures_semaine)
                line.GetDynamicText = GetHeuresSalarie
                line.summary = SUMMARY_DEN
                lignes_salaries.append(line)
        lignes_salaries.sort(key=lambda line: line.label)    

        if lignes_salaries:
            lignes_enfants.append(None)
        self.SetLines(lignes_enfants + lignes_salaries)
    
    def GetSummaryDynamicText(self):
        heures = 0.0
        for line in self.lines:
            if line is None:
                break
            elif not isinstance(line, basestring):
                heures += line.GetNombreHeures()
        
        if heures > 0:
            text = GetHeureString(heures)
            den = creche.GetCapacite() * creche.GetAmplitudeHoraire()
            if den > 0:
                text += " / " + "%.1f" % (heures * 100 / den) + "%"
            return text 
        else:
            return None

    def SetData(self, site, groupe, date):
        self.site = site
        self.groupe = groupe
        self.date = date
        self.UpdateContents()
        

class PlanningPanel(GPanel):
    name = "Planning"
    bitmap = GetBitmapFile("planning.png")
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Planning')
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.current_site = 0
        
        # La combobox pour la selection du site
        self.site_choice = wx.Choice(self, -1)
        for site in creche.sites:
            self.site_choice.Append(site.nom, site)
        sizer.Add(self.site_choice, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        if len(creche.sites) < 2:
            self.site_choice.Show(False)
        self.site_choice.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.onChangeWeek, self.site_choice)
        
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
        
        # La combobox pour la selection du groupe (si groupes)
        self.groupe_choice = wx.Choice(self, -1)
        sizer.Add(self.groupe_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_CHOICE, self.onChangeGroupeDisplayed, self.groupe_choice)
        self.UpdateGroupeCombobox()
        
        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self)
        sizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        
        # Le bouton d'impression
        bmp = wx.Bitmap(GetBitmapFile("printer.png"), wx.BITMAP_TYPE_PNG)
        button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
        sizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.onPrintPlanning, button)
            
        # Le bouton de synchro tablette
        if config.options & TABLETTE:
            bmp = wx.Bitmap(GetBitmapFile("tablette.png"), wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, -1, bmp, style=wx.NO_BORDER)
            sizer.Add(button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.onTabletteSynchro, button)

        self.sizer.Add(sizer, 0, wx.EXPAND)
        
        # le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        for week_day in range(7):
            if JourSemaineAffichable(week_day):
                date = first_monday + datetime.timedelta(semaine * 7 + week_day)
                planning_panel = DayPlanningPanel(self.notebook, self.activity_choice)
                if len(creche.sites) > 1:
                    planning_panel.SetData(creche.sites[0], None, date)
                else:
                    planning_panel.SetData(None, None, date)
                self.notebook.AddPage(planning_panel, GetDateString(date))
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onChangeWeekday, self.notebook)
        self.sizer.Layout()
    
    def UpdateGroupeCombobox(self):
        if len(creche.groupes) > 0:
            self.groupe_choice.Clear()
            for groupe, value in [("Tous groupes", None)] + [(groupe.nom, groupe) for groupe in creche.groupes]:
                self.groupe_choice.Append(groupe, value)
            self.groupe_choice.SetSelection(0)
            self.groupe_choice.Show(True)
        else:
            self.groupe_choice.Show(False)
        self.last_groupe_observer = time.time()

    def onPrintPlanning(self, evt):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()
        week_selection = self.week_choice.GetSelection()
        start = self.week_choice.GetClientData(week_selection)
        end = start + datetime.timedelta(6)
        DocumentDialog(self, PlanningDetailleModifications((start, end), site, groupe)).ShowModal()

    def onChangeGroupeDisplayed(self, evt):
        self.onChangeWeek(None)
    
    def onChangeWeekday(self, evt=None):
        self.notebook.GetCurrentPage().UpdateDrawing()
    
    def GetSelectedSite(self):
        if len(creche.sites) > 1:
            self.current_site = self.site_choice.GetSelection()
            return self.site_choice.GetClientData(self.current_site)
        else:
            return None    

    def GetSelectedGroupe(self):
        if len(creche.groupes) > 1:
            self.current_groupe = self.groupe_choice.GetSelection()
            return self.groupe_choice.GetClientData(self.current_groupe)
        else:
            return None        
            
    def onChangeWeek(self, evt=None):
        site = self.GetSelectedSite()
        groupe = self.GetSelectedGroupe()
        
        week_selection = self.week_choice.GetSelection()
        self.previous_button.Enable(week_selection is not 0)
        self.next_button.Enable(week_selection is not self.week_choice.GetCount() - 1)
        monday = self.week_choice.GetClientData(week_selection)
        page_index = 0
        for week_day in range(7):
            if JourSemaineAffichable(week_day):
                day = monday + datetime.timedelta(week_day)
                self.notebook.SetPageText(page_index, GetDateString(day))
                note = self.notebook.GetPage(page_index)
                note.SetData(site, groupe, day)
                page_index += 1
        self.notebook.SetSelection(0)
        self.sizer.Layout()
        
    def onPreviousWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() - 1)
        self.onChangeWeek()
    
    def onNextWeek(self, evt):
        self.week_choice.SetSelection(self.week_choice.GetSelection() + 1)
        self.onChangeWeek()

    def onTabletteSynchro(self, evt):
        journal = config.connection.LoadJournal()
        
        class PeriodePresence(object):
            def __init__(self, date, arrivee, depart=None):
                self.date = date
                self.arrivee = arrivee
                self.depart = depart
        
        array = {}
        lines = journal.split("\n")
        
        index = -1
        if len(creche.last_tablette_synchro) > 20:
            try:
                index = lines.index(creche.last_tablette_synchro)
            except:
                pass

        for line in lines[index+1:]:
            try:
                label, idx, date = line.split()
                idx = int(idx)
                tm = time.strptime(date, "%Y-%m-%d@%H:%M")
                date = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
                if idx not in array:
                    array[idx] = []
                if label == "Arrivee":
                    arrivee = tm.tm_hour * 12 + tm.tm_min / creche.granularite * (creche.granularite/BASE_GRANULARITY)
                    array[idx].append(PeriodePresence(date, arrivee))
                elif label == "Depart":
                    depart = tm.tm_hour * 12 + (tm.tm_min+creche.granularite-1) / creche.granularite * (creche.granularite/BASE_GRANULARITY)
                    last = array[idx][-1]
                    if last.date == date and last.arrivee:
                        last.depart = depart
                    else:
                        array[idx].append(PeriodePresence(date, None, depart))
                creche.last_tablette_synchro = line
            except Exception, e:
                pass
        
        errors = []            
        for key in array:
            inscrit = creche.GetInscrit(key)
            if inscrit:
                for periode in array[key]:
                    if not periode.arrivee:
                        reference = inscrit.getJournee(periode.date)
                        periode.arrivee = reference.GetPlageHoraire()[0]
                        errors.append(u"%s : Pas d'arrivée enregistrée le %s" % (GetPrenomNom(inscrit), periode.date))
                    elif not periode.depart:
                        reference = inscrit.getJournee(date)
                        periode.depart = reference.GetPlageHoraire()[-1]
                        errors.append(u"%s : Pas de départ enregistré le %s" % (GetPrenomNom(inscrit), periode.date))
                    
                    if periode.date in inscrit.journees:
                        inscrit.journees[periode.date].remove_activities(0)
                        inscrit.journees[periode.date].remove_activities(0|PREVISIONNEL)
                    else:
                        inscrit.journees[periode.date] = Journee(inscrit, periode.date)
                    inscrit.journees[periode.date].SetActivity(periode.arrivee, periode.depart, 0)
                    history.Append(None)
            else:
                errors.append(u"Inscrit %d: Inconnu!" % key)
        if errors:
            dlg = wx.MessageDialog(None, u"\n".join(errors), u'Erreurs de saisie tablette', wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
        
        self.UpdateContents()
        
    def UpdateContents(self):
        if len(creche.sites) > 1:
            self.site_choice.Show(True)
            self.site_choice.Clear()
            for site in creche.sites:
                self.site_choice.Append(site.nom, site)
            self.site_choice.SetSelection(self.current_site)
        else:
            self.site_choice.Show(False)
            
        self.activity_choice.Clear()
        selected = 0
        if creche.HasActivitesAvecHoraires():
            self.activity_choice.Show(True)
            for i, activity in enumerate(creche.activites.values()):
                if activity.mode not in (MODE_SANS_HORAIRES, MODE_SYSTEMATIQUE_SANS_HORAIRES):
                    self.activity_choice.Append(activity.label, activity)
                    try:
                        if self.activity_choice.activity.value == activity.value:
                            selected = i
                    except:
                        pass
        else:
            self.activity_choice.Show(False)
            self.activity_choice.Append(creche.activites[0].label, creche.activites[0])
        self.activity_choice.SetSelection(selected)
        
        if 'groupes' in observers and observers['groupes'] > self.last_groupe_observer:
            self.UpdateGroupeCombobox()
            
        self.onChangeWeek()
        self.sizer.Layout()

