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
from cotisation import Cotisation, CotisationException
from ooffice import *
from controls import *
from facture_mensuelle import GenereFactureMensuelle
from attestation_paiement import GenereAttestationPaiement
from appel_cotisations import GenereAppelCotisations

class FacturationPanel(GPanel):
    bitmap = './bitmaps/facturation.png'
    index = 30
    profil = PROFIL_TRESORIER
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Facturation")
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
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des factures'), wx.HORIZONTAL)
        self.inscrits_choice["factures"] = wx.Choice(self)
        self.factures_monthchoice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtFacturesInscritChoice, self.inscrits_choice["factures"])
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFacture, button)
        box_sizer.AddMany([(self.inscrits_choice["factures"], 1, wx.ALL|wx.EXPAND, 5), (self.factures_monthchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
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
        box_sizer.AddMany([(self.inscrits_choice["recus"], 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5),
                           (self.recus_periodechoice, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5),
                           (wx.StaticText(self, -1, '-'), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5),
                           (self.recus_endchoice, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND, 5),
                           (button, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        self.sizer.Add(sizer, 1, wx.EXPAND)

    def EvtFacturesInscritChoice(self, evt):
        self.factures_monthchoice.Clear()
        inscrit = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        date = getFirstMonday()
        while date < today:
            if isinstance(inscrit, list) or inscrit.getInscriptions(datetime.date(date.year, date.month, 1), getMonthEnd(date)):
                self.factures_monthchoice.Append('%s %d' % (months[date.month - 1], date.year), date)
            date = getNextMonthStart(date)
        if today.month == 1:
            self.factures_monthchoice.SetStringSelection('%s %d' % (months[11], today.year - 1))
        else:
            self.factures_monthchoice.SetStringSelection('%s %d' % (months[today.month - 2], today.year))

    def EvtRecusInscritChoice(self, evt):
        self.recus_periodechoice.Clear()
        inscrit = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        if isinstance(inscrit, list) or inscrit.getInscriptions(datetime.date(today.year-1, 1, 1), datetime.date(today.year-1, 12, 31)):
            self.recus_periodechoice.Append(u"Année %d" % (today.year-1), (datetime.date(today.year-1, 1, 1), datetime.date(today.year-1, 12, 31)))
        if isinstance(inscrit, list):
            if today.month == 1:
                self.recus_periodechoice.Append("Janvier %d" % today.year, (datetime.date(today.year, 1, 1), datetime.date(today.year, 1, 31)))
            else:
                self.recus_periodechoice.Append(u"Janvier - %s %d" % (months[today.month-1], today.year), (datetime.date(today.year, 1, 1), datetime.date(today.year, today.month, 1)))
        elif inscrit.getInscriptions(datetime.date(today.year, 1, 1), getMonthEnd(today)):
            debut = 1
            while not inscrit.getInscriptions(datetime.date(today.year, debut, 1), getMonthEnd(datetime.date(today.year, debut, 1))) and debut < today.month:
                debut += 1
            if debut == today.month:
                self.recus_periodechoice.Append("%s %d" % (months[debut-1], today.year), (datetime.date(today.year, debut, 1), getMonthEnd(datetime.date(today.year, debut, 1))))
            else:
                self.recus_periodechoice.Append(u"%s - %s %d" % (months[debut-1], months[today.month-1], today.year), (datetime.date(today.year, debut, 1), datetime.date(today.year, today.month, 1)))

        self.recus_periodechoice.Append(50 * "-", None)
        date = getFirstMonday()
        while date < today:
            if isinstance(inscrit, list) or inscrit.getInscriptions(datetime.date(date.year, date.month, 1), getMonthEnd(date)):
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
                    if isinstance(inscrit, list) or inscrit.getInscriptions(datetime.date(date.year, date.month, 1), getMonthEnd(date)):
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
        # Ceux qui sont presents
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) != None:
                for choice in self.inscrits_choice.values():
                    choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        # Les autres
        separator = False
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) == None:
                if not separator:
                    separator = True
                    for choice in self.inscrits_choice.values():
                        choice.Append(50 * '-', None)
                for choice in self.inscrits_choice.values():
                    choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        for choice in self.inscrits_choice.values():
            choice.SetSelection(0)

        self.EvtFacturesInscritChoice(None)
        self.EvtRecusInscritChoice(None)

    def EvtGenerationAppelCotisations(self, evt):
        periode = self.appels_monthchoice.GetClientData(self.appels_monthchoice.GetSelection())
        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = u"Appel cotisations %s %d.ods" % (months[periode.month - 1], periode.year)
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=config.documents_directory, defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
        response = dlg.ShowModal()
        dlg.Destroy()
        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            config.documents_directory = os.path.dirname(oofilename)
            options = NO_NOM
            try:
                errors = GenereAppelCotisations(oofilename, periode, options)
                message = u"Document %s généré" % oofilename
                if errors:
                    message += ' avec des erreurs :\n' + decodeErrors(errors)
                    dlg = wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING)
                else:
                    dlg = wx.MessageDialog(self, message, 'Message', wx.OK)
            except Exception, e:
                dlg = wx.MessageDialog(self, str(e), 'Erreur', wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def EvtGenerationFacture(self, evt):
        inscrit = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        periode = self.factures_monthchoice.GetClientData(self.factures_monthchoice.GetSelection())
        if isinstance(inscrit, list):
            dlg = wx.DirDialog(self, u'Générer des documents OpenOffice', defaultPath=documents_directory, style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                config.documents_directory = dlg.GetPath()
                inscrits = [inscrit for inscrit in creche.inscrits if inscrit.getInscription(periode) is not None]
                self.GenereFactures(inscrits, periode, oopath=config.documents_directory)
        else:
            wildcard = "OpenDocument (*.odt)|*.odt"
            oodefaultfilename = u"Cotisation %s %s %d.odt" % (inscrit.prenom, months[periode.month - 1], periode.year)
            dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=config.documents_directory, defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
            response = dlg.ShowModal()
            if response == wx.ID_OK:
                oofilename = dlg.GetPath()
                config.documents_directory = os.path.dirname(oofilename)
                self.GenereFactures([inscrit], periode, oofilename)

    def EvtGenerationRecu(self, evt):
        inscrit = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        debut, fin = self.recus_periodechoice.GetClientData(self.recus_periodechoice.GetSelection())
        if self.recus_endchoice.IsEnabled():
            fin = self.recus_endchoice.GetClientData(self.recus_endchoice.GetSelection())[1]
        if isinstance(inscrit, list):
            dlg = wx.DirDialog(self, u'Générer des documents OpenOffice', defaultPath=config.documents_directory, style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                config.documents_directory = dlg.GetPath()
                inscrits = [inscrit for inscrit in creche.inscrits if inscrit.getInscriptions(debut, fin)]
                self.GenereAttestationsPaiement(inscrits, debut, fin, oopath=config.documents_directory)
        else:
            wildcard = "OpenDocument (*.odt)|*.odt"
            oodefaultfilename = u"Attestation de paiement %s %s-%s %d.odt" % (inscrit.prenom, months[debut.month - 1], months[fin.month - 1], debut.year)
            dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=config.documents_directory, defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                oofilename = dlg.GetPath()
                config.documents_directory = os.path.dirname(oofilename)
                self.GenereAttestationsPaiement([inscrit], debut, fin, oofilename)

    def GenereFactures(self, inscrits, periode, oofilename=None, oopath=None):
        nbdocs, errors = 0, []
        for inscrit in inscrits:
            if oofilename is None:
                filename = '%s/Cotisation %s %s %d.odt' % (oopath, inscrit.prenom, months[periode.month - 1], periode.year)
            else:
                filename = oofilename
            doc_errors = GenereFactureMensuelle(filename, inscrit, periode)
            if doc_errors:
                errors.extend(doc_errors)
            else:
                nbdocs += 1

        if nbdocs > 1:
            message = u'%d factures générées' % nbdocs
        elif nbdocs == 1:
            message = u'1 facture générée'
        else:
            message = u'Aucune facture générée'
        if errors:
            message += '\n' + decodeErrors(errors)
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING)
        else:
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def GenereAttestationsPaiement(self, inscrits, debut, fin, oofilename=None, oopath=None):
        nbdocs, errors = 0, []
        for inscrit in inscrits:
            if oofilename is None:
                filename = '%s/Attestation de paiement %s %s-%s %d.odt' % (oopath, inscrit.prenom, months[debut.month - 1], months[fin.month - 1], debut.year)
            else:
                filename = oofilename
            doc_errors = GenereAttestationPaiement(filename, inscrit, debut, fin)
            if doc_errors:
                errors.extend(doc_errors)
            else:
                nbdocs += 1

        if nbdocs > 1:
            message = u'%d attestations générées' % nbdocs
        elif nbdocs == 1:
            message = u'1 attestation générée'
        else:
            message = u'Aucune attestation générée'
        if errors:
            message += '\n' + decodeErrors(errors)
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING)
        else:
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

panels = [FacturationPanel]

if __name__ == '__main__':
    import sys, os
    import config
    from data import *
    Load()

##    for inscrit in creche.inscrits:
##        if inscrit.prenom == 'Soen':
##            GenereAttestationPaiement('recu soen.ods', inscrit, datetime.date(2007, 4, 1), datetime.date(2007, 9, 1))
##            print u'Fichier "recu soen.ods" généré'
##
##    sys.exit(0)
##    GenereAppelCotisations('appel cotisations.ods', datetime.date(2007, 8, 1))
##    print u'Fichier "appel cotisations.ods" généré'
    
    for inscrit in creche.inscrits:
        if inscrit.prenom == 'Germain':
            GenereFactureMensuelle('basile.ods', inscrit, datetime.date(2007, 7, 1))
            print u'Fichier "basile.ods" généré'



