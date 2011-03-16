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

from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from ooffice import *

def isPresentDuringTranche(journee, tranche):
    # Tranches horaires
    tranches = [(creche.ouverture, 12), (12, 14), (14, creche.fermeture)]
    
    debut, fin = tranches[tranche]
    for i in range(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))):
        if journee.values[i] > 0:
            return True
    return False

class PlanningModifications(object):
    def __init__(self, debut):
        self.template = 'Planning.ods'
        self.default_output = "Planning %s.ods" % str(debut)
        self.debut = debut
        self.metas = {"Format": 1, "Periodicite": 11}

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print meta.toprettyxml()
                name = meta.getAttribute('meta:name')
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = float(value)
                else:
                    self.metas[name] = value
            return None
        elif filename != 'content.xml':
            return None
              
        date_fin = self.debut + datetime.timedelta(self.metas["Periodicite"])
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes, [('date-debut', self.debut),
                              ('date-fin', date_fin)])

        if self.metas["Format"] == 1:
            table.setAttribute('table:name', '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

            # Les jours
            ligne = lignes.item(1)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for semaine in range(2):
                for jour in range(5):
                    date = self.debut + datetime.timedelta(semaine * 7 + jour)
                    cellule = cellules.item(1 + semaine * 6 + jour)
                    ReplaceFields([cellule], [('date', date)])
    
            ligne_total = lignes.item(15)
    
    #        # Les enfants en adaptation
    #        indexes = [] # TODO getAdaptationIndexes(self.debut, date_fin)
    #        indexes = getTriParPrenomIndexes(indexes)
    #        self.printPresences(template, indexes, 15)
    #        nb_ad = max(2, len(indexes))
    
            # Les halte-garderie
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_HALTE_GARDERIE)
            indexes = getTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 11)
            nb_hg = max(2, len(indexes))
    
            # Les mi-temps
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_4_5|MODE_3_5)
            indexes = getTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 7)
            nb_45 = max(2, len(indexes))
    
            # Les plein-temps
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_5_5)
            indexes = getTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 3)
            nb_55 = max(2, len(indexes))
    
            cellules = ligne_total.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if (cellule.hasAttribute('table:formula')):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('14', '%d' % (3+nb_55+1+nb_45+1+nb_hg+1))
                    cellule.setAttribute('table:formula', formule)
        elif self.metas["Format"] == 2:
            inscriptions = GetInscriptions(self.debut, date_fin)
            tableau = { } # par professeur
            for inscription in inscriptions:
                if inscription.professeur in tableau:
                    tableau[inscription.professeur].append(inscription)
                else:
                    tableau[inscription.professeur] = [inscription]
            def GetState(inscription, delta):
                state = inscription.inscrit.getState(self.debut + datetime.timedelta(delta))[0]
                if state <= 0:
                    return 0
                else:
                    return state & PRESENT
            template = table
            for professeur in tableau:
                table = template.cloneNode(1)
                table.setAttribute('table:name', GetPrenomNom(professeur))
                template.parentNode.insertBefore(table, template)
                ligne_template = GetRow(table, 10)
                for inscription in tableau[professeur]:
                    ligne = ligne_template.cloneNode(1)
                    fields = [('prenom', GetPrenom(inscription.inscrit)),
                              ('nom', GetNom(inscription.inscrit)),
                              ('professeur-prenom', GetPrenom(inscription.professeur)),
                              ('professeur-nom', GetNom(inscription.professeur))] 
                    for i, day in enumerate(days):
                        fields.append((day.lower(), GetState(inscription, i)))
                    ReplaceFields(ligne, fields)
                    table.insertBefore(ligne, ligne_template)
                table.removeChild(ligne_template)
            template.parentNode.removeChild(template)
        elif self.metas["Format"] == 3:
            # lecture des couleurs
            couleurs = {}
            for i, inscrit in enumerate(creche.inscrits):
                row = lignes[5+(i%40)]
                couleurs[GetPrenomNom(inscrit)] = [GetCell(row, j).getAttribute("table:style-name") for j in range(1, 5)]
            for row in lignes[5:45]:
                table.removeChild(row)
            del lignes[5:45]

            date = self.debut
            fin = self.debut + datetime.timedelta(5)
            jour = 0
            while date < fin:
                template = lignes[4+3*jour]
                lignes_presence = GetLines(date, creche.inscrits, presence=True)
                for i, presence in enumerate(lignes_presence):
                    if i == 0:
                        row = lignes[3+3*jour]
                        GetCell(row, 0).setAttribute("table:number-rows-spanned", str(len(lignes_presence)))
                    else:
                        row = template.cloneNode(1)
                        table.insertBefore(row, template)
                    nom_ecrit = False
                    for c in range(24): # 12h
                        cell = GetCell(row, c+1)
                        if IsPresentDuringTranche(presence, 7.0+c*0.5, 7.0+c*0.5+0.5):
                            if not nom_ecrit:
                                cell.setAttribute("office:value-type", "string")
                                text_node = GetCell(row, 3).childNodes[0]
                                GetCell(row, 3).removeChild(text_node)
                                ReplaceTextFields(text_node, [("nom", GetPrenomNom(presence)) ])
                                cell.appendChild(text_node)
                                nom_ecrit = True
                            cell.setAttribute("table:style-name", couleurs[presence.label][2 + (c&1)])
                        else:
                            cell.setAttribute("table:style-name", couleurs[presence.label][c&1])
                table.removeChild(template)               
                date += datetime.timedelta(1)
                jour += 1                
        
        #print dom.toprettyxml()
        return None

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
            if i < len(indexes):
                inscrit = creche.inscrits[indexes[i]]
            else:
                inscrit = None
            ligne = lignes.item(ligne_depart + i)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for semaine in range(2):
                # le prenom
                cellule = cellules.item(semaine * 17)
                if inscrit:
                    try:
                        age = (self.debut.year-inscrit.naissance.year) * 12 + self.debut.month - inscrit.naissance.month
                        if age >= 24:
                            age = '(%d ans)' % (age/12)
                        else:
                            age = '(%d mois)' % age
                    except:
                        age = '(?)'
                    ReplaceFields([cellule], [('prenom', inscrit.prenom), ('nom', inscrit.nom), ('(age)', age)])
                else:
                    ReplaceFields([cellule], [('prenom', ''), ('nom', ''), ('(age)', '')])
                # les presences
                for jour in range(5):
                    date = self.debut + datetime.timedelta(semaine * 7 + jour)
                    if inscrit:
                        if date in inscrit.journees:
                            journee = inscrit.journees[date]
                        else:
                            journee = inscrit.getReferenceDayCopy(date)
                    for tranche in range(3):
                        cellule = cellules.item(1 + semaine * 17 + jour * 3 + tranche)
                        if inscrit and journee:
                            ReplaceFields([cellule], [('p', int(isPresentDuringTranche(journee, tranche)))])
                        else:
                            ReplaceFields([cellule], [('p', '')])


if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    filename = 'planning-1.ods'
    try:
        GenerateOODocument(PlanningModifications(datetime.date(2011, 3, 14)), filename)
        print u'Fichier %s généré' % filename
    except CotisationException, e:
        print e.errors
