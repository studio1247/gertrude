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

import os.path
import datetime
from constants import *
from controls import *
from sqlobjects import *

types_creche = [("Parental", TYPE_PARENTAL),
                ("Associatif", TYPE_ASSOCIATIF),
                ("Municipal", TYPE_MUNICIPAL)]

class CrecheTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        sizer2.AddMany([wx.StaticText(self, -1, u'Nom de la crèche :'), (AutoTextCtrl(self, creche, 'nom'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Adresse :'), (AutoTextCtrl(self, creche, 'adresse'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Code Postal :'), (AutoNumericCtrl(self, creche, 'code_postal', precision=0), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Ville :'), (AutoTextCtrl(self, creche, 'ville'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, u'Téléphone :'), (AutoPhoneCtrl(self, creche, 'telephone'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'E-mail :'), (AutoTextCtrl(self, creche, 'email'), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Type :'), (AutoChoiceCtrl(self, creche, 'type', items=types_creche), 0, wx.EXPAND)])
        sizer2.AddMany([wx.StaticText(self, -1, u'Capacité :'), (AutoNumericCtrl(self, creche, 'capacite', precision=0), 0, wx.EXPAND)])
        sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

class EmployesTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.employes_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, employe in enumerate(creche.employes):
            self.line_add(i)
        self.sizer.Add(self.employes_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvel employé')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.employe_add, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.employes_sizer.GetChildren()), len(creche.employes)):
            self.line_add(i)
        for i in range(len(creche.employes), len(self.employes_sizer.GetChildren())):
            self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'employes[%d].prenom' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'employes[%d].nom' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Arrivée :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, creche, 'employes[%d].date_embauche' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Domicile :"), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, creche, 'employes[%d].telephone_domicile' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Portable :"), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, creche, 'employes[%d].telephone_portable' % index), 1, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.employe_del, delbutton)
        self.employes_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def line_del(self):
        index = len(self.employes_sizer.GetChildren()) - 1
        sizer = self.employes_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.employes_sizer.Detach(index)

    def employe_add(self, event):
        history.Append(Delete(creche.employes, -1))
        creche.employes.append(Employe())
        self.line_add(len(creche.employes) - 1)
        self.sizer.Layout()

    def employe_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(creche.employes, index, creche.employes[index]))
        self.line_del()
        creche.employes[index].delete()
        del creche.employes[index]
        self.sizer.Layout()
        self.UpdateContents()

class ResponsabilitesTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'bureaux')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, Bureau), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        self.responsables_ctrls = []
        self.responsables_ctrls.append(AutoChoiceCtrl(self, None, 'president'))
        sizer2.AddMany([wx.StaticText(self, -1, u'Président :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, None, 'vice_president'))
        sizer2.AddMany([wx.StaticText(self, -1, u'Vice président :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, None, 'tresorier'))
        sizer2.AddMany([wx.StaticText(self, -1, u'Trésorier :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        self.responsables_ctrls.append(AutoChoiceCtrl(self, None, 'secretaire'))        
        sizer2.AddMany([wx.StaticText(self, -1, u'Secrétaire :'), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
        sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(creche)

    def SetInstance(self, instance, periode=None):
        self.instance = instance
        if instance and len(instance.bureaux) > 0:
            if periode is None:
                current_periode = eval("self.instance.%s[-1]" % self.member)
            else:
                current_periode = eval("self.instance.%s[%d]" % (self.member, periode))
            parents = self.GetNomsParents(current_periode)
            for ctrl in self.responsables_ctrls:
                ctrl.SetItems(parents)
        PeriodeMixin.SetInstance(self, instance, periode)

    def GetNomsParents(self, periode):
        result = []
        parents = []
        for inscrit in getInscrits(periode.debut, periode.fin):
            for parent in (inscrit.papa, inscrit.maman):
                if parent.prenom and parent.nom:
                    tmp = parent.prenom + ' ' + parent.nom
                    if not tmp in parents:
                        parents.append(tmp)
                        result.append((tmp, parent))
        result.sort(cmp=lambda x,y: cmp(x[0].lower(), y[0].lower()))
        return result

activity_modes = [("Normal", 0),
                  (u"Libère une place", MODE_LIBERE_PLACE),
                 ]

class ActivitesTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.activites_sizer = wx.BoxSizer(wx.VERTICAL)
        for activity in creche.activites.values():
            self.line_add(activity)
        self.sizer.Add(self.activites_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle activité')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.activite_add, button_add)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def UpdateContents(self):
        self.activites_sizer.Clear(True)
        for activity in creche.activites.values():
            self.line_add(activity)
        self.sizer.Layout()

    def line_add(self, activity):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Label :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'activites[%d].label' % activity.value), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Mode :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoChoiceCtrl(self, creche, 'activites[%d].mode' % activity.value, items=activity_modes), 1, wx.EXPAND)])
        color_cb = ActivityComboBox(self)
        color_cb.reference = activity
        for color in range(1, 10):
            color_cb.Append("", color)
        if activity.color is not None:
            color_cb.SetSelection(activity.color-1)
        self.Bind(wx.EVT_COMBOBOX, self.changeColor, color_cb)
        sizer.AddMany([(wx.StaticText(self, -1, 'Couleur :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (color_cb, 1, wx.EXPAND)])
        
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = activity.value
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.activite_del, delbutton)
        self.activites_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def activite_add(self, event):
        activity = Activite()
        colors = [tmp.color for tmp in creche.activites.values()]
        for color in range(1, 10):
            if color not in colors:
                activity.color = color
                break
        creche.activites[activity.value] = activity
        history.Append(Delete(creche.activites, activity.value))
        self.line_add(activity)
        self.sizer.Layout()

    def activite_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(creche.activites, index, creche.activites[index]))
        for i, child in enumerate(self.activites_sizer.GetChildren()):
            sizer = child.GetSizer()
            if index == sizer.GetItem(6).GetWindow().index:
                sizer.DeleteWindows()
                self.activites_sizer.Detach(i)
        creche.activites[index].delete()
        del creche.activites[index]
        self.sizer.Layout()
        self.UpdateContents()

    def changeColor(self, event):
        obj = event.GetEventObject()
        obj.reference.color = obj.GetSelection() + 1

class CafTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'baremes_caf')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, BaremeCAF), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, 'Plancher :'), AutoNumericCtrl(self, None, 'plancher', precision=2)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Plafond :'), AutoNumericCtrl(self, None, 'plafond', precision=2)])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(creche)
        
class JoursFermeturePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            if text in creche.feries:
                checkbox.SetValue(True)
            self.sizer.Add(checkbox, 0, wx.EXPAND)
            self.Bind(wx.EVT_CHECKBOX, self.feries_check, checkbox)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(creche.conges):
            self.line_add(i)
        self.sizer.Add(self.conges_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(button_add, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.conges_add, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        for i in range(len(self.conges_sizer.GetChildren()), len(creche.conges)):
            self.line_add(i)
        for i in range(len(creche.conges), len(self.conges_sizer.GetChildren())):
            self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].debut' % index)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].fin' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.conges_del, delbutton)
        self.conges_sizer.Add(sizer)

    def line_del(self):
        index = len(self.conges_sizer.GetChildren()) - 1
        sizer = self.conges_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(index)

    def conges_add(self, event):
        history.Append(Delete(creche.conges, -1))
        creche.add_conge(Conge())
        self.line_add(len(creche.conges) - 1)
        self.sizer.Layout()

    def conges_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(creche.conges, index, creche.conges[index]))
        self.line_del()
        creche.conges[index].delete()
        del creche.conges[index]
        self.sizer.Layout()
        self.UpdateContents()

    def feries_check(self, event):
        label = event.GetEventObject().GetLabelText()
        if event.IsChecked():
            conge = Conge(creation=False)
            conge.debut = label
            conge.create()
            creche.add_conge(conge)
        else:
            conge = creche.feries[label]
            conge.delete()
            del creche.feries[label]
            creche.calcule_jours_fermeture()
        history.Append(None)

class ParametersPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.FlexGridSizer(0, 2, 5, 5)
        sizer.AddGrowableCol(1, 1)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(AutoChoiceCtrl(self, creche, 'ouverture', [('7h30', 7.5), ('7h45', 7.75), ('8h', 8), ('8h30', 8.5), ('9h', 9)]), 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'fermeture', [('18h', 18), ('18h30', 18.5), ('18h45', 18.75), ('19h', 19)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures d\'ouverture :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(AutoChoiceCtrl(self, creche, 'affichage_min', [('7h30', 7.5), ('7h45', 7.75), ('8h', 8), ('8h30', 8.5), ('9h', 9)]), 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'affichage_max', [('18h', 18), ('18h30', 18.5), ('18h45', 18.75), ('19h', 19)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures affichées sur le planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Granularité du planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'granularite', [('1/4 heure', 4), ('1/2 heure', 2), ('1 heure', 1)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nombre de mois payés :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'mois_payes', [('12 mois', 12), ('11 mois', 11)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences prévisionnelles :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'presences_previsionnelles', [(u'Géré', True), (u'Non géré', False)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Modes d'inscription :"), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'modes_inscription', [(u'Crèche à plein-temps uniquement', MODE_5_5), ('Tous modes', MODE_5_5+MODE_4_5+MODE_3_5+MODE_HALTE_GARDERIE)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Minimum de jours de maladie pour déduction :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'minimum_maladie', min=0, precision=0), 0, wx.EXPAND)])
        facturation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        facturation_sizer.Add(AutoCheckBox(self, creche, 'mode_facturation', u'PSU', FACTURATION_PSU), 0, wx.EXPAND|wx.RIGHT, 5)
        facturation_sizer.Add(AutoCheckBox(self, creche, 'mode_facturation', u'Déduction de jours pour maladie avec carence', DEDUCTION_MALADIE_AVEC_CARENCE), 0, wx.EXPAND)
        sizer.AddMany([(wx.StaticText(self, -1, u'Mode de facturation :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (facturation_sizer, 0, wx.EXPAND)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)

class CrecheNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(CrecheTab(self), u'Crèche')
        self.AddPage(EmployesTab(self), u'Employés')
        self.AddPage(ResponsabilitesTab(self), u'Responsabilités')
        self.AddPage(CafTab(self), 'C.A.F.')
        self.AddPage(JoursFermeturePanel(self), u'Congés')
        self.AddPage(ActivitesTab(self), u'Activités')
        self.AddPage(ParametersPanel(self), u'Paramètres')
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()

class CrechePanel(GPanel):
    bitmap = './bitmaps/creche.png'
    index = 50
    profil = PROFIL_BUREAU
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Crèche')
        self.notebook = CrecheNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()

panels = [CrechePanel]
