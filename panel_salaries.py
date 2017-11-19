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
from __future__ import division

import os, datetime, time, xml.dom.minidom
import wx, wx.lib.scrolledpanel, wx.html
from constants import *
from controls import *
from database import TimeslotPlanningSalarie, CongeSalarie, ContratSalarie, Salarie, PlanningSalarie
from planning import *
from cotisation import *
from ooffice import *
            
wildcard = "PNG (*.png)|*.png|"     \
           "BMP (*.pmp)|*.bmp|"     \
           "All files (*.*)|*.*"


class SalariesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.salarie = None

    def SetSalarie(self, salarie):
        self.salarie = salarie
        for ctrl in self.ctrls:
            ctrl.SetInstance(salarie)


class IdentiteSalariePanel(SalariesTab):
    def __init__(self, parent):
        SalariesTab.__init__(self, parent)
        self.salarie = None
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 10)
        self.sizer2 = sizer2
        sizer2.AddGrowableCol(1, 1)
        prenom_ctrl = AutoTextCtrl(self, None, 'prenom')
        self.Bind(wx.EVT_TEXT, self.EvtChangementPrenomNom, prenom_ctrl)
        nom_ctrl = AutoTextCtrl(self, None, 'nom')
        self.Bind(wx.EVT_TEXT, self.EvtChangementPrenomNom, nom_ctrl)
        sizer2.AddMany([(wx.StaticText(self, -1, 'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (prenom_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (nom_ctrl, 0, wx.EXPAND)])
        for label, field in ("Téléphone domicile", "telephone_domicile"), ("Téléphone portable", "telephone_portable"):
            sizer3 = wx.BoxSizer(wx.HORIZONTAL)
            sizer3.AddMany([(AutoPhoneCtrl(self, None, field), 0), (AutoTextCtrl(self, None, field+'_notes'), 1, wx.LEFT|wx.EXPAND, 5)])
            sizer2.AddMany([(wx.StaticText(self, -1, label+' :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'E-mail :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'email'), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, "Diplômes :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoComboBox(self, None, 'diplomes', choices=["CAP petite enfance", "Auxiliaire puéricultrice", "EJE", "Puéricultrice", "Sans objet"]), 0, wx.EXPAND)])
        self.sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        if config.options & TABLETTE:
            self.tabletteSizer = TabletteSizer(self, self.salarie)
            self.sizer.Add(self.tabletteSizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.FitInside(self)
        
    def EvtChangementPrenomNom(self, event):
        event.GetEventObject().onText(event)
        self.parent.EvtChangementPrenomNom(event)

    def EvtChangementDateNaissance(self, event):
        date_naissance = self.date_naissance_ctrl.GetValue()
        self.age_ctrl.SetValue(GetAgeString(date_naissance))

    def EvtChangementCodePostal(self, event):
        code_postal = self.code_postal_ctrl.GetValue()
        if code_postal and not self.ville_ctrl.GetValue():
            for salarie in database.creche.salaries:
                if salarie.code_postal == code_postal and salarie.ville:
                    self.ville_ctrl.SetValue(salarie.ville)
                    break
        
    def UpdateContents(self):
        AutoTab.UpdateContents(self)
        if config.options & TABLETTE:
            self.tabletteSizer.UpdateCombinaison()
        self.sizer.FitInside(self)
        
    def SetSalarie(self, salarie):
        self.salarie = salarie
        if config.options & TABLETTE:
            self.tabletteSizer.SetObject(salarie)
        self.UpdateContents()
        SalariesTab.SetSalarie(self, salarie)


class CongesPanel(SalariesTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        
        SalariesTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.conges_creche_sizer = wx.BoxSizer(wx.VERTICAL)
        self.AfficheCongesCreche()
        self.sizer.Add(self.conges_creche_sizer, 0, wx.ALL, 5)
        
        self.conges_salarie_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.conges_salarie_sizer, 0, wx.ALL, 5)
        
        self.nouveau_conge_button = wx.Button(self, -1, 'Nouvelle période de congés')
        self.sizer.Add(self.nouveau_conge_button, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnCongeAdd, self.nouveau_conge_button)

#        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.AddMany([(wx.StaticText(self, -1, 'Nombre de semaines de congés déduites :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'semaines_conges', min=0, precision=0), 0, wx.EXPAND)])
#        self.sizer.Add(sizer2, 0, wx.EXPAND+wx.TOP, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        # if sys.platform == 'win32':
        #     self.Hide()
        if counters['conges'] > self.conges_observer:
            self.AfficheCongesCreche()
        if self.salarie:
            for i in range(len(self.conges_salarie_sizer.GetChildren()), len(self.salarie.conges)):
                self.AddLine(i)
            for i in range(len(self.salarie.conges), len(self.conges_salarie_sizer.GetChildren())):
                self.RemoveLine()
        else:
            for i in range(len(self.conges_salarie_sizer.GetChildren())):
                self.RemoveLine()
        self.sizer.Layout()
        self.sizer.FitInside(self)
        AutoTab.UpdateContents(self)
        # if sys.platform == 'win32':
        #     self.Show()
        
    def SetSalarie(self, salarie):
        self.salarie = salarie
        self.UpdateContents()
        SalariesTab.SetSalarie(self, salarie)
        self.nouveau_conge_button.Enable(self.salarie is not None and not config.readonly)

    def AfficheCongesCreche(self):
        self.conges_creche_sizer.DeleteWindows()
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            checkbox.Disable()
            if text in database.creche.feries:
                checkbox.SetValue(True)
            self.conges_creche_sizer.Add(checkbox, 0, wx.EXPAND)
        for conge in database.creche.conges:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'debut', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'fin', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, 'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, conge, 'label', fixed_instance=True)])
            for child in sizer.GetChildren():
                child.GetWindow().Disable()
            self.conges_creche_sizer.Add(sizer)
        self.conges_observer = counters['conges']

    def AddLine(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.salarie, 'conges[%d].debut' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.salarie, 'conges[%d].fin' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.salarie, 'conges[%d].label' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnCongeRemove, delbutton)
        self.conges_salarie_sizer.Add(sizer)
        
    def RemoveLine(self):
        index = len(self.conges_salarie_sizer.GetChildren()) - 1
        sizer = self.conges_salarie_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_salarie_sizer.Detach(index)

    def OnCongeAdd(self, _):
        history.Append(Delete(self.salarie.conges, -1))
        self.salarie.add_conge(CongeSalarie(salarie=self.salarie))
        self.AddLine(len(self.salarie.conges) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnCongeRemove(self, event):
        index = event.GetEventObject().index
        conge = self.salarie.conges[index]
        history.Append(Insert(self.salarie.conges, index, self.salarie.conges[index]))
        self.RemoveLine()
        self.salarie.delete_conge(conge)
        self.sizer.Layout()
        self.UpdateContents()


class WxSalariePlanningLine(BasePlanningLine, BaseWxPythonLine):
    # TODO merge this code into panel_inscriptions
    def __init__(self, planning, index, label):
        BasePlanningLine.__init__(self, label)
        self.planning = planning
        self.index = index
        self.day = planning.get_day_from_index(index)
        self.timeslots = self.day.timeslots

    def update(self):
        self.day = self.planning.get_day_from_index(self.index)
        self.timeslots = self.day.timeslots

    def add_timeslot(self, debut, fin, value):
        timeslot = TimeslotPlanningSalarie(day=self.index, debut=debut, fin=fin, value=value)
        self.planning.days.add(timeslot)
        self.update()

    def delete_timeslot(self, i, check=True):
        timeslot = self.timeslots[i]
        self.planning.days.remove(timeslot)
        self.update()

    def get_badge_text(self):
        heures_jour = 0
        heures_semaine = 0
        first_day = 7 * (self.index // 7)
        for index in range(first_day, first_day + 7):
            day = self.planning.get_day_from_index(index)
            heures = day.get_duration()
            if index == self.index:
                heures_jour += heures
            heures_semaine += heures
        return GetHeureString(heures_jour) + "/" + GetHeureString(heures_semaine)


class PlanningReferenceSalariePanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS | PRESENCES_ONLY | NO_SALARIES)
        
    def UpdateContents(self):
        lines = []
        if self.planning:
            for index in range(self.planning.duree_reference):
                if database.creche.is_jour_semaine_travaille(index):
                    lines.append(WxSalariePlanningLine(self.planning, index, days[index % 7]))
        self.SetLines(lines)

    def SetPlanning(self, planning):
        self.planning = planning
        self.UpdateContents()

    def GetSummaryDynamicText(self):
        return GetHeureString(self.planning.get_duration_per_week())


class ContratsSalariePanel(SalariesTab, PeriodeMixin):
    def __init__(self, parent):
        SalariesTab.__init__(self, parent)
        PeriodeMixin.__init__(self, "contrats")
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ligne_sizer.Add(PeriodeChoice(self, self.nouveauContrat, onModify=self.onPeriodeModification))
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        sizer1 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer1.AddGrowableCol(1, 1)

        self.sites_items = wx.StaticText(self, -1, "Site :"), AutoChoiceCtrl(self, None, "site")
        self.UpdateSiteItems()
        sizer1.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])

        sizer1.AddMany([(wx.StaticText(self, -1, "Fonction :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, "fonction"), 0, wx.EXPAND)])
        sizer.Add(sizer1, 0, wx.ALL | wx.EXPAND, 5)

        self.plannings_panel = PeriodePanel(self, "plannings")
        self.plannings_panel.SetPeriode = self.SetPlanningPeriode
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self.plannings_panel, -1, "Plannings"), wx.VERTICAL)
        box_sizer.Add(PeriodeChoice(self.plannings_panel, self.nouveauPlanning))  # , onModify=self.onPlanningModification
        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.duree_reference_choice = ChoiceWithoutScroll(self.plannings_panel)
        for item, data in [("1 semaine", 7)] + [("%d semaines" % (i+2), 7*(i+2)) for i in range(MAX_SEMAINES_REFERENCE-1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.onDureeReferenceChoice, self.duree_reference_choice)
        line_sizer.AddMany([(wx.StaticText(self.plannings_panel, -1, "Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5), (self.duree_reference_choice, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALL, 5)])
        self.button_copy = wx.Button(self.plannings_panel, -1, "Recopier lundi sur toute la période")
        line_sizer.Add(self.button_copy, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND | wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.onMondayCopy, self.button_copy)

        self.activity_choice = ActivityComboBox(self.plannings_panel)
        line_sizer.Add(self.activity_choice, 1, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL, 5)

        self.planning_panel = PlanningReferenceSalariePanel(self.plannings_panel, self.activity_choice)
        box_sizer.Add(line_sizer, 0, wx.EXPAND)
        box_sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.plannings_panel.SetSizer(box_sizer)

        sizer.Add(self.plannings_panel, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.UpdateContents()

    def SetPlanningPeriode(self, periode):
        self.plannings_panel.SetInstance(self.plannings_panel.instance, periode)
        self.UpdatePlanningPanel()

    def nouveauPlanning(self):
        contrat = self.salarie.contrats[self.periode]
        planning = PlanningSalarie(contrat=contrat, debut=datetime.date.today())
        contrat.plannings.append(planning)
        return planning

    def onPeriodeModification(self):
        contrat = self.salarie.contrats[self.periode]
        if database.creche.gestion_plannings_salaries == GESTION_SIMPLE_PLANNINGS_SALARIES:
            contrat.plannings[0].debut = contrat.debut
            contrat.plannings[0].fin = contrat.fin

    def nouveauContrat(self):
        contrat = ContratSalarie(salarie=self.salarie, debut=datetime.date.today())
        if self.salarie.creche.gestion_plannings_salaries == GESTION_SIMPLE_PLANNINGS_SALARIES:
            planning = PlanningSalarie(contrat=contrat)
            contrat.plannings.append(planning)
        return contrat

    def SetSalarie(self, salarie):
        self.salarie = salarie
        self.SetInstance(salarie)
        self.UpdateContents()

    def onDureeReferenceChoice(self, _):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.salarie.contrats[self.periode].plannings[self.plannings_panel.periode].duree_reference = duration
        self.UpdateContents()

    def onMondayCopy(self, _):
        history.Append(None)
        for line in self.planning_panel.lines[1:]:
            for i in range(len(line.timeslots)):
                line.delete_timeslot(0)
            for timeslot in self.planning_panel.lines[0].timeslots:
                line.add_timeslot(timeslot.debut, timeslot.fin, timeslot.value)
        self.UpdateContents()

    def UpdateSiteItems(self):
        if len(database.creche.sites) > 1:
            items = [(site.nom, site) for site in database.creche.sites]
            self.sites_items[1].SetItems(items)
        else:
            for item in self.sites_items:
                item.Show(False)
        self.sites_observer = counters['sites']

    def UpdateContents(self):
        if counters['sites'] > self.sites_observer:
            self.UpdateSiteItems()

        SalariesTab.UpdateContents(self)

        self.UpdateContratPanel()
        self.activity_choice.Clear()
        selected = 0
        if database.creche.has_activites_avec_horaires():
            self.activity_choice.Show(True)
            for i, activity in enumerate(database.creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                try:
                    if self.activity_choice.activity.value == activity.value:
                        selected = i
                except:
                    pass
        else:
            self.activity_choice.Show(False)
            self.activity_choice.Append(database.creche.activites[0].label, database.creche.activites[0])
        self.activity_choice.SetSelection(selected)

        enabled = (database.creche.gestion_plannings_salaries == GESTION_SIMPLE_PLANNINGS_SALARIES)
        self.activity_choice.Show(enabled)
        self.button_copy.Show(enabled)
        self.duree_reference_choice.Enable(enabled)
        self.plannings_panel.periodechoice.set_readonly(not enabled)
        if not enabled:
            self.planning_panel.options |= READ_ONLY
        else:
            self.planning_panel.options &= ~READ_ONLY

        self.Layout()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        self.UpdateContratPanel()

    def UpdateContratPanel(self):
        if self.salarie and self.periode is not None and self.periode != -1 and self.periode < len(self.salarie.contrats):
            contrat = self.salarie.contrats[self.periode]
            PeriodeMixin.SetPeriode(self, self.periode)
            self.plannings_panel.periode = min(self.plannings_panel.periode, len(contrat.plannings) - 1)
            self.UpdatePlanningPanel()
        else:
            self.planning_panel.SetPlanning(None)
            for obj in [self.duree_reference_choice, self.button_copy]:
                obj.Disable()

    def UpdatePlanningPanel(self):
        contrat = self.salarie.contrats[self.periode]
        planning = contrat.plannings[self.plannings_panel.periode]
        self.duree_reference_choice.Enable(not config.readonly and database.creche.gestion_plannings_salaries == GESTION_SIMPLE_PLANNINGS_SALARIES)
        self.button_copy.Enable(not config.readonly)
        if len(database.creche.sites) > 1:
            for item in self.sites_items:
                item.Show(True)
        self.duree_reference_choice.SetSelection(planning.duree_reference // 7 - 1)
        self.planning_panel.SetPlanning(planning)


class PlanningEquipeInternalPanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS | PRESENCES_ONLY | NO_SALARIES)
        self.index = 0
        self.plannings = []

    def UpdateContents(self):
        lines = []
        if database.creche.is_jour_semaine_travaille(self.index % 7):
            for planning in self.plannings:
                lines.append(WxSalariePlanningLine(planning, self.index, GetPrenomNom(planning.contrat.salarie)))
        self.SetLines(lines)

    def SetPlannings(self, plannings, index):
        self.plannings = plannings
        self.index = index
        self.UpdateContents()

    def GetSummaryDynamicText(self):
        return ""
        # return GetHeureString(self.planning.get_duration_per_week())


class Periode(object):
    def __init__(self, debut, fin):
        self.debut = debut
        self.fin = fin


class SpecialPeriodChoice(PeriodeChoice):
    def Enable(self, enable=True):
        self.periodechoice.Enable(enable and len(self.instance) > 0)
        self.periodesettingsbutton.Show(False)
        self.periodeaddbutton.Enable(enable and self.instance is not None and not config.readonly)
        self.periodedelbutton.Enable(enable and self.instance is not None and len(self.instance) > 0 and not config.readonly)

    def EvtPeriodeAddButton(self, _):
        periode = Periode(datetime.date.today(), None)
        dlg = PeriodeDialog(self.parent, periode)
        response = dlg.ShowModal()
        dlg.Destroy()
        if response == wx.ID_OK:
            periode.debut = dlg.debut_ctrl.GetValue()
            self.parent.add_periode(periode)

    def EvtPeriodeDelButton(self, evt):
        dlg = wx.MessageDialog(self.parent,
                               u'Cette période va être supprimée, confirmer ?',
                               'Confirmation',
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_YES:
            index = self.periodechoice.GetSelection()
            periode = self.instance[index]
            self.parent.delPeriode(periode)


class PlanningsEquipePanel(wx.lib.scrolledpanel.ScrolledPanel, PeriodeMixin):
    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        PeriodeMixin.__init__(self, 'plannings')
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.periodechoice = SpecialPeriodChoice(self, None)
        ligne_sizer.Add(self.periodechoice)
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        sizer1 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer1.AddGrowableCol(1, 1)
        sizer.Add(sizer1, 0, wx.ALL | wx.EXPAND, 5)

        self.duree_reference_choice = ChoiceWithoutScroll(self)
        for item, data in [("1 semaine", 7)] + \
                          [("%d semaines" % (i + 2), 7 * (i + 2)) for i in range(MAX_SEMAINES_REFERENCE - 1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.onDureeReferenceChoice, self.duree_reference_choice)
        sizer1.AddMany([
            (wx.StaticText(self, -1, "Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.duree_reference_choice, 0, wx.EXPAND)
        ])

        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.semaine_choice = ChoiceWithoutScroll(self)
        self.Bind(wx.EVT_CHOICE, self.onSemaineChoice, self.semaine_choice)
        line_sizer.AddMany([
            (wx.StaticText(self, -1, "Choix de la semaine :"), 0, wx.ALIGN_CENTER_VERTICAL),
            (self.semaine_choice, 0, wx.EXPAND | wx.ALL, 5)
        ])

        self.activity_choice = ActivityComboBox(self)
        line_sizer.Add(self.activity_choice, 0, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL, 5)
        sizer.Add(line_sizer, 0, wx.EXPAND)

        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        for weekday in range(7):
            if database.creche.is_jour_semaine_travaille(weekday):
                planning_panel = PlanningEquipeInternalPanel(self.notebook, self.activity_choice)
                self.notebook.AddPage(planning_panel, days[weekday])
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnChangementJour, self.notebook)

        self.salarie = None
        self.semaine = None
        self.plannings = {}
        self.periodes = []

        self.SetSizer(sizer)
        self.UpdateContents()

    def OnChangementJour(self, _):
        self.notebook.GetCurrentPage().UpdateContents()

    def SetSalarie(self, salarie):
        self.salarie = salarie

    def add_periode(self, periode):
        history.append(None)
        for salarie in database.creche.salaries:
            for contrat in salarie.contrats:
                if periode.debut >= contrat.debut and (not contrat.fin or periode.debut <= contrat.fin):
                    planning = self.get_salarie_planning(salarie, periode.debut)
                    if not planning and periode.debut not in self.plannings:
                        previous = self.get_salarie_previous_planning(salarie, periode.debut)
                        planning = self.get_planning_copy(contrat, previous)
                        planning.debut = periode.debut
                        contrat.plannings.append(planning)
        self.update_periodes()

    def delPeriode(self, periode):
        history.append(None)
        for salarie in database.creche.salaries:
            planning = self.get_salarie_planning(salarie, periode.debut)
            if planning:
                planning.contrat.plannings.remove(planning)
        self.update_periodes()

    def onDureeReferenceChoice(self, _):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        for planning in self.get_plannings():
            planning.duree_reference = duration
        self.UpdateDureePeriodeReference()
        self.UpdateTabs()

    def onSemaineChoice(self, _):
        self.semaine = self.semaine_choice.GetClientData(self.semaine_choice.GetSelection())
        self.UpdateTabs()

    def UpdateActivityChoice(self):
        self.activity_choice.Clear()
        selected = 0
        if database.creche.has_activites_avec_horaires():
            self.activity_choice.Show(True)
            for i, activity in enumerate(database.creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                try:
                    if self.activity_choice.activity.value == activity.value:
                        selected = i
                except:
                    pass
        else:
            self.activity_choice.Show(False)
            self.activity_choice.Append(database.creche.activites[0].label, database.creche.activites[0])
        self.activity_choice.SetSelection(selected)

    @staticmethod
    def get_salarie_planning(salarie, date):
        for contrat in salarie.contrats:
            for planning in contrat.plannings:
                if planning.debut == date:
                    return planning
        return None

    @staticmethod
    def get_salarie_previous_planning(salarie, date):
        result = None
        for contrat in salarie.contrats:
            for planning in contrat.plannings:
                if (not planning.debut or planning.debut < date) and (not result or not result.debut or (planning.debut and planning.debut > result.debut)):
                    result = planning
        return result

    @staticmethod
    def get_planning_copy(contrat, planning):
        if planning:
            clone = PlanningSalarie(contrat=contrat, duree_reference=planning.duree_reference)
            for timeslot in planning.days:
                clone.days.add(TimeslotPlanningSalarie(day=timeslot.day, debut=timeslot.debut, fin=timeslot.fin, value=timeslot.value))
        else:
            clone = PlanningSalarie(contrat=contrat, duree_reference=7)
        return clone

    def add_planning(self, date, planning):
        if date not in self.plannings:
            self.plannings[date] = []
        if planning:
            self.plannings[date].append(planning)

    def update_periodes(self):
        dates = set()
        for salarie in database.creche.salaries:
            for contrat in salarie.contrats:
                if contrat.debut:
                    dates.add(contrat.debut)
                    if contrat.fin:
                        dates.add(contrat.fin + datetime.timedelta(1))
                    for planning in contrat.plannings[:]:
                        if contrat.fin and planning.debut and planning.debut > contrat.fin:
                            contrat.plannings.remove(planning)
                        elif planning.debut:
                            dates.add(planning.debut)
        dates = list(dates)
        dates.sort()
        self.periodes = []
        for i, date in enumerate(dates):
            self.periodes.append(Periode(date, (dates[i+1] - datetime.timedelta(1)) if (i < len(dates) - 1) else None))
        self.plannings = {}
        for date in dates:
            self.plannings[date] = []
        for salarie in database.creche.salaries:
            for contrat in salarie.contrats:
                for date in dates:
                    if (contrat.debut and date >= contrat.debut) and (not contrat.fin or date <= contrat.fin):
                        planning = self.get_salarie_planning(salarie, date)
                        if not planning:
                            previous = self.get_salarie_previous_planning(salarie, date)
                            planning = self.get_planning_copy(contrat, previous)
                            planning.contrat = contrat
                            planning.debut = date
                            contrat.plannings.append(planning)
                        self.plannings[date].append(planning)
        self.periode = 0
        self.periodechoice.SetInstance(self.periodes, self.periode)
        self.periodechoice.Enable(len(self.plannings) > 0)

    def get_plannings(self):
        if not self.plannings:
            return self.plannings
        periode = self.periodes[self.periode]
        return self.plannings[periode.debut]

    def UpdateDureePeriodeReference(self):
        plannings = self.get_plannings()
        if len(plannings) > 0:
            planning = self.get_plannings()[0]
            semaines_count = planning.duree_reference // 7
        else:
            semaines_count = 1
        self.duree_reference_choice.Enable(len(plannings) > 0)
        self.duree_reference_choice.SetSelection(semaines_count - 1)
        self.semaine_choice.Clear()
        for item, data in [("Semaine %d" % (i + 1), i) for i in range(semaines_count)]:
            self.semaine_choice.Append(item, data)
        self.semaine = 0
        self.semaine_choice.Enable(len(plannings) > 0)
        self.semaine_choice.SetSelection(0)

    def UpdateTabs(self):
        plannings = self.get_plannings()
        for page in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(page).SetPlannings(plannings, self.semaine * 7 + page)

    def UpdateContents(self):
        if database.creche.gestion_plannings_salaries == GESTION_GLOBALE_PLANNINGS_SALARIES:
            self.UpdateActivityChoice()
            self.update_periodes()
            self.UpdateDureePeriodeReference()
            self.UpdateTabs()
            self.Layout()
        else:
            self.Hide()

    def SetPeriode(self, periode):
        self.periode = periode
        self.UpdateDureePeriodeReference()
        self.UpdateTabs()

    
class SalariesNotebook(wx.Notebook):
    def __init__(self, parent, *args, **kwargs):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT, *args, **kwargs)      
        self.parent = parent
        self.salarie = None

        self.AddPage(IdentiteSalariePanel(self), "Identité")
        self.AddPage(CongesPanel(self), "Congés")
        if database.creche.gestion_plannings_salaries == GESTION_SIMPLE_PLANNINGS_SALARIES:
            self.AddPage(ContratsSalariePanel(self), "Plannings de référence")
        else:
            self.AddPage(ContratsSalariePanel(self), "Contrats")
            self.AddPage(PlanningsEquipePanel(self), "Plannings de référence de l'équipe")

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged, self)
            
    def EvtChangementPrenomNom(self, _):
        self.parent.ChangePrenomNom(self.salarie)

    def onPageChanged(self, event):
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def SetSalarie(self, salarie):
        self.salarie = salarie
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetSalarie(salarie)
            
    def UpdateContents(self):
        self.GetCurrentPage().UpdateContents()


class SalariesPanel(GPanel):
    name = "Salariés"
    bitmap = GetBitmapFile("salaries.png")
    profil = PROFIL_SALARIES

    def __init__(self, parent):
        GPanel.__init__(self, parent, "Salariés")

        # Le control pour la selection du bebe
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtSalarieChoice, self.choice)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp)
        self.delbutton = wx.BitmapButton(self, -1, delbmp)
        self.addbutton.SetToolTipString("Ajouter un salarié")
        self.delbutton.SetToolTipString("Retirer ce salarié")
        self.Bind(wx.EVT_BUTTON, self.EvtSalarieAddButton, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtSalarieDelButton, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (self.addbutton, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (self.delbutton, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND | wx.LEFT, MACOS_MARGIN)
        # le notebook pour la fiche d'contrat
        self.notebook = SalariesNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.TOP, 5)
        self.InitSalaries()

    def UpdateContents(self):
        self.notebook.UpdateContents()

    def InitSalaries(self, selected=None):
        self.choice.Clear()

        salaries = {}
        autres = {}
        for salarie in database.creche.salaries:
            if salarie.get_contrat(datetime.date.today()):
                salaries[GetPrenomNom(salarie)] = salarie
            else:
                autres[GetPrenomNom(salarie)] = salarie
        
        keys = salaries.keys()
        keys.sort()
        for key in keys:
            self.choice.Append(key, salaries[key])
        
        if len(salaries) > 0 and len(autres) > 0:
            self.choice.Append("-" * 150, None)
        
        keys = autres.keys()
        keys.sort()
        for key in keys:
            self.choice.Append(key, autres[key])

        if len(database.creche.salaries) > 0 and selected and selected in database.creche.salaries:
            self.SelectSalarie(selected)
        elif len(database.creche.salaries) > 0:
            self.SelectSalarie(self.choice.GetClientData(0))
        else:
            self.SelectSalarie(None)

    def EvtSalarieChoice(self, evt):
        ctrl = evt.GetEventObject()
        selected = ctrl.GetSelection()
        salarie = ctrl.GetClientData(selected)
        if salarie:
            self.delbutton.Enable()
            self.notebook.SetSalarie(salarie)
        else:
            ctrl.SetSelection(0)
            self.EvtSalarieChoice(evt)

    def SelectSalarie(self, salarie):
        if salarie:
            for i in range(self.choice.GetCount()):
                if self.choice.GetClientData(i) == salarie:
                    self.choice.SetSelection(i)
                    break
        else:
            self.choice.SetSelection(-1)
        self.notebook.SetSalarie(salarie)

    def EvtSalarieAddButton(self, _):
        history.Append(Delete(database.creche.salaries, -1))
        salarie = Salarie(creche=database.creche)
        self.choice.Insert("Nouveau salarié", 0, salarie)
        self.choice.SetSelection(0)
        database.creche.salaries.append(salarie)
        self.notebook.SetSalarie(salarie)
        self.notebook.SetSelection(0)  # Sélectionne la page identite

    def EvtSalarieDelButton(self, _):
        selected = self.choice.GetSelection()
        salarie = self.choice.GetClientData(selected)
        if salarie:
            dlg = wx.MessageDialog(self,
                                   'Les données de ce salarié vont être supprimées, êtes-vous sûr de vouloir continuer ?',
                                   'Confirmation',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_YES:
                index = database.creche.salaries.index(salarie)
                history.Append(Insert(database.creche.salaries, index, salarie))
                del database.creche.salaries[index]
                self.choice.Delete(selected)
                self.choice.SetSelection(-1)
                self.notebook.SetSalarie(None)
                self.delbutton.Disable()
            dlg.Destroy()
        
    def ChangePrenomNom(self, salarie):
        if database.creche and salarie:
            label = GetPrenomNom(salarie)
            if label.isspace():
                label = "Nouveau salarié"
            selection = self.choice.GetSelection()
            self.choice.SetString(selection, label)
            self.choice.SetSelection(selection)
