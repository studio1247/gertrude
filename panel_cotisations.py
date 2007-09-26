# -*- coding: cp1252 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os.path
import sys
import string
import datetime
import zipfile
import wx
import wx.lib.scrolledpanel
import wx.html
import xml.dom.minidom
from common import *
from facture import Facture
from cotisation import Cotisation, CotisationException
from gpanel import GPanel
from ooffice import *

couleurs = ['C2', 'D2', 'B2', 'E2', 'A2']

class FactureModifications(object):
    def __init__(self, inscrit, periode):
        self.inscrit = inscrit
        self.periode = periode

    def execute(self, dom):
        facture = Facture(self.inscrit, self.periode.year, self.periode.month)
        debut = datetime.date(self.periode.year, self.periode.month, 1)
        fin = getMonthEnd(debut)
        inscriptions = self.inscrit.getInscriptions(debut, fin)

        # D'abord le tableau des presences du mois
        empty_cells = debut.weekday()
        if empty_cells > 4:
            empty_cells -= 7
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
                break

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
                    cell.setAttribute('table:style-name', 'Tableau1.%s' % couleurs[presence])
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

    def execute(self, dom):
        date = self.debut
        total = 0.0
        while date.year < self.fin.year or date.month <= self.fin.month:
            try:
                facture = Facture(self.inscrit, date.year, date.month)
                if facture.total == 0:
                    self.debut = getNextMonthStart(self.debut)
            except CotisationException, e:
                print e.errors
            total += facture.total
            date = getNextMonthStart(date)
        
        tresorier = Select(creche.bureaux, today).tresorier

        # Les champs du recu
        fields = [('nom-creche', creche.nom),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('de-debut', '%s %d' % (getDeMoisStr(self.debut.month - 1), self.debut.year)),
                ('de-fin', '%s %d' % (getDeMoisStr(self.fin.month - 1), self.fin.year)),
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
    def __init__(self, debut):
        self.debut = debut
        self.fin = getMonthEnd(self.debut)
        
    def execute(self, dom):
        errors = []
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")

        # La date
        ReplaceFields(lignes, [('date', self.debut)])
        template = [lignes.item(5), lignes.item(6)]

        # Les cotisations
        indexes = getCrecheIndexes(self.debut, self.fin)
        for i, index in enumerate(indexes):
            inscrit = creche.inscrits[index]
            line = template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month)                
                ReplaceFields(line, [('prenom', inscrit.prenom),
                                     ('cotisation', facture.cotisation_mensuelle),
                                     ('commentaire', None)])
            except CotisationException, e:
                ReplaceFields(line, [('prenom', inscrit.prenom),
                                     ('cotisation', '?'),
                                     ('commentaire', '\n'.join(e.errors))])
                errors.append((inscrit, e.errors))
            table.insertBefore(line, template[0])
            IncrementFormulas(template[i % 2], +2)

        table.removeChild(template[0])
        table.removeChild(template[1])
        return errors

def GenereAppelCotisations(date, oofilename):
    return GenerateDocument('./templates/Appel Cotisations.ods', oofilename, AppelCotisationsModifications(date))

def GenereFacture(inscrit, periode, oofilename):
    return GenerateDocument('./templates/facture_mensuelle_creche.odt', oofilename, FactureModifications(inscrit, periode))

def GenereRecu(inscrit, debut, fin, oofilename):
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
        self.Bind(wx.EVT_CHOICE, self.EvtRecusInscritChoice, self.inscrits_choice["recus"])
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationRecu, button)
        box_sizer.AddMany([(self.inscrits_choice["recus"], 1, wx.ALL|wx.EXPAND, 5), (self.recus_periodechoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
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
        
    def UpdateContents(self):
        for choice in self.inscrits_choice.values():
            choice.Clear()
            choice.Append('Tous les enfants', creche.inscrits)
        # Ceux qui sont presents
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) != None:
                for choice in self.inscrits_choice.values():
                    choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        for choice in self.inscrits_choice.values():
            choice.Append(50 * '-', None)
        # Les autres
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) == None:
                for choice in self.inscrits_choice.values():
                    choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        for choice in self.inscrits_choice.values():
            choice.SetSelection(0)

        self.EvtFacturesInscritChoice(None)
        self.EvtRecusInscritChoice(None)

    def EvtGenerationFacture(self, evt):
        inscrit = self.inscrits_choice["factures"].GetClientData(self.inscrits_choice["factures"].GetSelection())
        periode = self.factures_monthchoice.GetClientData(self.factures_monthchoice.GetSelection())
        if type(inscrit) == list:
            dlg = wx.DirDialog(self, u'Générer des documents OpenOffice', style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
            response = dlg.ShowModal()
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

    def EvtGenerationAppelCotisations(self, evt):
        periode = self.appels_monthchoice.GetClientData(self.appels_monthchoice.GetSelection())
        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = u"Appel cotisations %s %d.ods" % (months[periode.month - 1], periode.year)
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
        response = dlg.ShowModal()
        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                errors = GenereAppelCotisations(periode, oofilename)
                message = u"Document %s généré" % oofilename
                if errors:
                    message += ' avec des erreurs :\n'
                    for error in errors:
                        message += '\n'+error[0].prenom+'\n  '
                        message += '\n  '.join(error[1])
                dlg = wx.MessageDialog(self, message, 'Message', wx.OK)                
            except Exception, e:
                dlg = wx.MessageDialog(self, str(e), 'Erreur', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def EvtGenerationRecu(self, evt):
        inscrits_choice = self.inscrits_choice["recus"]
        inscrit = inscrits_choice.GetClientData(inscrits_choice.GetSelection())
        debut, fin = self.recus_periodechoice.GetClientData(self.recus_periodechoice.GetSelection())
        wildcard = "OpenDocument (*.odt)|*.odt"
        oodefaultfilename = u"Attestation de paiement %s %s-%s %d.odt" % (inscrit.prenom, months[debut.month - 1], months[fin.month - 1], debut.year)
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
        response = dlg.ShowModal()
        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                errors = GenereRecu(inscrit, debut, fin, oofilename)
                message = u"Document %s généré" % oofilename
                if errors:
                    message += ' avec des erreurs :\n'
                    for error in errors:
                        message += '\n'+error[0].prenom+'\n  '
                        message += '\n  '.join(error[1])
                dlg = wx.MessageDialog(self, message, 'Message', wx.OK)                
            except Exception, e:
                dlg = wx.MessageDialog(self, str(e), 'Erreur', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def GenereFactures(self, inscrits, periode, oofilename=None, oopath=None):
        nbfactures = 0
        errors = []
        for inscrit in inscrits:
            try:
                if oofilename is None:
                    filename = '%s/Cotisation %s %s %d.odt' % (oopath, inscrit.prenom, months[periode.month - 1], periode.year)
                else:
                    filename = oofilename
                GenereFacture(inscrit, periode, filename)
                nbfactures += 1
            except CotisationException, e:
                errors.append('%s %s' % (inscrit.prenom, inscrit.nom))
                errors.extend(e.errors)

        if nbfactures > 1:
            message = u'%d factures générées' % nbfactures
        elif nbfactures == 1:
            message = u'1 facture générée'
        else:
            message = u'Aucune facture générée'
        if errors:
            message += '\n\n' + '\n'.join(errors)
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK | wx.ICON_WARNING)
        else:
            dlg = wx.MessageDialog(self, message, 'Message', wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

panels = [CotisationsPanel]

if __name__ == '__main__':
    import sys, os, __builtin__
    from datafiles import *
    __builtin__.creche = Load()

    for inscrit in creche.inscrits:
        if inscrit.prenom == 'Soen':
            GenereRecu(inscrit, datetime.date(2007, 4, 1), datetime.date(2007, 9, 1), 'recu soen.ods')
            print u'Fichier "recu soen.ods" généré'

    sys.exit(0)
    GenereAppelCotisations(datetime.date(2007, 8, 1), 'appel cotisations.ods')
    print u'Fichier "appel cotisations.ods" généré'
    
    for inscrit in creche.inscrits:
        if inscrit.prenom == 'Basile':
            GenereFacture(inscrit, datetime.date(2005, 12, 1), 'basile.ods')
            print u'Fichier "basile.ods" généré'



