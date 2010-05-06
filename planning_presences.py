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
from cotisation import Cotisation, CotisationException
from ooffice import *

def isPresentDuringTranche(journee, tranche):
    # Tranches horaires
    tranches = [(creche.ouverture, 12), (12, 14), (14, creche.fermeture)]
    
    debut, fin = tranches[tranche]
    for i in range(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))):
        if journee.values[i]:
            return True
    return False

class PlanningModifications(object):
    def __init__(self, debut):
        self.template = 'Planning presences.ods'
        self.default_output = "Planning presences %s.ods" % str(debut)
        self.debut = debut

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        date_fin = self.debut + datetime.timedelta(11)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        tables = spreadsheet.getElementsByTagName("table:table")
        template = tables.item(0)
        template.setAttribute('table:name', '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

        lignes = template.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes.item(0), [('date-debut', self.debut),
                                       ('date-fin', date_fin)])

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
        indexes = getInscritsByMode(self.debut, date_fin, MODE_HALTE_GARDERIE)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 11)
        nb_hg = max(2, len(indexes))

        # Les mi-temps
        indexes = getInscritsByMode(self.debut, date_fin, MODE_4_5|MODE_3_5)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 7)
        nb_45 = max(2, len(indexes))

        # Les plein-temps
        indexes = getInscritsByMode(self.debut, date_fin, MODE_5_5)
        indexes = getTriParPrenomIndexes(indexes)
        self.printPresences(template, indexes, 3)
        nb_55 = max(2, len(indexes))

        cellules = ligne_total.getElementsByTagName("table:table-cell")
        for i in range(cellules.length):
            cellule = cellules.item(i)
            if (cellule.hasAttribute('table:formula')):
                formule = cellule.getAttribute('table:formula')
                formule = formule.replace('14', '%d' % (3+nb_55+1+nb_45+1+nb_hg+1))
                cellule.setAttribute('table:formula', formule)

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

