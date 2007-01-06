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

def getPleinTempsIndexes(inscrits, date_debut, date_fin):
    result = []
    for i in range(len(inscrits)):
        inscrit = inscrits[i]
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                semaine_type = inscription.semaine_type
                for jour in semaine_type:
                    if jour != [1, 1, 1]:
                        break
                else:
                    result.append(i)
    return result

def getMiTempsIndexes(inscrits, date_debut, date_fin):
    result = []
    for i in range(len(inscrits)):
        inscrit = inscrits[i]
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                semaine_type = inscription.semaine_type
                nb_jours = 0
                for jour in semaine_type:
                    if jour == [1, 1, 1]:
                        nb_jours += 1
                if (nb_jours != 5):
                    result.append(i)
    return result

def getCrecheIndexes(inscrits, date_debut, date_fin):
    result = []
    for i in range(len(inscrits)):
        inscrit = inscrits[i]
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                result.append(i)
    return result

def getHalteGarderieIndexes(inscrits, date_debut, date_fin):
    result = []
    for i in range(len(inscrits)):
        inscrit = inscrits[i]
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) and inscriptions[0].mode == 1:
            result.append(i)
    return result

def getAdaptationIndexes(inscrits, date_debut, date_fin):
    result = []
    for i in range(len(inscrits)):
        inscrit = inscrits[i]
    return result


def getTriParCommuneEtNomIndexes(indexes, inscrits):
    # Tri par commune (Rennes en premier) + ordre alphabetique des noms
    def tri(one, two):
        i1 = inscrits[one] ; i2 = inscrits[two]
        if (i1.ville.lower() != 'rennes' and i2.ville.lower() == 'rennes'):
            return 1
        elif (i1.ville.lower() == 'rennes' and i2.ville.lower() != 'rennes'):
            return -1
        else:
            return cmp("%s %s" % (i1.nom, i1.prenom), "%s %s" % (i2.nom, i2.prenom))

    indexes.sort(tri)
    return indexes

def getTriParPrenomIndexes(indexes, inscrits):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = inscrits[one] ; i2 = inscrits[two]
        return cmp(i1.prenom, i2.prenom)

    indexes.sort(tri)
    return indexes

def getTriParNomIndexes(indexes, inscrits):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = inscrits[one] ; i2 = inscrits[two]
        return cmp(i1.nom, i2.nom)

    indexes.sort(tri)
    return indexes

def getPresentsIndexes(indexes, inscrits, (debut, fin)):
    result = []
    for i in range(len(indexes)):
        inscrit = inscrits[indexes[i]]
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

def ReplaceFields(cellules, values):
    # Si l'argument est une ligne ...
    if cellules.__class__ == xml.dom.minidom.Element:
        cellules = cellules.getElementsByTagName("table:table-cell")
    # Fonction ...
    for cellule in cellules:
        for tag in cellule.getElementsByTagName("text:p"):
            text = tag.firstChild.wholeText
            if '[' in text and ']' in text:
                for key in values.keys():
                    if '[%s]' % key in text:
                        if values[key] is None:
                            text = text.replace('[%s]' % key, '')
                        elif type(values[key]) == int:
                            if text == '[%s]' % key:
                                cellule.setAttribute("office:value-type", 'float')
                                cellule.setAttribute("office:value", '%d' % values[key])
                            text = text.replace('[%s]' % key, str(values[key]))
                        elif type(values[key]) == datetime.date:
                            date = values[key]
                            if text == '[%s]' % key:
                                cellule.setAttribute("office:value-type", 'date')
                                cellule.setAttribute("office:date-value", '%d-%d-%d' % (date.year, date.month, date.day))
                            text = text.replace('[%s]' % key, '%.2d/%.2d/%.4d' % (date.day, date.month, date.year))
                        else:
                            text = text.replace('[%s]' % key, values[key])

                    if '[' not in text or ']' not in text:
                        break
                else:
                    text = ''

                tag.firstChild.replaceWholeText(text)

def ReplaceEtatsTrimestrielsContent(document, inscrits, annee):
    nb_cellules = 13
    premiere_ligne = 4
    nb_lignes = 8
    nb_pages = 3

    global_indexes = getTriParCommuneEtNomIndexes(range(len(inscrits)), inscrits)

    dom = xml.dom.minidom.parseString(document)
    spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
    tables = spreadsheet.getElementsByTagName("table:table")

    # LES 4 TRIMESTRES
    template = tables.item(1)
    spreadsheet.removeChild(template)
    for trimestre in range(4):
    # On retire ceux qui ne sont pas inscrits pendant la periode qui nous interesse
        debut = datetime.date(annee, trimestre * 3 + 1, 1)
        if trimestre == 3:
            fin = datetime.date(annee, 12, 31)
        else:
            fin = datetime.date(annee, trimestre * 3 + 4, 1) - datetime.timedelta(1)
        indexes = getPresentsIndexes(global_indexes, inscrits, (debut, fin))

        table = template.cloneNode(1)
        spreadsheet.appendChild(table)
        table.setAttribute("table:name", "%s tr %d" % (trimestres[trimestre], annee))
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes.item(0), {'annee': annee,
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
                previsionnel = [[0] * 3, [0] * 3]

                if index < len(indexes):
                    inscrit = inscrits[indexes[index]]

                    # Calcul du nombre d'heures pour chaque mois
                    for m in range(3):
                        mois = trimestre * 3 + m + 1
                        heures[0][m], previsionnel[0][m] = inscrit.getTotalHeuresMois(annee, mois, 0)
                        heures[1][m], previsionnel[1][m] = inscrit.getTotalHeuresMois(annee, mois, 1)

                        fields = {'nom': inscrit.nom,
                                  'prenom': inscrit.prenom,
                                  'adresse': inscrit.adresse,
                                  'ville': inscrit.ville,
                                  'code_postal': str(inscrit.code_postal),
                                  'naissance': inscrit.naissance,
                                  'entree': inscrit.inscriptions[0].debut,
                                  'sortie': inscrit.inscriptions[-1].fin}

                        for m, mode in enumerate(["creche", "halte"]):
                            for j in range(3):
                                if heures[m][j] == 0:
                                    fields['%s(%d)' % (mode, j+1)] = ''
                                elif previsionnel[m][j]:
                                    fields['%s(%d)' % (mode, j+1)] = '(%d)' % heures[m][j]
                                else:
                                    fields['%s(%d)' % (mode, j+1)] = heures[m][j]
                else:
                    fields = {}

                ReplaceFields(cellules[page * nb_cellules : (page + 1) * nb_cellules], fields)

    # LA SYNTHESE ANNUELLE
    table = tables.item(0)
    debut = datetime.date(annee, 1, 1)
    fin = datetime.date(annee, 12, 31)
    lignes = table.getElementsByTagName("table:table-row")

    def Synthese(indexes, mode, str_mode, premiere_ligne):
        indexes = getTriParNomIndexes(indexes, inscrits)

        # Le titre
        ReplaceFields(lignes.item(premiere_ligne), {'annee': annee})

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
            inscrit = inscrits[indexes[i]]
            ligne = template.cloneNode(1)
            table.insertBefore(ligne, template)

            heures = [0] * 12
            previsionnel = [0] * 12

            # Calcul du nombre d'heures pour chaque mois
            for m in range(12):
                heures[m], previsionnel[m] = inscrit.getTotalHeuresMois(annee, m+1, mode)
                total[m] += heures[m]
                total_previsionnel[m] += previsionnel[m]

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

    # Les inscrits en creche
    indexes = getCrecheIndexes(inscrits, debut, fin)
    Synthese(indexes, MODE_CRECHE, 'creche', 0)
    # Les inscrits en halte-garderie
    indexes = getHalteGarderieIndexes(inscrits, debut, fin)
    Synthese(indexes, MODE_HALTE_GARDERIE, 'halte', 6)

    #print dom.toprettyxml()
    return dom.toxml('UTF-8')

def ReplacePlanningPresencesContent(document, inscrits, date_debut):
    date_fin = date_debut + datetime.timedelta(11)

    dom = xml.dom.minidom.parseString(document)
    spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
    tables = spreadsheet.getElementsByTagName("table:table")
    template = tables.item(0)
    template.setAttribute('table:name', '%d %s %d - %d %s %d' % (date_debut.day, months[date_debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

    lignes = template.getElementsByTagName("table:table-row")

    # Les titres des pages
    ReplaceFields(lignes.item(0), {'date_debut': date_debut,
                                   'date_fin': date_fin})

    # Les jours
    ligne = lignes.item(1)
    cellules = ligne.getElementsByTagName("table:table-cell")
    for semaine in range(2):
        for jour in range(5):
            date = date_debut + datetime.timedelta(semaine * 7 + jour)
            cellule = cellules.item(1 + semaine * 6 + jour)
            ReplaceFields([cellule], {'date': date})

    def printPresences(indexes, ligne_depart):
        lignes = template.getElementsByTagName("table:table-row")
        nb_lignes = 3
        if len(indexes) > 3:
            for i in range(3, len(indexes)):
                template.insertBefore(lignes.item(ligne_depart+1).cloneNode(1), lignes.item(ligne_depart+2))
            nb_lignes = len(indexes)
        elif len(indexes) < 3:
            template.removeChild(lignes.item(ligne_depart+1))
            nb_lignes = 2
        lignes = template.getElementsByTagName("table:table-row")
        for i in range(nb_lignes):
            if (i < len(indexes)):
                inscrit = inscrits[indexes[i]]
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
                    date = date_debut + datetime.timedelta(semaine * 7 + jour)
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

    ligne_total = lignes.item(19)

    # Les enfants en adaptation
    indexes = getAdaptationIndexes(inscrits, date_debut, date_fin)
    indexes = getTriParPrenomIndexes(indexes, inscrits)
    printPresences(indexes, 15)
    nb_ad = max(2, len(indexes))

    # Les halte-garderie
    indexes = getHalteGarderieIndexes(inscrits, date_debut, date_fin)
    indexes = getTriParPrenomIndexes(indexes, inscrits)
    printPresences(indexes, 11)
    nb_hg = max(2, len(indexes))

    # Les mi-temps
    indexes = getMiTempsIndexes(inscrits, date_debut, date_fin)
    indexes = getTriParPrenomIndexes(indexes, inscrits)
    printPresences(indexes, 7)
    nb_45 = max(2, len(indexes))

    # Les plein-temps
    indexes = getPleinTempsIndexes(inscrits, date_debut, date_fin)
    indexes = getTriParPrenomIndexes(indexes, inscrits)
    printPresences(indexes, 3)
    nb_55 = max(2, len(indexes))

    cellules = ligne_total.getElementsByTagName("table:table-cell")
    for i in range(cellules.length):
        cellule = cellules.item(i)
        if (cellule.hasAttribute('table:formula')):
            formule = cellule.getAttribute('table:formula')
            formule = formule.replace('18', '%d' % (3+nb_55+1+nb_45+1+nb_hg+1+nb_ad))
            cellule.setAttribute('table:formula', formule)

    #print dom.toprettyxml()
    return dom.toxml('UTF-8')

def GenereEtatsTrimestriels(inscrits, annee, oofilename):
    template = zipfile.ZipFile('./templates/Etats trimestriels.ods', 'r')
    oofile = zipfile.ZipFile(oofilename, 'w')
    for filename in template.namelist():
        data = template.read(filename)
        if (filename == 'content.xml'):
            data = ReplaceEtatsTrimestrielsContent(data, inscrits, annee)
        oofile.writestr(filename, data)

    template.close()
    oofile.close()

def GenerePlanningPresences(inscrits, date, oofilename):
    template = zipfile.ZipFile('./templates/Planning Presences.ods', 'r')
    oofile = zipfile.ZipFile(oofilename, 'w')
    for filename in template.namelist():
        data = template.read(filename)
        if (filename == 'content.xml'):
            data = ReplacePlanningPresencesContent(data, inscrits, date)
        oofile.writestr(filename, data)

    template.close()
    oofile.close()

class RelevesPanel(GPanel):
    def __init__(self, parent, profil, creche, inscrits):
        GPanel.__init__(self, parent, u'Relevés')
        self.profil = profil
        self.inscrits = inscrits

        today = datetime.date.today()

        # Les releves trimestriels
        wx.StaticBox(self, -1, u'Relevés trimestriels', pos=(5, 35), size=(400, 75))
        self.choice = wxChoice(self, -1, pos=(20, 60), size=(200, 30))
        button = wx.Button(self, -1, u'Génération', pos=(240, 60))
        for year in range(first_date.year, last_date.year + 1):
            self.choice.Append(u'Année %d' % year, year)
        self.choice.SetSelection(today.year - first_date.year)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationEtatsTrimestriels, button)

        # Les plannings de presence enfants
        wx.StaticBox(self, -1, u'Planning des présences', pos=(5, 130), size=(400, 75))
        self.weekchoice = wxChoice(self, -1, pos=(20, 155), size=(200, 30))
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
        button = wx.Button(self, -1, u'Génération', pos=(240, 155))
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningPresences, button)

    def EvtGenerationEtatsTrimestriels(self, evt):
        annee = self.choice.GetClientData(self.choice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Etats trimestriels %d.ods" % annee
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            GenereEtatsTrimestriels(self.inscrits, annee, oofilename)

    def EvtGenerationPlanningPresences(self, evt):
        date = self.weekchoice.GetClientData(self.weekchoice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Planning presences %s.ods" % str(date)
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            GenerePlanningPresences(self.inscrits, date, oofilename)



if __name__ == '__main__':
    import sys, os
    from datafiles import *
    creche, inscrits = LoadFile(filename)
    #today = datetime.date.today()

    filename = 'etats_trimestriels_%d.ods' % (today.year - 1)
    GenereEtatsTrimestriels(inscrits, today.year - 1, filename)
    print u'Fichier %s généré' % filename

    filename = 'planning_presences_%s.ods' % first_date
    GenerePlanningPresences(inscrits, getfirstmonday(), filename)
    print u'Fichier %s généré' % filename
