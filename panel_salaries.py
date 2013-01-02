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

import os, datetime, time, xml.dom.minidom, cStringIO
import wx, wx.lib.scrolledpanel, wx.html
from constants import *
from sqlobjects import *
from controls import *
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
        sizer2.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (prenom_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (nom_ctrl, 0, wx.EXPAND)])
        for label, field in (u"Téléphone domicile", "telephone_domicile"), (u"Téléphone portable", "telephone_portable"):
            sizer3 = wx.BoxSizer(wx.HORIZONTAL)
            sizer3.AddMany([(AutoPhoneCtrl(self, None, field), 0), (AutoTextCtrl(self, None, field+'_notes'), 1, wx.LEFT|wx.EXPAND, 5)])
            sizer2.AddMany([(wx.StaticText(self, -1, label+' :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'E-mail :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'email'), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, u"Diplômes :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoComboBox(self, None, 'diplomes', choices=["CAP petite enfance", u"Auxiliaire puéricultrice", "EJE", u"Puéricultrice", "Sans objet"]), 0, wx.EXPAND)])
        self.sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
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
            for salarie in creche.salaries:
                if salarie.code_postal == code_postal and salarie.ville:
                    self.ville_ctrl.SetValue(salarie.ville)
                    break
        
    def UpdateContents(self):
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        
    def SetSalarie(self, salarie):
        self.salarie = salarie
        self.UpdateContents()
        SalariesTab.SetSalarie(self, salarie)

class CongesPanel(SalariesTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.last_creche_observer = -1
        
        SalariesTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.conges_creche_sizer = wx.BoxSizer(wx.VERTICAL)
        self.affiche_conges_creche()
        self.sizer.Add(self.conges_creche_sizer, 0, wx.ALL, 5)
        
        self.conges_salarie_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.conges_salarie_sizer, 0, wx.ALL, 5)
        
        self.nouveau_conge_button = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(self.nouveau_conge_button, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.evt_conge_add, self.nouveau_conge_button)

#        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.AddMany([(wx.StaticText(self, -1, u'Nombre de semaines de congés déduites :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'semaines_conges', min=0, precision=0), 0, wx.EXPAND)])
#        self.sizer.Add(sizer2, 0, wx.EXPAND+wx.TOP, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        if 'conges' in observers and observers['conges'] > self.last_creche_observer:
            self.affiche_conges_creche()
        if self.salarie:
            for i in range(len(self.conges_salarie_sizer.GetChildren()), len(self.salarie.conges)):
                self.line_add(i)
            for i in range(len(self.salarie.conges), len(self.conges_salarie_sizer.GetChildren())):
                self.line_del()
        else:
            for i in range(len(self.conges_salarie_sizer.GetChildren())):
                self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)
        
    def SetSalarie(self, salarie):
        self.salarie = salarie
        self.UpdateContents()
        SalariesTab.SetSalarie(self, salarie)
        self.nouveau_conge_button.Enable(self.salarie is not None and not readonly)

    def affiche_conges_creche(self):
        self.conges_creche_sizer.DeleteWindows()
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            checkbox.Disable()
            if text in creche.feries:
                checkbox.SetValue(True)
            self.conges_creche_sizer.Add(checkbox, 0, wx.EXPAND)
        for conge in creche.conges:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'debut', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'fin', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, conge, 'label', fixed_instance=True)])
            for child in sizer.GetChildren():
                child.GetWindow().Disable()
            self.conges_creche_sizer.Add(sizer)
        self.last_creche_observer = time.time()

    def line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.salarie, 'conges[%d].debut' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.salarie, 'conges[%d].fin' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.salarie, 'conges[%d].label' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.evt_conge_del, delbutton)
        self.conges_salarie_sizer.Add(sizer)
        
    def line_del(self):
        index = len(self.conges_salarie_sizer.GetChildren()) - 1
        sizer = self.conges_salarie_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_salarie_sizer.Detach(index)

    def evt_conge_add(self, event):
        history.Append(Delete(self.salarie.conges, -1))
        self.salarie.add_conge(CongeSalarie(self.salarie))
        self.line_add(len(self.salarie.conges) - 1)
        self.sizer.Layout()

    def evt_conge_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.salarie.conges, index, self.salarie.conges[index]))
        self.line_del()
        conge = self.salarie.conges[index]
        del self.salarie.conges[index]
        conge.delete()
        self.sizer.Layout()
        self.UpdateContents()

class PlanningReferenceSalariePanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS|PRESENCES_ONLY)
        
    def UpdateContents(self):
        lines = []
        if self.contrat:
            for day in range(self.contrat.duree_reference):
                if JourSemaineAffichable(day):
                    line = self.contrat.reference[day]
                    line.insert = None
                    line.label = days[day % 7]
                    line.reference = None
                    line.summary = True
                    lines.append(line)
        self.SetLines(lines)

    def SetContrat(self, contrat):
        self.contrat = contrat
        self.UpdateContents()
        
class ContratsSalariePanel(SalariesTab, PeriodeMixin):
    def __init__(self, parent):
        SalariesTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'contrats')
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ligne_sizer.Add(PeriodeChoice(self, self.nouveauContrat))
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        sizer1 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer1.AddGrowableCol(1, 1)
        
        self.sites_items = wx.StaticText(self, -1, u"Site :"), AutoChoiceCtrl(self, None, 'site'), wx.StaticText(self, -1, u"Sites de préinscription :"), wx.CheckListBox(self, -1)
        self.UpdateSiteItems()
        sizer1.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])
        sizer1.AddMany([(self.sites_items[2], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[3], 0, wx.EXPAND)])
                        
        sizer1.AddMany([(wx.StaticText(self, -1, u"Fonction :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'fonction'), 0, wx.EXPAND)])
        
        self.duree_reference_choice = wx.Choice(self)
        for item, data in [("1 semaine", 7)] + [("%d semaines" % (i+2), 7*(i+2)) for i in range(MAX_SEMAINES_REFERENCE-1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.onDureeReferenceChoice, self.duree_reference_choice)
        sizer1.AddMany([(wx.StaticText(self, -1, u"Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.duree_reference_choice, 0, wx.EXPAND)])
        sizer.Add(sizer1, 0, wx.ALL|wx.EXPAND, 5)
       
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.button_copy = wx.Button(self, -1, u"Recopier lundi sur toute la période")
        sizer2.Add(self.button_copy)
        self.Bind(wx.EVT_BUTTON, self.onMondayCopy, self.button_copy)
        
        self.activity_choice = ActivityComboBox(self)        
        sizer2.Add(self.activity_choice, 0, wx.ALIGN_RIGHT)
        sizer.Add(sizer2, 0, wx.EXPAND)
        
        self.planning_panel = PlanningReferenceSalariePanel(self, self.activity_choice)
        sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.UpdateContents()
        
    def nouveauContrat(self): # TODO les autres pareil ...
        contrat = Contrat(self.salarie)
        return contrat

    def SetSalarie(self, salarie):
        self.salarie = salarie
        self.SetInstance(salarie)
        self.UpdateContents()
           
    def onDureeReferenceChoice(self, event):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.salarie.contrats[self.periode].setReferenceDuration(duration)
        self.UpdateContents()
        
    def onMode_5_5(self, event):
        history.Append(None)
        contrat = self.salarie.contrats[self.periode]
        contrat.mode = MODE_5_5
        for i, day in enumerate(contrat.reference):
            if JourSemaineAffichable(i):
                day.set_state(0)
        self.UpdateContents()
    
    def onMondayCopy(self, event):
        history.Append(None)
        contrat = self.salarie.contrats[self.periode]
        for i, day in enumerate(contrat.reference):
            if i > 0 and JourSemaineAffichable(i):
                day.Copy(contrat.reference[0], False)
                day.Save()
        self.UpdateContents()
    
    def UpdateSiteItems(self):
        if len(creche.sites) > 1:
            items = [(site.nom, site) for site in creche.sites]
            self.sites_items[1].SetItems(items)
            for nom, site in items:
                self.sites_items[3].Append(nom)
        else:
            for item in self.sites_items:
                item.Show(False)
        self.last_site_observer = time.time()

    def UpdateContents(self):
        if 'sites' in observers and observers['sites'] > self.last_site_observer:
            self.UpdateSiteItems()

        SalariesTab.UpdateContents(self)

        self.InternalUpdate()
            
        self.activity_choice.Clear()
        selected = 0
        if creche.HasActivitesAvecHoraires():
            self.activity_choice.Show(True)
            for i, activity in enumerate(creche.activites.values()):
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
                                    
        self.Layout()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        self.InternalUpdate()
    
    def InternalUpdate(self):
        if self.salarie and self.periode is not None and self.periode != -1 and self.periode < len(self.salarie.contrats):
            contrat = self.salarie.contrats[self.periode]
            for obj in [self.duree_reference_choice, self.button_copy]:
                obj.Enable(not readonly)
            if len(creche.sites) > 1:
                for item in self.sites_items[0:2]:
                    item.Show(True)
                for item in self.sites_items[2:4]:
                    item.Show(False)
                    
            self.duree_reference_choice.SetSelection(contrat.duree_reference / 7 - 1)
            self.planning_panel.SetContrat(contrat)
        else:
            self.planning_panel.SetContrat(None)
            for obj in [self.duree_reference_choice, self.button_copy]:
                obj.Disable()

class SalariesNotebook(wx.Notebook):
    def __init__(self, parent, *args, **kwargs):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT, *args, **kwargs)      
        self.parent = parent
        self.salarie = None

        self.AddPage(IdentiteSalariePanel(self), u'Identité')
        self.AddPage(CongesPanel(self), u"Congés")
        self.AddPage(ContratsSalariePanel(self), u"Plannings de référence")

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)  
            
    def EvtChangementPrenomNom(self, event):
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
    bitmap = GetBitmapFile("salaries.png")
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u"Salariés")

        # Le control pour la selection du bebe
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtSalarieChoice, self.choice)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp, style=wx.BU_EXACTFIT)
        self.delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.BU_EXACTFIT)
        self.addbutton.SetToolTipString(u"Ajouter un salarié")
        self.delbutton.SetToolTipString(u"Retirer ce salarié")
        self.Bind(wx.EVT_BUTTON, self.EvtSalarieAddButton, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtSalarieDelButton, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.addbutton, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.delbutton, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND)
        # le notebook pour la fiche d'contrat
        self.notebook = SalariesNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        self.InitSalaries()

    def UpdateContents(self):
        self.notebook.UpdateContents()

    def InitSalaries(self, selected=None):
        self.choice.Clear()

        salaries = { }
        autres = { }
        for salarie in creche.salaries:
            if salarie.GetContrat(datetime.date.today()) != None:
                salaries[GetPrenomNom(salarie)] = salarie
            else:
                autres[GetPrenomNom(salarie)] = salarie
        
        keys = salaries.keys()
        keys.sort()
        for key in keys:
            self.choice.Append(key, salaries[key])
        
        if len(salaries) > 0 and len(autres) > 0:
            self.choice.Append(150 * '-', None)
        
        keys = autres.keys()
        keys.sort()
        for key in keys:
            self.choice.Append(key, autres[key])

        if len(creche.salaries) > 0 and selected != None and selected in creche.salaries:
            self.SelectSalarie(selected)
        elif len(creche.salaries) > 0:
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

    def EvtSalarieAddButton(self, evt):
        history.Append(Delete(creche.salaries, -1))
        salarie = Salarie()
        self.choice.Insert(u'Nouveau salarié', 0, salarie)
        self.choice.SetSelection(0)
        creche.salaries.append(salarie)
        self.notebook.SetSalarie(salarie)
        self.notebook.SetSelection(0) # Selectionne la page identite

    def EvtSalarieDelButton(self, evt):
        selected = self.choice.GetSelection()
        salarie = self.choice.GetClientData(selected)
        if salarie:
            dlg = wx.MessageDialog(self,
                                   u'Les données de ce salarié vont être supprimées, êtes-vous sûr de vouloir continuer ?',
                                   'Confirmation',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION )
            if dlg.ShowModal() == wx.ID_YES:
                index = creche.salaries.index(salarie)
                history.Append(Insert(creche.salaries, index, salarie))
                salarie.delete()
                del creche.salaries[index]
                self.choice.Delete(selected)
                self.choice.SetSelection(-1)
                self.notebook.SetSalarie(None)
                self.delbutton.Disable()
            dlg.Destroy()
        
    def ChangePrenomNom(self, salarie):
        if creche and salarie:
            id = GetPrenomNom(salarie)
            if id.isspace():
                id = u'Nouveau salarié'
            selection = self.choice.GetSelection()
            self.choice.SetString(selection, id)
            self.choice.SetSelection(selection)
                                