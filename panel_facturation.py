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
import os.path, sys
import string, datetime
import wx, wx.lib.scrolledpanel, wx.html
import xml.dom.minidom
from constants import *
from functions import *
from facture import *
from ooffice import *
from controls import *
from doc_facture_mensuelle import FactureModifications
from doc_export_compta import ExportComptaModifications
from doc_attestation_paiement import AttestationModifications
from doc_appel_cotisations import AppelCotisationsModifications
from sqlobjects import Correction, NumeroFacture

class CorrectionsTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # la selection du mois et le numéro de facture
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.monthchoice = wx.Choice(self)
        date = getFirstMonday()
        first_date = datetime.date(year=date.year, month=date.month, day=1) 
        while date < last_date:
            string = '%s %d' % (months[date.month - 1], date.year)
            self.monthchoice.Append(string, date)
            date = getNextMonthStart(date)
        self.monthchoice.SetStringSelection('%s %d' % (months[today.month - 1], today.year))        
        self.Bind(wx.EVT_CHOICE, self.EvtMonthChoice, self.monthchoice)
        sizer.Add(self.monthchoice, 1, wx.EXPAND, 5)
        self.numfacture = AutoNumericCtrl(self, None, 'valeur', precision=0)
        sizer.AddMany([(wx.StaticText(self, -1, u'Premier numéro de facture :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (self.numfacture, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.corrections_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.corrections_sizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.UpdateContents()
        self.Layout()
        
    def EvtMonthChoice(self, evt=None):
        while len(self.corrections_sizer.GetChildren()):
            sizer = self.corrections_sizer.GetItem(0)
            sizer.DeleteWindows()
            self.corrections_sizer.Detach(0)
            
        date = self.monthchoice.GetClientData(self.monthchoice.GetSelection())
        if not date in creche.numeros_facture:
            creche.numeros_facture[date] = NumeroFacture(date)
        self.numfacture.SetInstance(creche.numeros_facture[date])
        
        for inscrit in creche.inscrits:
            if inscrit.HasFacture(date): # TODO and date not in inscrit.factures_cloturees:
                if not date in inscrit.corrections:
                    inscrit.corrections[date] = Correction(inscrit, date)
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.Add(wx.StaticText(self, -1, GetPrenomNom(inscrit), size=(200, -1)), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 15)
                sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, inscrit.corrections[date], 'libelle')])
                sizer.AddMany([(wx.StaticText(self, -1, 'Valeur :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, inscrit.corrections[date], 'valeur', precision=2)])
                self.corrections_sizer.Add(sizer)
        
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)              

    def UpdateContents(self):
        self.EvtMonthChoice()
        
class FacturationTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.inscrits_choice = {}
        
        # Les appels de cotisations
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des appels de cotisation'), wx.HORIZONTAL)
        self.appels_monthchoice = wx.Choice(self)
        date = getFirstMonday()
        first_date = datetime.date(year=date.year, month=date.month, day=1) 
        while date < last_date:
            string = '%s %d' % (months[date.month - 1], date.year)
            self.appels_monthchoice.Append(string, date)
            date = getNextMonthStart(date)
        self.appels_monthchoice.SetStringSelection('%s %d' % (months[today.month - 1], today.year))
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationAppelCotisations, button)
        box_sizer.AddMany([(self.appels_monthchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les factures
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Clôture et édition des factures'), wx.HORIZONTAL)
        self.inscrits_choice["factures"] = wx.Choice(self)
        self.factures_monthchoice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtFacturesInscritChoice, self.inscrits_choice["factures"])
        self.Bind(wx.EVT_CHOICE, self.EvtFacturesMonthChoice, self.factures_monthchoice)
        self.cloture_button = wx.Button(self, -1, u'Clôture')
        self.Bind(wx.EVT_BUTTON, self.EvtClotureFacture, self.cloture_button)
        button2 = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFacture, button2)
        box_sizer.AddMany([(self.inscrits_choice["factures"], 1, wx.ALL|wx.EXPAND, 5), (self.factures_monthchoice, 1, wx.ALL|wx.EXPAND, 5), (self.cloture_button, 0, wx.ALL, 5), (button2, 0, wx.ALL, 5)])
        if IsTemplateFile("Export compta.txt"):
            exportButton = wx.Button(self, -1, u'Export compta')
            self.Bind(wx.EVT_BUTTON, self.EvtExportCompta, exportButton)
            box_sizer.Add(exportButton, 0, wx.ALL, 5)
        if config.options & DECLOTURE:
            self.decloture_button = wx.Button(self, -1, u'Dé-clôture')
            self.Bind(wx.EVT_BUTTON, self.EvtDeclotureFacture, self.decloture_button)
            box_sizer.Add(self.decloture_button, 0, wx.ALL, 5)
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les attestations de paiement
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des attestations de paiement'), wx.HORIZONTAL)
        self.inscrits_choice["recus"] = wx.Choice(self)
        self.recus_periodechoice = wx.Choice(self)
        self.recus_endchoice = wx.Choice(self)
        self.recus_endchoice.Disable()
        self.Bind(wx.EVT_CHOICE, self.EvtRecusInscritChoice, self.inscrits_choice["recus"])
        self.Bind(wx.EVT_CHOICE, self.EvtRecusPeriodeChoice, self.recus_periodechoice)
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationRecu, button)
        box_sizer.AddMany([(self.inscrits_choice["recus"], 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                           (self.recus_periodechoice, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                           (wx.StaticText(self, -1, '-'), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                           (self.recus_endchoice, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                           (button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        self.SetSizer(sizer)
        self.UpdateContents()
        self.Layout()

    def EvtFacturesInscritChoice(self, evt):
        selection = self.factures_monthchoice.GetStringSelection()
        self.factures_monthchoice.Clear()
        inscrit = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        date = getFirstMonday()
        while date <= datetime.date.today():
            if IsFacture(date) and (isinstance(inscrit, list) or inscrit.HasFacture(date)):
                self.factures_monthchoice.Append('%s %d' % (months[date.month - 1], date.year), date)
            date = getNextMonthStart(date)
        self.factures_monthchoice.SetSelection(self.factures_monthchoice.GetCount()-1)
        self.EvtFacturesMonthChoice()
        
    def EvtFacturesMonthChoice(self, evt=None):
        date = self.factures_monthchoice.GetClientData(self.factures_monthchoice.GetSelection())
        if date:
            inscrits = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
            if not isinstance(inscrits, list):
                inscrits = [inscrits]
            for inscrit in inscrits:
                if inscrit.HasFacture(date) and date not in inscrit.factures_cloturees:
                    self.cloture_button.Enable()
                    break
            else:
                self.cloture_button.Disable()

    def EvtRecusInscritChoice(self, evt):
        self.recus_periodechoice.Clear()
        need_separator = False
        inscrit = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        if isinstance(inscrit, list):
            need_separator = True
            self.recus_periodechoice.Append(u"Année %d" % (today.year-1), (datetime.date(today.year-1, 1, 1), datetime.date(today.year-1, 12, 31)))
            if today.month == 1:
                self.recus_periodechoice.Append("Janvier %d" % today.year, (datetime.date(today.year, 1, 1), datetime.date(today.year, 1, 31)))
            else:
                self.recus_periodechoice.Append(u"Janvier - %s %d" % (months[today.month-1], today.year), (datetime.date(today.year, 1, 1), datetime.date(today.year, today.month, 1)))
        else:
            for year in range(today.year-10, today.year):
                if inscrit.GetInscriptions(datetime.date(year, 1, 1), datetime.date(year, 12, 31)):
                    need_separator = True
                    self.recus_periodechoice.Append(u"Année %d" % year, (datetime.date(year, 1, 1), datetime.date(year, 12, 31)))
            if inscrit.GetInscriptions(datetime.date(today.year, 1, 1), getMonthEnd(today)):
                need_separator = True
                debut = 1
                while not inscrit.GetInscriptions(datetime.date(today.year, debut, 1), getMonthEnd(datetime.date(today.year, debut, 1))) and debut < today.month:
                    debut += 1
                if debut == today.month:
                    self.recus_periodechoice.Append("%s %d" % (months[debut-1], today.year), (datetime.date(today.year, debut, 1), getMonthEnd(datetime.date(today.year, debut, 1))))
                else:
                    self.recus_periodechoice.Append(u"%s - %s %d" % (months[debut-1], months[today.month-1], today.year), (datetime.date(today.year, debut, 1), datetime.date(today.year, today.month, 1)))

        
        date = getFirstMonday()
        while date < today:
            if isinstance(inscrit, list) or inscrit.GetInscriptions(datetime.date(date.year, date.month, 1), getMonthEnd(date)):
                if need_separator:
                    self.recus_periodechoice.Append(20 * "-", None)
                    need_separator = False
                self.recus_periodechoice.Append('%s %d' % (months[date.month - 1], date.year), (datetime.date(date.year, date.month, 1), getMonthEnd(date)))
            date = getNextMonthStart(date)
        self.recus_periodechoice.SetSelection(0)
        self.EvtRecusPeriodeChoice(evt)

    def EvtRecusPeriodeChoice(self, evt):
        inscrit = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        periode = self.recus_periodechoice.GetClientData(self.recus_periodechoice.GetSelection())
        self.recus_endchoice.Clear()
        if periode:
            debut, fin = periode
            if debut.month == fin.month and debut < today:
                date = debut
                while date < today:
                    if isinstance(inscrit, list) or inscrit.GetInscriptions(datetime.date(date.year, date.month, 1), getMonthEnd(date)):
                        self.recus_endchoice.Append('%s %d' % (months[date.month - 1], date.year), (datetime.date(date.year, date.month, 1), getMonthEnd(date)))
                    date = getNextMonthStart(date)
                self.recus_endchoice.Enable()
                self.recus_endchoice.SetSelection(0)
            else:
                self.recus_endchoice.Disable()
        else:
            self.recus_periodechoice.SetSelection(0)
            self.EvtRecusPeriodeChoice(evt)

    def UpdateContents(self):
        for choice in self.inscrits_choice.values():
            choice.Clear()
            choice.Append('Tous les enfants', creche.inscrits)
            if len(creche.sites) > 1:
                sites = { }
                for inscrit in creche.inscrits:
                    for inscription in inscrit.inscriptions:
                        if inscription.site:
                            if inscription.site not in sites:
                                sites[inscription.site] = set()
                            sites[inscription.site].add(inscrit)
                for site in sites:
                    choice.Append('Enfants du site ' + site.nom.strip(), list(sites[site]))
            
        inscrits = { }
        autres = { }
        for inscrit in creche.inscrits:
            if inscrit.GetInscription(datetime.date.today()) != None:
                inscrits[GetPrenomNom(inscrit)] = inscrit
            else:
                autres[GetPrenomNom(inscrit)] = inscrit
        
        keys = inscrits.keys()
        keys.sort()
        for key in keys:
            for choice in self.inscrits_choice.values():
                choice.Append(key, inscrits[key])
        
        if len(inscrits) > 0 and len(autres) > 0:
            for choice in self.inscrits_choice.values():
                choice.Append(20 * '-', None)
        
        keys = autres.keys()
        keys.sort()
        for key in keys:
            for choice in self.inscrits_choice.values():
                choice.Append(key, autres[key])
            
        for choice in self.inscrits_choice.values():
            choice.SetSelection(0)
        
        self.cloture_button.Show(creche.cloture_factures)

        self.EvtFacturesInscritChoice(None)
        self.EvtRecusInscritChoice(None)
        
        self.Layout()
        
    def EvtGenerationAppelCotisations(self, evt):
        periode = self.appels_monthchoice.GetClientData(self.appels_monthchoice.GetSelection())
        DocumentDialog(self, AppelCotisationsModifications(periode, options=NO_NOM)).ShowModal()

    def __get_facturation_inscrits_periode(self):
        inscrits = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        periode = self.factures_monthchoice.GetClientData(self.factures_monthchoice.GetSelection())
        if isinstance(inscrits, list):
            inscrits = [inscrit for inscrit in inscrits if inscrit.HasFacture(periode)]
        else:
            inscrits = [inscrits]
        return inscrits, periode
            
    def EvtClotureFacture(self, evt):
        inscrits, periode = self.__get_facturation_inscrits_periode()
        errors = {}
        for inscrit in inscrits:
            try:
                facture = Facture(inscrit, periode.year, periode.month)
                facture.Cloture()
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue
        if errors:
            message = u"Erreurs lors de la clôture :\n"
            for label in errors.keys():
                message += '\n' + label + ' :\n  '
                message += '\n  '.join(errors[label])
            wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING).ShowModal()
        self.EvtFacturesMonthChoice()

    def EvtDeclotureFacture(self, evt):
        inscrits, periode = self.__get_facturation_inscrits_periode()
        errors = {}
        for inscrit in inscrits:
            try:
                date = datetime.date(periode.year, periode.month, 1)
                if date in inscrit.factures_cloturees:
                    facture = inscrit.factures_cloturees[date]
                    facture.Decloture()
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue
        if errors:
            message = u"Erreurs lors de la de-clôture :\n"
            for label in errors.keys():
                message += '\n' + label + ' :\n  '
                message += '\n  '.join(errors[label])
            wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING).ShowModal()
        self.EvtFacturesMonthChoice()

    def EvtGenerationFacture(self, evt):
        inscrits, periode = self.__get_facturation_inscrits_periode()
        if len(inscrits) > 0:
            DocumentDialog(self, FactureModifications(inscrits, periode)).ShowModal()
        else:
            wx.MessageDialog(self, u'Aucune facture pour cette période', 'Message', wx.OK|wx.ICON_WARNING).ShowModal()

    def EvtGenerationRecu(self, evt):
        inscrits = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        debut, fin = self.recus_periodechoice.GetClientData(self.recus_periodechoice.GetSelection())
        if self.recus_endchoice.IsEnabled():
            fin = self.recus_endchoice.GetClientData(self.recus_endchoice.GetSelection())[1]
        DocumentDialog(self, AttestationModifications(inscrits, debut, fin)).ShowModal()
        
    def EvtExportCompta(self, evt):
        inscrits, periode = self.__get_facturation_inscrits_periode()
        if len(inscrits) > 0:
            DocumentDialog(self, ExportComptaModifications(inscrits, periode)).ShowModal()

class FacturationNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(FacturationTab(self), "Edition")
        self.AddPage(CorrectionsTab(self), u"Corrections")

    def UpdateContents(self):
        for page in range(self.GetPageCount()):
            self.GetPage(page).UpdateContents()
        
class FacturationPanel(GPanel):
    name = "Facturation"
    bitmap = GetBitmapFile("facturation.png")
    profil = PROFIL_TRESORIER
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Facturation')
        self.notebook = FacturationNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()

