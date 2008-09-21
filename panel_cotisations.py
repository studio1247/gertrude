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
import sys
import string
import datetime
import zipfile
import wx
import wx.lib.scrolledpanel
import wx.html
import xml.dom.minidom
from constants import *
from functions import *
from facture import *
from cotisation import Cotisation, CotisationException
from gpanel import GPanel
from ooffice import *

couleurs = ['C2', 'D2', 'B2', 'E2', 'A2']

class FactureModifications(object):
    def __init__(self, inscrit, periode):
        self.inscrit = inscrit
        self.periode = periode

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return []

        try:
            facture = Facture(self.inscrit, self.periode.year, self.periode.month)
        except CotisationException, e:
            return [(self.inscrit, e.errors)]

        debut, fin = getMonthStart(self.periode), getMonthEnd(self.periode)
        inscriptions = self.inscrit.getInscriptions(debut, fin)

        # D'abord le tableau des presences du mois
        empty_cells = debut.weekday()
        if empty_cells > 4:
            empty_cells -= 7

        #    création d'un tableau de cells
        for table in dom.getElementsByTagName('table:table'):
            if table.getAttribute('table:name') == 'Presences':
                rows = table.getElementsByTagName('table:table-row')[1:]
                cells = []
                for i in range(len(rows)):
                    cells.append(rows[i].getElementsByTagName('table:table-cell'))
                    for cell in cells[i]:
                        cell.setAttribute('table:style-name', 'Tableau1.E2')
                        text_node = cell.getElementsByTagName('text:p')[0]
                        text_node.firstChild.replaceWholeText(' ')

                date = debut
                while date.month == debut.month:
                    col = date.weekday()
                    if col < 5:
                        row = (date.day + empty_cells) / 7
                        cell = cells[row][col]
                        # ecriture de la date dans la cellule
                        text_node = cell.getElementsByTagName('text:p')[0]
                        text_node.firstChild.replaceWholeText('%d' % date.day)
                        if not date in creche.jours_fermeture:
                            # changement de la couleur de la cellule
                            presence = self.inscrit.getPresence(date)[0]
                            cell.setAttribute('table:style-name', 'Presences.%s' % couleurs[presence])
                    date += datetime.timedelta(1)

                for i in range(row + 1, len(rows)):
                    table.removeChild(rows[i])

        # Les champs de la facture
        fields = [('nom-creche', creche.nom),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('adresse', self.inscrit.adresse),
                ('code-postal', str(self.inscrit.code_postal)),
                ('ville', self.inscrit.ville),
                ('mois', '%s %d' % (months[debut.month - 1], debut.year)),
                ('de-mois', '%s %d' % (getDeMoisStr(debut.month - 1), debut.year)),
                ('prenom', self.inscrit.prenom),
                ('parents', getParentsStr(self.inscrit)),
                ('date', '%.2d/%.2d/%d' % (debut.day, debut.month, debut.year)),
                ('numfact', '%.2d%.4d%.2d%.4d' % (inscriptions[0].mode + 1, debut.year, debut.month, inscriptions[0].idx)),
                ('cotisation-mensuelle', '%.2f' % facture.cotisation_mensuelle),
                ('supplement', '%.2f' % facture.supplement),
                ('deduction', '- %.2f' % facture.deduction),
                ('raison-deduction', facture.raison_deduction),
                ('total', '%.2f' % facture.total)
                ]

        ReplaceTextFields(dom, fields)
        return []

class RecuModifications(object):
    def __init__(self, inscrit, debut, fin):
        self.inscrit = inscrit
        self.debut, self.fin = debut, fin

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return []
        
        facture_debut = facture_fin = None
        date = self.debut
        total = 0.0
        while date <= self.fin:
            try:
                facture = Facture(self.inscrit, date.year, date.month)
                if facture.total != 0:
		    if facture_debut is None:
		        facture_debut = date
	            facture_fin = getMonthEnd(date)
                    total += facture.total
            except CotisationException, e:
                return [(self.inscrit, e.errors)]

            date = getNextMonthStart(date)
        
        tresorier = Select(creche.bureaux, today).tresorier

        # Les champs du recu
        fields = [('nom-creche', creche.nom),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('de-debut', '%s %d' % (getDeMoisStr(facture_debut.month - 1), facture_debut.year)),
                ('de-fin', '%s %d' % (getDeMoisStr(facture_fin.month - 1), facture_fin.year)),
                ('prenom', self.inscrit.prenom),
                ('parents', getParentsStr(self.inscrit)),
                ('naissance', self.inscrit.naissance),
                ('nom', self.inscrit.nom),
                ('tresorier', "%s %s" % (tresorier.prenom, tresorier.nom)),
                ('date', '%.2d/%.2d/%d' % (today.day, today.month, today.year)),
                ('total', '%.2f' % total)
                ]

        if self.inscrit.sexe == 1:
            fields.append(('ne-e', u"né"))
        else:
            fields.append(('ne-e', u"née"))

        #print fields
        ReplaceTextFields(dom, fields)
        return []

class AppelCotisationsModifications(object):
    def __init__(self, debut, options=0):
        self.debut, self.fin = debut, getMonthEnd(debut)
        self.options = options
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return []
        
        errors = []
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")

        # La date
        ReplaceFields(lignes, [('date', self.debut)])
        template = [lignes.item(5), lignes.item(6)]

        # Les cotisations
        inscrits = getInscrits(self.debut, self.fin)
        for i, inscrit in enumerate(inscrits):
            line = template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month, self.options)
                cotisation, supplement = facture.cotisation_mensuelle, None
                commentaire = None
                if self.debut.month == 10 and self.options & RATTRAPAGE_SEPTEMBRE:
                    facture_septembre = Facture(inscrit, self.debut.year, 9)
                    facture_septembre_fausse = Facture(inscrit, self.debut.year, 9, REVENUS_ANNEE_PRECEDENTE)
                    supplement = facture_septembre.cotisation_mensuelle - facture_septembre_fausse.cotisation_mensuelle
            except CotisationException, e:
                cotisation, supplement = '?', None
                commentaire = '\n'.join(e.errors)
                errors.append((inscrit, e.errors))
            ReplaceFields(line, [('prenom', inscrit.prenom),
                                 ('cotisation', cotisation),
                                 ('supplement', supplement),
                                 ('commentaire', commentaire)])
            table.insertBefore(line, template[0])
            IncrementFormulas(template[i % 2], +2)

        table.removeChild(template[0])
        table.removeChild(template[1])
        return errors

def GenereAppelCotisations(oofilename, date, options=0):
    return GenerateDocument('./templates/Appel Cotisations.ods', oofilename, AppelCotisationsModifications(date, options))

def GenereFacture(oofilename, inscrit, periode):
    return GenerateDocument('./templates/facture_mensuelle_creche.odt', oofilename, FactureModifications(inscrit, periode))

def GenereRecu(oofilename, inscrit, debut, fin):
    return GenerateDocument('./templates/Attestation paiement.odt', oofilename, RecuModifications(inscrit, debut, fin))

class CotisationsPanel(GPanel):
    bitmap = './bitmaps/facturation.png'
    index = 30
    profil = PROFIL_TRESORIER
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Cotisations")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.inscrits_choice = {}
        
        # Les appels de cotisations
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des appels de cotisation'), wx.HORIZONTAL)
        self.appels_monthchoice = wx.Choice(self)
        date = getfirstmonday()
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
        date = getfirstmonday()
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
        date = getfirstmonday()
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
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
        response = dlg.ShowModal()
        dlg.Destroy()
        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            options = NO_NOM
            if periode.month == 9:
                dlg = wx.MessageDialog(self, u"Voulez-vous un appel de cotisations basé sur les revenus de l'année précédente ?",
                                       'Message', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    options |= REVENUS_ANNEE_PRECEDENTE
                dlg.Destroy()
            elif periode.month == 10:
                dlg = wx.MessageDialog(self, u"Voulez-vous un appel de cotisations prenant en compte les rattrapages du mois de septembre ?",
                                       'Message', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
                if dlg.ShowModal() == wx.ID_YES:
                    options |= RATTRAPAGE_SEPTEMBRE
                dlg.Destroy()
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
            dlg = wx.DirDialog(self, u'Générer des documents OpenOffice', style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                oopath = dlg.GetPath()
                inscrits = [inscrit for inscrit in creche.inscrits if inscrit.getInscription(periode) is not None]
                self.GenereFactures(inscrits, periode, oopath=oopath)
        else:
            wildcard = "OpenDocument (*.odt)|*.odt"
            oodefaultfilename = u"Cotisation %s %s %d.odt" % (inscrit.prenom, months[periode.month - 1], periode.year)
            dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
            response = dlg.ShowModal()
            if response == wx.ID_OK:
                oofilename = dlg.GetPath()
                self.GenereFactures([inscrit], periode, oofilename)

    def EvtGenerationRecu(self, evt):
        inscrit = self.inscrits_choice["recus"].GetClientData(self.inscrits_choice["recus"].GetSelection())
        debut, fin = self.recus_periodechoice.GetClientData(self.recus_periodechoice.GetSelection())
        if self.recus_endchoice.IsEnabled():
            fin = self.recus_endchoice.GetClientData(self.recus_endchoice.GetSelection())[1]
        if isinstance(inscrit, list):
            dlg = wx.DirDialog(self, u'Générer des documents OpenOffice', style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                oopath = dlg.GetPath()
                inscrits = [inscrit for inscrit in creche.inscrits if inscrit.getInscriptions(debut, fin)]
                self.GenereRecus(inscrits, debut, fin, oopath=oopath)
        else:
            wildcard = "OpenDocument (*.odt)|*.odt"
            oodefaultfilename = u"Attestation de paiement %s %s-%s %d.odt" % (inscrit.prenom, months[debut.month - 1], months[fin.month - 1], debut.year)
            dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                oofilename = dlg.GetPath()
                self.GenereRecus([inscrit], debut, fin, oofilename)

    def GenereFactures(self, inscrits, periode, oofilename=None, oopath=None):
        nbdocs, errors = 0, []
        for inscrit in inscrits:
            if oofilename is None:
                filename = '%s/Cotisation %s %s %d.odt' % (oopath, inscrit.prenom, months[periode.month - 1], periode.year)
            else:
                filename = oofilename
            doc_errors = GenereFacture(filename, inscrit, periode)
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

    def GenereRecus(self, inscrits, debut, fin, oofilename=None, oopath=None):
        nbdocs, errors = 0, []
        for inscrit in inscrits:
            if oofilename is None:
                filename = '%s/Attestation de paiement %s %s-%s %d.odt' % (oopath, inscrit.prenom, months[debut.month - 1], months[fin.month - 1], debut.year)
            else:
                filename = oofilename
            doc_errors = GenereRecu(filename, inscrit, debut, fin)
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

panels = [CotisationsPanel]

if __name__ == '__main__':
    import sys, os
    import config
    from data import *
    Load()

##    for inscrit in creche.inscrits:
##        if inscrit.prenom == 'Soen':
##            GenereRecu('recu soen.ods', inscrit, datetime.date(2007, 4, 1), datetime.date(2007, 9, 1))
##            print u'Fichier "recu soen.ods" généré'
##
##    sys.exit(0)
##    GenereAppelCotisations('appel cotisations.ods', datetime.date(2007, 8, 1))
##    print u'Fichier "appel cotisations.ods" généré'
    
    for inscrit in creche.inscrits:
        if inscrit.prenom == 'Germain':
            GenereFacture('basile.ods', inscrit, datetime.date(2007, 7, 1))
            print u'Fichier "basile.ods" généré'



