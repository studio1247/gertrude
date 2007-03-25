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
import wx
import wx.lib.scrolledpanel
import wx.html
from common import *
from planning import GPanel
from controls import *
from cotisation import CotisationException
from facture import Facture
from ooffice import *

def getPleinTempsIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                periode_reference = inscription.periode_reference
                for jour in periode_reference:
                    if jour != [1, 1, 1]:
                        break
                else:
                    result.append(i)
    return result

def getMiTempsIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                periode_reference = inscription.periode_reference
                nb_jours = 0
                for jour in periode_reference:
                    if jour == [1, 1, 1]:
                        nb_jours += 1
                if nb_jours != 5:
                    result.append(i)
    return result

def getCrecheIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                result.append(i)
    return result

def getHalteGarderieIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) and inscriptions[0].mode == 1:
            result.append(i)
    return result

def getAdaptationIndexes(date_debut, date_fin):
    result = []
    return result


def getTriParCommuneEtNomIndexes(indexes):
    # Tri par commune (Rennes en premier) + ordre alphabetique des noms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        if (i1.ville.lower() != 'rennes' and i2.ville.lower() == 'rennes'):
            return 1
        elif (i1.ville.lower() == 'rennes' and i2.ville.lower() != 'rennes'):
            return -1
        else:
            return cmp("%s %s" % (i1.nom, i1.prenom), "%s %s" % (i2.nom, i2.prenom))

    indexes.sort(tri)
    return indexes

def getTriParPrenomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        return cmp(i1.prenom, i2.prenom)

    indexes.sort(tri)
    return indexes

def getTriParNomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        return cmp(i1.nom, i2.nom)

    indexes.sort(tri)
    return indexes

def getPresentsIndexes(indexes, (debut, fin)):
    result = []
    for i in range(len(indexes)):
        inscrit = creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if ((inscription.fin == None or inscription.fin >= debut) and (inscription.debut != None and inscription.debut <= fin)):
                result.append(indexes[i])
                break

    return result

#def PresencesEffectives(inscrit, annee, mois):
#  date = datetime.date(annee, mois, 1)
#  while (date.month == mois):
#    if (date.weekday() < 5):
#      periode = GetPeriode(inscrit, date)
#      if (periode != None):
#        if date in inscrit.presences:
#          heures[inscrit.mode[periode]][j] += inscrit.presences[date].Total()
#        else:
#          presence = GetPresenceFromSemaineType(inscrit, date)
#          heures[inscrit.mode[periode]][j] += presence.Total()
#          if (presence.value == 0):
#            previsionnel[inscrit.mode[periode]][j] = 1
#    date += datetime.timedelta(1)

class EtatsTrimestrielsModifications(object):
    def __init__(self, annee):
        self.annee = annee
        self.factures = {}
        self.errors = {}

    def execute(self, dom):
        nb_cellules = 13
        premiere_ligne = 4
        nb_lignes = 8
        nb_pages = 3

        global_indexes = getTriParCommuneEtNomIndexes(range(len(creche.inscrits)))

        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        tables = spreadsheet.getElementsByTagName("table:table")

        # LES 4 TRIMESTRES
        template = tables.item(1)
        spreadsheet.removeChild(template)
        for trimestre in range(4):
        # On retire ceux qui ne sont pas inscrits pendant la periode qui nous interesse
            debut = datetime.date(self.annee, trimestre * 3 + 1, 1)
            if trimestre == 3:
                fin = datetime.date(self.annee, 12, 31)
            else:
                fin = datetime.date(self.annee, trimestre * 3 + 4, 1) - datetime.timedelta(1)
            indexes = getPresentsIndexes(global_indexes, (debut, fin))

            table = template.cloneNode(1)
            spreadsheet.appendChild(table)
            table.setAttribute("table:name", "%s tr %d" % (trimestres[trimestre], self.annee))
            lignes = table.getElementsByTagName("table:table-row")

            # Les titres des pages
            ReplaceFields(lignes.item(0), {'annee': self.annee,
                                        'trimestre': trimestres[trimestre].upper()})
            # Les mois
            ReplaceFields(lignes.item(2), {'mois(1)': months[trimestre * 3].upper(),
                                        'mois(2)': months[(trimestre * 3) + 1].upper(),
                                        'mois(3)': months[(trimestre * 3) + 2].upper()})

            for page in range(nb_pages):
                for i in range(nb_lignes):
                    ligne = lignes.item(premiere_ligne + i)
                    cellules = ligne.getElementsByTagName("table:table-cell")
                    index = page * nb_lignes + i
                    heures = [[0] * 3, [0] * 3]
                    previsionnel = [0] * 3

                    if index < len(indexes):
                        inscrit = creche.inscrits[indexes[index]]

                        # Calcul du nombre d'heures pour chaque mois
                        for i in range(3):
                            mois = trimestre * 3 + i + 1
                            try:
                                facture = self.get_facture(inscrit, mois)
                            except:
                                continue
                            previsionnel[i] = facture.previsionnel
                            heures[MODE_CRECHE][i] = facture.detail_heures_facturees[MODE_CRECHE]
                            heures[MODE_HALTE_GARDERIE][i] = facture.detail_heures_facturees[MODE_HALTE_GARDERIE]

                        fields = {'nom': inscrit.nom,
                                'prenom': inscrit.prenom,
                                'adresse': inscrit.adresse,
                                'ville': inscrit.ville,
                                'code_postal': str(inscrit.code_postal),
                                'naissance': inscrit.naissance,
                                'entree': inscrit.inscriptions[0].debut,
                                'sortie': inscrit.inscriptions[-1].fin}

                        for m, mode in enumerate(["creche", "halte"]):
                                for i in range(3):
                                    if heures[m][i] == 0:
                                        fields['%s(%d)' % (mode, i+1)] = ''
                                    elif previsionnel[m]:
                                        fields['%s(%d)' % (mode, i+1)] = '(%d)' % heures[m][i]
                                    else:
                                        fields['%s(%d)' % (mode, i+1)] = heures[m][i]
                    else:
                        fields = {}

                    ReplaceFields(cellules[page * nb_cellules : (page + 1) * nb_cellules], fields)

        # LA SYNTHESE ANNUELLE
        table = tables.item(0)
        debut = datetime.date(self.annee, 1, 1)
        fin = datetime.date(self.annee, 12, 31)
        lignes = table.getElementsByTagName("table:table-row")

        # Les inscrits en creche
        indexes = getCrecheIndexes(debut, fin)
        self.Synthese(table, lignes, indexes, MODE_CRECHE, 'creche', 0)
        # Les inscrits en halte-garderie
        indexes = getHalteGarderieIndexes(debut, fin)
        self.Synthese(table, lignes, indexes, MODE_HALTE_GARDERIE, 'halte', 6)

        if len(self.errors) > 0:
            raise CotisationException(self.errors)

    def get_facture(self, inscrit, annee, mois):
        if (inscrit.idx, mois) not in self.factures:
            try:
                self.factures[inscrit.idx, mois] = Facture(inscrit, annee, mois)
            except CotisationException, e:
                if not (inscrit.prenom, inscrit.nom) in self.errors:
                    self.errors[(inscrit.prenom, inscrit.nom)] = set(e.errors)
                else:
                    self.errors[(inscrit.prenom, inscrit.nom)].update(e.errors)
                raise
        return self.factures[inscrit.idx, mois]

    def Synthese(self, table, lignes, indexes, mode, str_mode, premiere_ligne):
        indexes = getTriParNomIndexes(indexes)

        # Le titre
        ReplaceFields(lignes.item(premiere_ligne), {'annee': self.annee})

        # Les mois
        fields = {}
        for mois in range(12):
            fields['mois(%d)' % (mois+1)] = months_abbrev[mois].upper()
        ReplaceFields(lignes.item(premiere_ligne+2), fields)

        # Les valeurs
        template = lignes.item(premiere_ligne+3)
        #print template.toprettyxml()
        total = [0] * 12
        total_previsionnel = [0] * 12
        for i in range(len(indexes)):
            inscrit = creche.inscrits[indexes[i]]
            ligne = template.cloneNode(1)
            table.insertBefore(ligne, template)

            heures = [0] * 12
            previsionnel = [0] * 12

            # Calcul du nombre d'heures pour chaque mois
            for mois in range(12):
                try:
                    facture = self.get_facture(inscrit, mois+1)
                except:
                    continue
                heures[mois], previsionnel[mois] = facture.detail_heures_facturees[mode], facture.previsionnel
                total[mois] += heures[mois]
                total_previsionnel[mois] += previsionnel[mois]

            fields = {'nom': inscrit.nom,
                    'prenom': inscrit.prenom,
                    'adresse': inscrit.adresse,
                    'ville': inscrit.ville,
                    'code_postal': str(inscrit.code_postal),
                    'naissance': inscrit.naissance,
                    'entree': inscrit.inscriptions[0].debut,
                    'sortie': inscrit.inscriptions[-1].fin}

            for mois in range(12):
                if heures[mois] == 0:
                    fields['%s(%d)' % (str_mode, mois+1)] = ''
                elif previsionnel[mois]:
                    fields['%s(%d)' % (str_mode, mois+1)] = '(%d)' % heures[mois]
                else:
                    fields['%s(%d)' % (str_mode, mois+1)] = heures[mois]

            if sum(previsionnel):
                fields['total_enfant'] = '(%d)' % sum(heures)
            else:
                fields['total_enfant'] = sum(heures)
            ReplaceFields(ligne, fields)
        table.removeChild(template)

        # Les totaux des mois
        ligne = lignes.item(premiere_ligne+4)
        fields = {}
        for mois in range(12):
            if total_previsionnel[mois]:
                fields['total(%d)' % (mois+1)] = '(%s)' % total[mois]
            else:
                fields['total(%d)' % (mois+1)] = total[mois]
            if sum(total_previsionnel):
                fields['total'] = '(%s)' % sum(total)
            else:
                fields['total'] = sum(total)
        ReplaceFields(ligne, fields)


class PlanningModifications(object):
    def __init__(self, debut):
        self.debut = debut

    def execute(self, dom):
        date_fin = self.debut + datetime.timedelta(11)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        tables = spreadsheet.getElementsByTagName("table:table")
        template = tables.item(0)
        template.setAttribute('table:name', '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

        lignes = template.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes.item(0), {'date_debut': self.debut,
                                    'date_fin': date_fin})

        # Les jours
        ligne = lignes.item(1)
        cellules = ligne.getElementsByTagName("table:table-cell")
        for semaine in range(2):
            for jour in range(5):
                date = self.debut + datetime.timedelta(semaine * 7 + jour)
                cellule = cellules.item(1 + semaine * 6 + jour)
                ReplaceFields([cellule], {'date': date})

        ligne_total = lignes.item(19)

        # Les enfants en adaptation
        indexes = getAdaptationIndexes(self.debut, date_fin)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 15)
        nb_ad = max(2, len(indexes))

        # Les halte-garderie
        indexes = getHalteGarderieIndexes(self.debut, date_fin)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 11)
        nb_hg = max(2, len(indexes))

        # Les mi-temps
        indexes = getMiTempsIndexes(self.debut, date_fin)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 7)
        nb_45 = max(2, len(indexes))

        # Les plein-temps
        indexes = getPleinTempsIndexes(self.debut, date_fin)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 3)
        nb_55 = max(2, len(indexes))

        cellules = ligne_total.getElementsByTagName("table:table-cell")
        for i in range(cellules.length):
            cellule = cellules.item(i)
            if (cellule.hasAttribute('table:formula')):
                formule = cellule.getAttribute('table:formula')
                formule = formule.replace('18', '%d' % (3+nb_55+1+nb_45+1+nb_hg+1+nb_ad))
                cellule.setAttribute('table:formula', formule)

        #print dom.toprettyxml()

    def printPresences(self, dom, indexes, ligne_depart):
        lignes = dom.getElementsByTagName("table:table-row")
        nb_lignes = 3
        if len(indexes) > 3:
            for i in range(3, len(indexes)):
                dom.insertBefore(lignes.item(ligne_depart+1).cloneNode(1), lignes.item(ligne_depart+2))
            nb_lignes = len(indexes)
        elif len(indexes) < 3:
            dom.removeChild(lignes.item(ligne_depart+1))
            nb_lignes = 2
        lignes = dom.getElementsByTagName("table:table-row")
        for i in range(nb_lignes):
            if (i < len(indexes)):
                inscrit = creche.inscrits[indexes[i]]
            else:
                inscrit = None
            ligne = lignes.item(ligne_depart + i)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for semaine in range(2):
                # le prenom
                cellule = cellules.item(semaine * 17)
                if inscrit:
                    ReplaceFields([cellule], {'prenom': inscrit.prenom})
                else:
                    ReplaceFields([cellule], {'prenom': ''})
                # les presences
                for jour in range(5):
                    date = self.debut + datetime.timedelta(semaine * 7 + jour)
                    if inscrit:
                        if date in inscrit.presences:
                            presence = inscrit.presences[date]
                        else:
                            presence = inscrit.getPresenceFromSemaineType(date)
                    for tranche in range(3):
                        cellule = cellules.item(1 + semaine * 17 + jour * 3 + tranche)
                        if inscrit:
                            ReplaceFields([cellule], {'p': int(presence.isPresentDuringTranche(tranche))})
                        else:
                            ReplaceFields([cellule], {'p': ''})

def GenereEtatsTrimestriels(annee, oofilename):
    GenerateDocument('./templates/Etats trimestriels.ods', oofilename, EtatsTrimestrielsModifications(annee))

def GenerePlanningPresences(date, oofilename):
    GenerateDocument('./templates/Planning Presences.ods', oofilename, PlanningModifications(date))

class RelevesPanel(GPanel):
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Relev�s')

        today = datetime.date.today()

        # Les releves trimestriels
        wx.StaticBox(self, -1, u'Relev�s trimestriels', pos=(5, 35), size=(400, 75))
        self.choice = wx.Choice(self, -1, pos=(20, 60), size=(270, 30))
        button = wx.Button(self, -1, u'G�n�ration', pos=(310, 60))
        for year in range(first_date.year, last_date.year + 1):
            self.choice.Append(u'Ann�e %d' % year, year)
        self.choice.SetSelection(today.year - first_date.year)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationEtatsTrimestriels, button)

        # Les plannings de presence enfants
        wx.StaticBox(self, -1, u'Planning des pr�sences', pos=(5, 130), size=(400, 75))
        self.weekchoice = wx.Choice(self, -1, pos=(20, 155), size=(270, 30))
        day = getfirstmonday()
        semaine = 1
        while day < last_date:
            string = 'Semaines %d et %d (%d %s %d)' % (semaine, semaine+1, day.day, months[day.month - 1], day.year)
            self.weekchoice.Append(string, day)
            if (day.year == (day + datetime.timedelta(14)).year):
                semaine += 2
            else:
                semaine = 1
            day += datetime.timedelta(14)
        self.weekchoice.SetSelection((today - getfirstmonday()).days / 14 + 1)
        button = wx.Button(self, -1, u'G�n�ration', pos=(310, 155))
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningPresences, button)

    def EvtGenerationEtatsTrimestriels(self, evt):
        annee = self.choice.GetClientData(self.choice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Etats trimestriels %d.ods" % annee
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'G�n�rer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                GenereEtatsTrimestriels(annee, oofilename)
                dlg = wx.MessageDialog(self, u"Document %s g�n�r�" % oofilename, 'Message', wx.OK)
            except CotisationException, e:
                message = '\n'.join(['%s %s :\n%s' % (tmp[0], tmp[1], '\n'.join(list(e.errors[tmp]))) for tmp in e.errors])
                dlg = wx.MessageDialog(self, message, 'Erreur', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def EvtGenerationPlanningPresences(self, evt):
        date = self.weekchoice.GetClientData(self.weekchoice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Planning presences %s.ods" % str(date)
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'G�n�rer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            GenerePlanningPresences(date, oofilename)
            dlg = wx.MessageDialog(self, u"Document %s g�n�r�" % oofilename, 'Message', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()

if __name__ == '__main__':
    import sys, os, __builtin__
    from datafiles import *
    __builtin__.creche = Load()
    #today = datetime.date.today()

    filename = 'etats_trimestriels_%d.ods' % (today.year - 1)
    try:
        GenereEtatsTrimestriels(today.year - 1, filename)
        print u'Fichier %s g�n�r�' % filename
    except CotisationException, e:
        print e.errors

    filename = 'planning_presences_%s.ods' % first_date
    GenerePlanningPresences(getfirstmonday(), filename)
    print u'Fichier %s g�n�r�' % filename
