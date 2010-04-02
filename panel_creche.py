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
import wx

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
        self.color_buttons = {}
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Couleurs"), wx.VERTICAL)
        flex_sizer = wx.FlexGridSizer(0, 3, 3, 2)
        flex_sizer.AddGrowableCol(1, 1)
        for label, activite, field in ((u"présences", creche.activites[0], "couleur"), (u"présences supplémentaires", creche.activites[0], "couleur_supplement"), (u"présences prévisionnelles", creche.activites[0], "couleur_previsionnel"), (u"absences pour congés", creche.couleurs[VACANCES], "couleur"), (u"absences pour maladie", creche.couleurs[MALADE], "couleur")):
            color_button = wx.Button(self, -1, "", size=(20, 20))
            r, g, b, a, h = couleur = getattr(activite, field)
            color_button.SetBackgroundColour(wx.Color(r, g, b))
            self.Bind(wx.EVT_BUTTON, self.onColorButton, color_button)
            color_button.hash_cb = HashComboBox(self)
            color_button.activite = color_button.hash_cb.activite = activite
            color_button.field = color_button.hash_cb.field = [field]
            self.color_buttons[(activite.value, field)] = color_button
            self.UpdateHash(color_button.hash_cb, couleur)
            self.Bind(wx.EVT_COMBOBOX, self.onHashChange, color_button.hash_cb)
            flex_sizer.AddMany([(wx.StaticText(self, -1, u'Couleur des %s :' % label), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)])
        box_sizer.Add(flex_sizer, 0, wx.BOTTOM, 5)
        button = wx.Button(self, -1, u'Rétablir les couleurs par défaut')
        self.Bind(wx.EVT_BUTTON, self.couleursDefaut, button)
        box_sizer.Add(button, 0, wx.ALL, 5)
        self.sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)

        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Activités'), wx.VERTICAL)
        self.activites_sizer = wx.BoxSizer(wx.VERTICAL)
        for activity in creche.activites.values():
            if activity.value > 0:
                self.line_add(activity)
        box_sizer.Add(self.activites_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle activité')
        box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.activite_add, button_add)
        self.sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        self.UpdateContents()

    def UpdateContents(self):
        self.color_buttons[(0, "couleur_supplement")].Enable(creche.presences_supplementaires)
        self.color_buttons[(0, "couleur_supplement")].hash_cb.Enable(creche.presences_supplementaires)
        self.color_buttons[(0, "couleur_previsionnel")].Enable(creche.presences_previsionnelles)
        self.color_buttons[(0, "couleur_previsionnel")].hash_cb.Enable(creche.presences_previsionnelles)
        self.activites_sizer.Clear(True)
        for activity in creche.activites.values():
            if activity.value > 0:
                self.line_add(activity)
        self.sizer.Layout()
        
    def couleursDefaut(self, event):
        creche.activites[0].couleur = [5, 203, 28, 150, wx.SOLID]
        creche.activites[0].couleur_supplement = [5, 203, 28, 250, wx.SOLID]
        creche.activites[0].couleur_previsionnel = [5, 203, 28, 50, wx.SOLID]
        creche.couleurs[VACANCES].couleur = [0, 0, 255, 150, wx.SOLID]
        creche.couleurs[MALADE].couleur = [190, 35, 29, 150, wx.SOLID]
        for activite, field in [(creche.activites[0], "couleur"), (creche.activites[0], "couleur_supplement"), (creche.activites[0], "couleur_previsionnel")]:
            r, g, b, a, h = color = getattr(activite, field)
            self.color_buttons[(0, field)].SetBackgroundColour(wx.Color(r, g, b))
            self.UpdateHash(self.color_buttons[(0, field)].hash_cb, color)        

    def line_add(self, activity):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'activites[%d].label' % activity.value), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Mode :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoChoiceCtrl(self, creche, 'activites[%d].mode' % activity.value, items=activity_modes), 1, wx.EXPAND)])
        color_button = wx.Button(self, -1, "", size=(20, 20))
        r, g, b, a, h = activity.couleur
        color_button.SetBackgroundColour(wx.Color(r, g, b))
        self.Bind(wx.EVT_BUTTON, self.onColorButton, color_button)
        color_button.hash_cb = HashComboBox(self)
        color_button.activite = color_button.hash_cb.activite = activity
        color_button.field = color_button.hash_cb.field = ["couleur", "couleur_supplement", "couleur_previsionnel"]
        self.UpdateHash(color_button.hash_cb, activity.couleur)
        self.Bind(wx.EVT_COMBOBOX, self.onHashChange, color_button.hash_cb)
        sizer.AddMany([(wx.StaticText(self, -1, 'Couleur :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)])
        if creche.tarification_activites:
            sizer.AddMany([(wx.StaticText(self, -1, 'Tarif :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'activites[%d].tarif' % activity.value, precision=2), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = activity.value
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.activite_del, delbutton)
        self.activites_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def activite_add(self, event):
        activity = Activite()
        colors = [tmp.couleur for tmp in creche.activites.values()]
        for h in (wx.BDIAGONAL_HATCH, wx.CROSSDIAG_HATCH, wx.FDIAGONAL_HATCH, wx.CROSS_HATCH, wx.HORIZONTAL_HATCH, wx.VERTICAL_HATCH, wx.TRANSPARENT, wx.SOLID):
            for color in (wx.RED, wx.BLUE, wx.CYAN, wx.GREEN, wx.LIGHT_GREY):
                r, g, b = color.Get()
                if (r, g, b, 150, h) not in colors:
                    activity.couleur = (r, g, b, 150, h)
                    activity.couleur_supplement = (r, g, b, 250, h)
                    activity.couleur_previsionnel = (r, g, b, 50, h)
                    break
            if activity.couleur:
                break
        else:
            activity.couleur = 0, 0, 0, 150, wx.SOLID
            activity.couleur_supplement = 0, 0, 0, 250, wx.SOLID
            activity.couleur_previsionnel = 0, 0, 0, 50, wx.SOLID
        creche.activites[activity.value] = activity
        history.Append(Delete(creche.activites, activity.value))
        self.line_add(activity)
        self.sizer.Layout()

    def activite_del(self, event):
        index = event.GetEventObject().index
        entrees = []
        for inscrit in creche.inscrits:
            for date in inscrit.journees:
                journee = inscrit.journees[date]
                for start, end, activity in journee.activites:
                    if activity == index:
                        entrees.append((inscrit, date))
                        break
        if len(entrees) > 0:
            message = 'Cette activité est utilisée par :\n'
            for inscrit, date in entrees:
                message += '%s %s le %s, ' % (inscrit.prenom, inscrit.nom, getDateStr(date))
            message += '\nVoulez-vous vraiment la supprimer ?'
            dlg = wx.MessageDialog(self, message, 'Confirmation', wx.OK|wx.CANCEL|wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                return
        for inscrit, date in entrees:
            journee = inscrit.journees[date]
            journee.remove_all_activities(index)
        history.Append(Insert(creche.activites, index, creche.activites[index]))
        for i, child in enumerate(self.activites_sizer.GetChildren()):
            sizer = child.GetSizer()
            if index == sizer.GetItem(len(sizer.Children)-1).GetWindow().index:
                sizer.DeleteWindows()
                self.activites_sizer.Detach(i)
        creche.activites[index].delete()
        del creche.activites[index]
        self.sizer.Layout()
        self.UpdateContents()

    def UpdateHash(self, hash_cb, color):
        r, g, b, a, h = color
        hash_cb.Clear()
        for i, hash in enumerate((wx.SOLID, wx.TRANSPARENT, wx.BDIAGONAL_HATCH, wx.CROSSDIAG_HATCH, wx.FDIAGONAL_HATCH, wx.CROSS_HATCH, wx.HORIZONTAL_HATCH, wx.VERTICAL_HATCH)):
            hash_cb.Append("", (r, g, b, a, hash))
            if hash == h:
                hash_cb.SetSelection(i)
            
    def onColorButton(self, event):
        obj = event.GetEventObject()
        r, g, b, a, h = couleur = getattr(obj.activite, obj.field[0])
        data = wx.ColourData()
        data.SetColour((r, g, b, a))
        try:
            import wx.lib.agw.cubecolourdialog as CCD
            dlg = CCD.CubeColourDialog(self, data)
            dlg.GetColourData().SetChooseFull(True)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                colour = data.GetColour()
                r, g, b, a = colour.Red(), colour.Green(), colour.Blue(), colour.Alpha()
        except ImportError:
            dlg = wx.ColourDialog(self, data)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                r, g, b = data.GetColour()
        couleur = r, g, b, a, h
        for field in obj.field:
            setattr(obj.activite, field, couleur) 
        obj.SetBackgroundColour(wx.Color(r, g, b))
        self.UpdateHash(obj.hash_cb, couleur)
    
    def onHashChange(self, event):
        obj = event.GetEventObject()
        for field in obj.field:
            setattr(obj.activite, field, obj.GetClientData(obj.GetSelection()))

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
        self.ouverture_cb = AutoTimeCtrl(self, creche, "ouverture")
        self.fermeture_cb = AutoTimeCtrl(self, creche, "fermeture")
        self.ouverture_cb.check_function = self.ouverture_check
        self.fermeture_cb.check_function = self.fermeture_check
        self.Bind(wx.EVT_CHOICE, self.onOuverture, self.ouverture_cb)
        self.Bind(wx.EVT_CHOICE, self.onOuverture, self.fermeture_cb)
        sizer2.AddMany([(self.ouverture_cb, 0, wx.EXPAND), (self.ouverture_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (self.fermeture_cb, 0, wx.EXPAND), (self.fermeture_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures d\'ouverture :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.affichage_min_cb = AutoTimeCtrl(self, creche, "affichage_min")
        self.affichage_max_cb = AutoTimeCtrl(self, creche, "affichage_max")
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_min_cb)
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_max_cb)
        sizer2.AddMany([(self.affichage_min_cb, 0, wx.EXPAND), (self.affichage_min_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (self.affichage_max_cb, 0, wx.EXPAND), (self.affichage_max_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Heures affichées sur le planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Granularité du planning :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'granularite', [('10min', 10), ('1/4 heure', 15), ('1/2 heure', 30), ('1 heure', 60)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nombre de mois payés :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'mois_payes', [('12 mois', 12), ('11 mois', 11)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences prévisionnelles :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'presences_previsionnelles', [(u'Géré', True), (u'Non géré', False)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Présences supplémentaires :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'presences_supplementaires', [(u'Géré', True), (u'Non géré', False)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Modes d'inscription :"), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'modes_inscription', [(u'Crèche à plein-temps uniquement', MODE_5_5), ('Tous modes', MODE_5_5+MODE_4_5+MODE_3_5+MODE_HALTE_GARDERIE)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Mode de facturation :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'mode_facturation', [("Forfait 10h / jour", FACTURATION_FORFAIT_10H), (u"PSU (horaires réels)", FACTURATION_PSU), (u"PAJE (taux horaire fixe)", FACTURATION_PAJE)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Forfait horaire (PAJE):'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'forfait_horaire', precision=2), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Tarification des activités :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'tarification_activites', [(u'Non géré', ACTIVITES_NON_FACTUREES), (u'A la journée', ACTIVITES_FACTUREES_JOURNEE), (u"Période d'adaptation, à la journée", ACTIVITES_FACTUREES_JOURNEE_PERIODE_ESSAI)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Majoration mensuelle pour enfants hors commune:'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'majoration_localite', precision=2), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Traitement des absences pour maladie :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'traitement_maladie', [(u"Avec carence", DEDUCTION_MALADIE_AVEC_CARENCE), ("Sans carence", DEDUCTION_MALADIE_SANS_CARENCE)]), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Durée minimale d'absence pour déduction / Durée de la carence :"), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'minimum_maladie', min=0, precision=0), 0, 0)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)
    
    def ouverture_check(self, ouverture, a, b):
        return a >= ouverture * 4
    
    def fermeture_check(self, fermeture, a, b):
        return b <= fermeture * 4
    
    def onOuverture(self, event):
        errors = []
        obj = event.GetEventObject()
        value = event.GetClientData()
        for inscrit in creche.inscrits:
            for inscription in inscrit.inscriptions:
                for j, jour in enumerate(inscription.reference):
                    for a, b, v in jour.activites.keys():
                        if not obj.check_function(value, a, b):
                            errors.append((inscrit, jour, " (%s)" % periodestr(inscription), days[j%7].lower()))
            for j in inscrit.journees.keys():
                jour = inscrit.journees[j]
                for a, b, v in jour.activites.keys():
                    if not obj.check_function(value, a, b):
                        errors.append((inscrit, jour, "", date2str(j)))
                
        if errors:
            message = u"Diminuer la période d'ouverture changera les plannings des enfants suivants :\n"
            for inscrit, jour, info, date in errors:
                message += '  %s %s%s le %s\n' % (inscrit.prenom, inscrit.nom, info, date)
            message += 'Confirmer ?'
            dlg = wx.MessageDialog(self, message, 'Confirmation', wx.OK|wx.CANCEL|wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                obj.UpdateContents()
                return
        obj.AutoChange(value)
        for inscrit, jour, info, date in errors:
            for i in range(0, int(creche.ouverture*4)) + range(int(creche.fermeture*4), 24 * 60 / BASE_GRANULARITY):
                jour.values[i] = 0
            jour.save()
        if creche.affichage_min > creche.ouverture:
            creche.affichage_min = creche.ouverture
            self.affichage_min_cb.UpdateContents()
        if creche.affichage_max < creche.fermeture:
            creche.affichage_max = creche.fermeture
            self.affichage_max_cb.UpdateContents()
            
    def onAffichage(self, event):
        obj = event.GetEventObject()
        value = event.GetClientData()
        error = False
        if obj is self.affichage_min_cb:
            if value > creche.ouverture:
                error = True
        else:
            if value < creche.fermeture:
                error = True
        if error:
            dlg = wx.MessageDialog(self, u"La période d'affichage doit couvrir au moins l'amplitude horaire de la crèche !", "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            obj.UpdateContents()
        else:
            obj.AutoChange(value)

class CrecheNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(CrecheTab(self), u'Crèche')
        self.AddPage(EmployesTab(self), u'Employés')
        self.AddPage(ResponsabilitesTab(self), u'Responsabilités')
        self.AddPage(CafTab(self), 'C.A.F.')
        self.AddPage(JoursFermeturePanel(self), u'Congés')
        self.AddPage(ActivitesTab(self), u'Couleurs / Activités')
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
