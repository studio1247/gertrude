# -*- coding: cp1252 -*-

import os.path
import sys
import string
import datetime
import zipfile
from wxPython.wx import *
import wx
import wx.lib.scrolledpanel
import wx.html
import xml.dom.minidom
from common import *
from planning import GPanel
from Controls import *

couleurs = ['C2', 'D2', 'B2', 'E2', 'A2']

class CotisationException(Exception):
    def __init__(self, errors):
        self.errors = errors
        
class Cotisation:
    def __init__(self, creche, inscrit, periode):
        self.creche = creche
        self.inscrit = inscrit
        self.debut, self.fin = periode
        errors = []
        if not inscrit.prenom or not inscrit.nom or not inscrit.naissance or not inscrit.code_postal or not inscrit.ville:
            errors.append(u" - L'état civil de l'enfant est incomplet.")
        if not inscrit.papa.prenom or not inscrit.maman.prenom or not inscrit.papa.nom or not inscrit.maman.nom:
            errors.append(u" - L'état civil des parents est incomplet.")
        if self.debut is None:
            errors.append(u" - La date de début de la période n'est pas renseignée.")
            raise CotisationException(errors)
        self.revenus_papa = Select(inscrit.papa.revenus, self.debut)
        if self.revenus_papa is None or self.revenus_papa.revenu == '':
            errors.append(u" - Les déclarations de revenus du papa sont incomplètes.")
        self.revenus_maman = Select(inscrit.maman.revenus, self.debut)
        if self.revenus_maman is None or self.revenus_maman.revenu == '':
            errors.append(u" - Les déclarations de revenus de la maman sont incomplètes.")
        self.bureau = Select(creche.bureaux, self.debut)     
        if self.bureau is None:
            errors.append(u" - Il n'y a pas de bureau à cette date.")
        self.inscription = inscrit.getInscription(self.debut)
        if self.inscription is None:
            errors.append(u" - Il n'y a pas d'inscription à cette date.")
            raise CotisationException(errors)

        self.mode_garde = self.inscription.mode
        jours_garde = 0
        for jour in range(5):
            for tranche in range(3):
                if self.inscription.periode_reference[jour][tranche]:
                    jours_garde += 1
                    break
        if self.inscription.mode == 0 and jours_garde < 3:
            errors.append(u" - La semaine type de l'enfant est incompl&egrave;te pour le mode d'accueil choisi.")
            
        if len(errors) > 0:
            raise CotisationException(errors)
        
        self.assiette_annuelle = float(self.revenus_papa.revenu) 
        if self.revenus_papa.chomage:
            self.abattement_chomage_papa = 0.3 * float(self.revenus_papa.revenu)
            self.assiette_annuelle -= self.abattement_chomage_papa
            
        self.assiette_annuelle += float(self.revenus_maman.revenu)
        if self.revenus_maman.chomage:
            self.abattement_chomage_maman = 0.3 * float(self.revenus_maman.revenu)
            self.assiette_annuelle -= self.abattement_chomage_maman
            
        self.assiette_mensuelle = self.assiette_annuelle / 12
        
        self.taux_horaire = 0.05
        
        self.enfants_a_charge = 1
        self.enfants_en_creche = 1
        for frere_soeur in inscrit.freres_soeurs:
            if frere_soeur.naissance and frere_soeur.naissance <= self.debut:
                self.enfants_a_charge += 1
                if frere_soeur.entree and frere_soeur.entree <= self.debut and (frere_soeur.sortie is None or frere_soeur.sortie > self.debut):
                    self.enfants_en_creche += 1

        if self.enfants_en_creche > 1:
            self.mode_taux_horaire = u'%d enfants en crèche' % self.enfants_en_creche
            self.taux_horaire = 0.02
        else:
            self.mode_taux_horaire = u'%d enfants à charge' % self.enfants_a_charge
            if self.enfants_a_charge > 3:
                self.taux_horaire = 0.02
            elif self.enfants_a_charge == 3:
                self.taux_horaire = 0.03
            elif self.enfants_a_charge == 2:
                self.taux_horaire = 0.04
            else:
                self.mode_taux_horaire = u'1 enfant à charge'
                self.taux_horaire = 0.05

#        if (inscrit.handicape and self.taux_horaire > 0.02):
#            self.mode_taux_horaire += u', handicapé'
#            self.taux_horaire -= 0.01
    
        self.heures_garde = jours_garde * 40
        if jours_garde == 5:
            self.mode_heures_garde = u'plein temps'
        else:
            self.mode_heures_garde = u'%d/5èmes' % jours_garde

        self.montant_heure_garde = self.assiette_mensuelle * self.taux_horaire / 100
        self.cotisation_mensuelle = self.assiette_mensuelle * self.taux_horaire * self.heures_garde / 100

        if self.heures_garde < 200:
            self.montant_jour_supplementaire = self.assiette_mensuelle * self.taux_horaire / 10
        else:
            self.montant_jour_supplementaire = 0

        self.total_semaine = 0
        for j in range(5):
            if self.inscription.periode_reference[j][0] == 1: self.total_semaine += 4
            if self.inscription.periode_reference[j][1] == 1: self.total_semaine += 2
            if self.inscription.periode_reference[j][2] == 1: self.total_semaine += 4

        self.total_mois = 4 * self.total_semaine
        self.total_annee = 48 * self.total_semaine
        if self.inscription.mode == 0:
            self.cout_horaire = self.cotisation_mensuelle / self.total_mois
            
    def __cmp__(self, context2):
        return context2 == None or \
               self.cotisation_mensuelle != context2.cotisation_mensuelle or \
               self.total_mois != context2.total_mois or \
               self.bureau != context2.bureau or \
               self.assiette_annuelle != context2.assiette_annuelle

def ReplaceFactureContent(data, creche, inscrit, periode):
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
            if not date in jours_feries:
                jours += 1
                if inscrit.getInscription(date):
                    cotisation = Cotisation(creche, inscrit, (date, date))
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
        
def GenereFacture(creche, inscrit, periode, oofilename):
  template = zipfile.ZipFile('./templates/facture_mensuelle_creche.odt', 'r')
  files = []
  for filename in template.namelist():
    data = template.read(filename)
    if filename == 'content.xml':
      data = ReplaceFactureContent(data, creche, inscrit, periode)
    files.append((filename, data))
  template.close()

  oofile = zipfile.ZipFile(oofilename, 'w')
  for filename, data in files:
    oofile.writestr(filename, data)
  oofile.close()

class CotisationsPanel(GPanel):
    def __init__(self, parent, profil, creche, inscrits):
        GPanel.__init__(self, parent, "Cotisations")
        self.profil = profil
        self.creche = creche
        self.inscrits = inscrits

        wx.StaticBox(self, -1, u'Edition des appels de cotisation', pos=(5, 35), size=(600, 75))
        self.choice = wxChoice(self, -1, pos=(20, 60), size=(200, 30))
        self.monthchoice = wxChoice(self, -1, pos=(240, 60), size=(200, 30))
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
        self.choice.Append('Toutes les cotisations', self.inscrits)
        # Ceux qui sont presents
        for inscrit in self.inscrits:
            if inscrit.getInscription(datetime.date.today()) != None:
                self.choice.Append(GetInscritId(inscrit, self.inscrits), inscrit)
        self.choice.Append(50 * '-', None)
        # Les autres
        for inscrit in self.inscrits:
            if inscrit.getInscription(datetime.date.today()) == None:
                self.choice.Append(GetInscritId(inscrit, self.inscrits), inscrit)
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
                for inscrit in self.inscrits:
                    if inscrit.getInscription(periode) != None: # TODO cotisations ...
                        try:
                            GenereFacture(self.creche, inscrit, periode, '%s/Cotisation %s %s %d.odt' % (oopath, inscrit.prenom, months[periode.month - 1], periode.year))
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
                    GenereFacture(self.creche, inscrit, periode, oofilename)
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
          GenereFacture(creche, inscrit, datetime.date(2005, 12, 1), 'basile.ods')



