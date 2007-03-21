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
from planning import GPanel

couleurs = ['C2', 'D2', 'B2', 'E2', 'A2']

def ReplaceFactureContent(data, inscrit, periode):
    debut = datetime.date(periode.year, periode.month, 1)
    if periode.month == 12:
        fin = datetime.date(periode.year, 12, 31)
    else:
        fin = datetime.date(periode.year, periode.month + 1, 1) - datetime.timedelta(1)
    inscriptions = inscrit.getInscriptions(debut, fin)
    
    dom = xml.dom.minidom.parseString(data)

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
    jours = jours_supplementaires = jours_maladie = supplement = deduction = 0
    cotisations_mensuelles = {}
    while date.month == debut.month:
        col = date.weekday()
        if col < 5:
            row = (date.day + empty_cells) / 7
            cell = cells[row][col]
            # ecriture de la date dans la cellule
            text_node = cell.getElementsByTagName('text:p')[0]
            text_node.firstChild.replaceWholeText('%d' % date.day)
            if not date in creche.jours_fermeture:
                jours += 1
                if inscrit.getInscription(date):
                    cotisation = Cotisation(inscrit, (date, date))
                    if cotisation.cotisation_mensuelle in cotisations_mensuelles:
                        cotisations_mensuelles[cotisation.cotisation_mensuelle] += 1
                    else:
                        cotisations_mensuelles[cotisation.cotisation_mensuelle] = 1
                    # changement de la couleur de la cellule
                    presence = inscrit.getPresence(date)
                    cell.setAttribute('table:style-name', 'Tableau1.%s' % couleurs[presence])
                    if presence == SUPPLEMENT:
                        jours_supplementaires += 1
                        supplement += cotisation.montant_jour_supplementaire
                    elif presence == MALADE:
                        tmp = date - datetime.timedelta(1)
                        while date - tmp < datetime.timedelta(15):
                            presence_tmp = inscrit.getPresence(tmp)
                            if presence_tmp == PRESENT or presence_tmp == VACANCES:
                                break
                            tmp -= datetime.timedelta(1)
                        else:
                            jours_maladie += 1
                            deduction += cotisation.montant_jour_supplementaire
        date += datetime.timedelta(1)

    for i in range(row + 1, len(rows)):
        table.removeChild(rows[i])        

    # Les autres champs de la facture
    if jours_maladie > 0:
        raison_deduction = u'(maladie > 15j consécutifs)'
    else:
        raison_deduction = ''

    cotisation_mensuelle = 0.00
    for cotisation in cotisations_mensuelles:
        cotisation_mensuelle += cotisation * cotisations_mensuelles[cotisation] / jours
    strings = [('nom-creche', creche.nom.upper()),
               ('adresse-creche', creche.adresse),
               ('code-postal-creche', str(creche.code_postal)),
               ('ville-creche', creche.ville),
               ('adresse', inscrit.adresse),
               ('code-postal', str(inscrit.code_postal)),
               ('ville', inscrit.ville),
               ('mois', '%s %d' % (months[debut.month - 1], debut.year)),
               ('prenom', inscrit.prenom),
               ('date', '%.2d/%.2d/%d' % (debut.day, debut.month, debut.year)),
               ('numfact', '%.2d%.4d%.2d%.4d' % (inscriptions[0].mode + 1, debut.year, debut.month, inscriptions[0].idx)),
               ('cotisation-mensuelle', '%.2f' % cotisation_mensuelle),
               ('supplement', '%.2f' % supplement),
               ('deduction', '- %.2f' % deduction),
               ('raison-deduction', raison_deduction),
               ('total', '%.2f' % (cotisation_mensuelle + supplement - deduction))
               ]
    if months[debut.month - 1][0] == 'A' or months[debut.month - 1][0] == 'O':
        strings.append(('de-mois', 'd\'%s %d' % (months[debut.month - 1].lower(), debut.year)))
    else:
        strings.append(('de-mois', 'de %s %d' % (months[debut.month - 1].lower(), debut.year)))
    if inscrit.papa.nom == inscrit.maman.nom:
        strings.append(('parents', '%s et %s %s' % (inscrit.maman.prenom, inscrit.papa.prenom, inscrit.papa.nom)))
    else:
        strings.append(('parents', '%s %s et %s %s' % (inscrit.maman.prenom, inscrit.maman.nom, inscrit.papa.prenom, inscrit.papa.nom)))
    
    text_nodes = dom.getElementsByTagName('text:p')
    for node in text_nodes:
        try:
            text = node.firstChild.wholeText
            replace = 0
            for tag, value in strings:
                tag = '<%s>' % tag
                if tag in text:
                    replace = 1
                    text = text.replace(tag, value)
            if replace:
                node.firstChild.replaceWholeText(text)
        except:
            pass

    return dom.toxml('UTF-8')
        
def GenereFacture(inscrit, periode, oofilename):
  template = zipfile.ZipFile('./templates/facture_mensuelle_creche.odt', 'r')
  files = []
  for filename in template.namelist():
    data = template.read(filename)
    if filename == 'content.xml':
      data = ReplaceFactureContent(data, inscrit, periode)
    files.append((filename, data))
  template.close()

  oofile = zipfile.ZipFile(oofilename, 'w')
  for filename, data in files:
    oofile.writestr(filename, data)
  oofile.close()

class CotisationsPanel(GPanel):
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Cotisations")
        wx.StaticBox(self, -1, u'Edition des appels de cotisation', pos=(5, 35), size=(600, 75))
        self.choice = wx.Choice(self, -1, pos=(20, 60), size=(200, 30))
        self.monthchoice = wx.Choice(self, -1, pos=(240, 60), size=(200, 30))
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
        button = wx.Button(self, -1, u'Génération', pos=(480, 60))
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFacture, button)
    
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
                errors = []
                for inscrit in creche.inscrits:
                    if inscrit.getInscription(periode) != None: # TODO cotisations ...
                        try:
                            GenereFacture(inscrit, periode, '%s/Cotisation %s %s %d.odt' % (oopath, inscrit.prenom, months[periode.month - 1], periode.year))
                        except CotisationException, e:
                            errors.append('%s %s' % (inscrit.prenom, inscrit.nom))
                            errors.extend(e.errors)

                if errors:
                    error = '\n'.join(errors)
                    dlg = wx.MessageDialog(self, error, 'Erreur', wx.OK | wx.ICON_ERROR)
                    dlg.ShowModal()
                    dlg.Destroy()
        else:
            wildcard = "OpenDocument (*.odt)|*.odt"
            oodefaultfilename = "Cotisation %s %s %d.odt" % (inscrit.prenom, months[periode.month - 1], periode.year)
            dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE)
            response = dlg.ShowModal()
            if response == wx.ID_OK:
                oofilename = dlg.GetPath()
                try:
                    GenereFacture(inscrit, periode, oofilename)
                except CotisationException, e:
                    error = '\n'.join(e.errors)
                    dlg = wx.MessageDialog(self, '%s\n%s' % (inscrit.prenom, error), 'Erreur', wx.OK | wx.ICON_INFORMATION)
                    dlg.ShowModal()
                    dlg.Destroy()

if __name__ == '__main__':
  import sys, os
  from datafiles import *
  creche, inscrits = readBase(con)
  #today = datetime.date.today()

  for inscrit in inscrits:
      if inscrit.prenom == 'Basile':
          GenereFacture(inscrit, datetime.date(2005, 12, 1), 'basile.ods')



