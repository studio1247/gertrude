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
from planning import GPanel
from ooffice import *

couleurs = ['C2', 'D2', 'B2', 'E2', 'A2']

class FactureModifications(object):
    def __init__(self, inscrit, periode):
        self.inscrit = inscrit
        self.periode = periode

    def execute(self, dom):
        facture = Facture(self.inscrit, self.periode.year, self.periode.month)
        debut = datetime.date(self.periode.year, self.periode.month, 1)
        if self.periode.month == 12:
            fin = datetime.date(self.periode.year, 12, 31)
        else:
            fin = datetime.date(self.periode.year, self.periode.month + 1, 1) - datetime.timedelta(1)
        inscriptions = self.inscrit.getInscriptions(debut, fin)

        # D'abord le tableau des presences du mois
        empty_cells = debut.weekday()
        if empty_cells > 4:
            empty_cells -= 7
        for table in dom.getElementsByTagName('table:table'):
            if table.getAttribute('table:name') == 'Tableau1':
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
        fields = [('nom-creche', creche.nom.upper()),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('adresse', self.inscrit.adresse),
                ('code-postal', str(self.inscrit.code_postal)),
                ('ville', self.inscrit.ville),
                ('mois', '%s %d' % (months[debut.month - 1], debut.year)),
                ('prenom', self.inscrit.prenom),
                ('date', '%.2d/%.2d/%d' % (debut.day, debut.month, debut.year)),
                ('numfact', '%.2d%.4d%.2d%.4d' % (inscriptions[0].mode + 1, debut.year, debut.month, inscriptions[0].idx)),
                ('cotisation-mensuelle', '%.2f' % facture.cotisation_mensuelle),
                ('supplement', '%.2f' % facture.supplement),
                ('deduction', '- %.2f' % facture.deduction),
                ('raison-deduction', facture.raison_deduction),
                ('total', '%.2f' % facture.total)
                ]
        if months[debut.month - 1][0] == 'A' or months[debut.month - 1][0] == 'O':
            fields.append(('de-mois', 'd\'%s %d' % (months[debut.month - 1].lower(), debut.year)))
        else:
            fields.append(('de-mois', 'de %s %d' % (months[debut.month - 1].lower(), debut.year)))
        if self.inscrit.papa.nom == self.inscrit.maman.nom:
            fields.append(('parents', '%s et %s %s' % (self.inscrit.maman.prenom, self.inscrit.papa.prenom, self.inscrit.papa.nom)))
        else:
            fields.append(('parents', '%s %s et %s %s' % (self.inscrit.maman.prenom, self.inscrit.maman.nom, self.inscrit.papa.prenom, self.inscrit.papa.nom)))

        ReplaceTextFields(dom, fields)

class AppelCotisationsModifications(object):
    def __init__(self, debut):
        self.debut = debut
        if debut.month == 12:
            self.fin = datetime.date(debut.year, 12, 31)
        else:
            self.fin = datetime.date(debut.year, debut.month+1, 1) - datetime.timedelta(1)
        
    def execute(self, dom):
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
            table.insertBefore(line, template[0])
            IncrementFormulas(template[i % 2], +2)

        table.removeChild(template[0])
        table.removeChild(template[1])

def GenereFacture(inscrit, periode, oofilename):
    GenerateDocument('./templates/facture_mensuelle_creche.odt', oofilename, FactureModifications(inscrit, periode))

def GenereAppelCotisations(date, oofilename):
    GenerateDocument('./templates/Appel Cotisations.ods', oofilename, AppelCotisationsModifications(date))

class CotisationsPanel(GPanel):
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Cotisations")
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Les appels de cotisations
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des appels de cotisation'), wx.HORIZONTAL)
        self.monthchoice1 = wx.Choice(self)
        date = getfirstmonday()
        first_date = datetime.date(year=date.year, month=date.month, day=1) 
        while date < last_date:
            string = '%s %d' % (months[date.month - 1], date.year)
            self.monthchoice1.Append(string, date)
            if date.month < 12:
                date = datetime.date(year=date.year, month=date.month + 1, day=1)
            else:
                date = datetime.date(year=date.year + 1, month=1, day=1)
        # Par defaut, on selectionne le mois courant
        self.monthchoice1.SetStringSelection('%s %d' % (months[today.month - 1], today.year))
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationAppelCotisations, button)
        box_sizer.AddMany([(self.monthchoice1, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.ALL, 5)

        # Les factures
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Edition des factures'), wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.monthchoice = wx.Choice(self)
        date = getfirstmonday()
        first_date = datetime.date(year=date.year, month=date.month, day=1) 
        while date < last_date:
            string = '%s %d' % (months[date.month - 1], date.year)
            self.monthchoice.Append(string, date)
            if date.month < 12:
                date = datetime.date(year=date.year, month=date.month + 1, day=1)
            else:
                date = datetime.date(year=date.year + 1, month=1, day=1)
        # Par defaut, on selectionne le mois precedent
        if today.month == 1:
            self.monthchoice.SetStringSelection('%s %d' % (months[11], today.year - 1))
        else:
            self.monthchoice.SetStringSelection('%s %d' % (months[today.month - 2], today.year))
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFacture, button)
        box_sizer.AddMany([(self.choice, 1, wx.ALL|wx.EXPAND, 5), (self.monthchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.ALL, 5)

        self.sizer.Add(sizer, 1, wx.EXPAND)
                    

    def UpdateContents(self):
        self.choice.Clear()
        # D'abord l'ensemble des inscrits
        self.choice.Append('Toutes les cotisations', creche.inscrits)
        # Ceux qui sont presents
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) != None:
                self.choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        self.choice.Append(50 * '-', None)
        # Les autres
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) == None:
                self.choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        self.choice.SetSelection(0)

    def EvtGenerationFacture(self, evt):
        inscrit = self.choice.GetClientData(self.choice.GetSelection())
        periode = self.monthchoice.GetClientData(self.monthchoice.GetSelection())
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
        periode = self.monthchoice1.GetClientData(self.monthchoice1.GetSelection())
        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = u"Appel cotisations %s %d.ods" % (months[periode.month - 1], periode.year)
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
        response = dlg.ShowModal()
        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                GenereAppelCotisations(periode, oofilename)
                dlg = wx.MessageDialog(self, u"Document %s généré" % oofilename, 'Message', wx.OK)                
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

if __name__ == '__main__':
    import sys, os, __builtin__
    from datafiles import *
    __builtin__.creche = Load()
   
    GenereAppelCotisations(datetime.date(2007, 8, 1), 'appel cotisations.ods')
    print u'Fichier "appel cotisations.ods" généré'
    
    for inscrit in creche.inscrits:
        if inscrit.prenom == 'Basile':
            GenereFacture(inscrit, datetime.date(2005, 12, 1), 'basile.ods')
            print u'Fichier "basile.ods" généré'



