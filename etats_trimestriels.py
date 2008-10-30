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

class EtatsTrimestrielsModifications(object):
    def __init__(self, annee):
        self.annee = annee
        self.factures = {}
        self.errors = {}

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            fields = [('nom-creche', creche.nom),
                      ('adresse-creche', creche.adresse),
                      ('code-postal-creche', str(creche.code_postal)),
                      ('ville-creche', creche.ville),
                      ('capacite', creche.capacite),
                     ]
            ReplaceTextFields(dom, fields)
            return []
        
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
            debut = datetime.date(self.annee, trimestre * 3 + 1, 1)
            if debut > today:
                break

            if trimestre == 3:
                fin = datetime.date(self.annee, 12, 31)
            else:
                fin = datetime.date(self.annee, trimestre * 3 + 4, 1) - datetime.timedelta(1)

	    # On retire ceux qui ne sont pas inscrits pendant la periode qui nous interesse
            indexes = getPresentsIndexes(global_indexes, (debut, fin))

            table = template.cloneNode(1)
            spreadsheet.appendChild(table)
            table.setAttribute("table:name", "%s tr %d" % (trimestres[trimestre], self.annee))
            lignes = table.getElementsByTagName("table:table-row")

            # Les titres des pages
            ReplaceFields(lignes.item(0), [('annee', self.annee),
                                           ('trimestre', trimestres[trimestre].upper())])
            # Les mois
            ReplaceFields(lignes.item(2), [('mois(1)', months[trimestre * 3].upper()),
                                           ('mois(2)', months[(trimestre * 3) + 1].upper()),
                                           ('mois(3)', months[(trimestre * 3) + 2].upper())])

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
                            heures[0][i] = facture.detail_heures_facturees[0]
                            heures[1][i] = facture.detail_heures_facturees[1]

                        fields = [('nom', inscrit.nom),
                                  ('prenom', inscrit.prenom),
                                  ('adresse', inscrit.adresse),
                                  ('ville', inscrit.ville),
                                  ('code_postal', str(inscrit.code_postal)),
                                  ('naissance', inscrit.naissance),
                                  ('entree', inscrit.inscriptions[0].debut),
                                  ('sortie', inscrit.inscriptions[-1].fin)]

                        for m, mode in enumerate(["creche", "halte"]):
                            for i in range(3):
                                if heures[m][i] == 0:
                                    fields.append(('%s(%d)' % (mode, i+1), ''))
                                # elif getMonthEnd(datetime.date(self.annee, trimestre * 3 + i + 1, 1)) > today or (creche.presences_previsionnelles and previsionnel[m]):
                                #     fields.append(('%s(%d)' % (mode, i+1), '(%d)' % heures[m][i]))
                                else:
                                    fields.append(('%s(%d)' % (mode, i+1), heures[m][i]))
                    else:
                        fields = [(tmp, '') for tmp in ('nom', 'prenom', 'adresse', 'ville', 'code_postal', 'naissance', 'entree', 'sortie')]
                        for mode in ["creche", "halte"]:
                            for i in range(3):
                                fields.append(('%s(%d)' % (mode, i+1), ''))

                    ReplaceFields(cellules[page * nb_cellules : (page + 1) * nb_cellules], fields)

        # LA SYNTHESE ANNUELLE
        table = tables.item(0)
        if datetime.date(self.annee, 9, 1) < today:       
            debut = datetime.date(self.annee, 1, 1)
            fin = datetime.date(self.annee, 12, 31)
            if debut < today:
                lignes = table.getElementsByTagName("table:table-row")

                # Les inscrits en creche
                indexes = getInscritsByMode(debut, fin, MODE_5_5|MODE_4_5|MODE_3_5)
                self.Synthese(table, lignes, indexes, MODE_CRECHE, 'creche', 0)
                # Les inscrits en halte-garderie
                indexes = getInscritsByMode(debut, fin, MODE_HALTE_GARDERIE)
                self.Synthese(table, lignes, indexes, MODE_HALTE_GARDERIE, 'halte', 6)
        else:
            spreadsheet.removeChild(table)

        if len(self.errors) > 0:
            raise CotisationException(self.errors)

        return []

    def get_facture(self, inscrit, mois):
        if (inscrit.idx, mois) not in self.factures:
            try:
                self.factures[inscrit.idx, mois] = Facture(inscrit, self.annee, mois, options=NO_REVENUS)
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
        ReplaceFields(lignes.item(premiere_ligne), [('annee', self.annee)])

        # Les mois
        fields = [('mois(%d)' % (mois+1), months_abbrev[mois].upper()) for mois in range(12)]
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

            fields = [('nom', inscrit.nom),
                      ('prenom', inscrit.prenom),
                      ('adresse', inscrit.adresse),
                      ('ville', inscrit.ville),
                      ('code_postal', str(inscrit.code_postal)),
                      ('naissance', inscrit.naissance),
                      ('entree', inscrit.inscriptions[0].debut),
                      ('sortie', inscrit.inscriptions[-1].fin)]

            for mois in range(12):
                if heures[mois] == 0:
                    fields.append(('%s(%d)' % (str_mode, mois+1), ''))
                elif previsionnel[mois]:
                    fields.append(('%s(%d)' % (str_mode, mois+1), '(%d)' % heures[mois]))
                else:
                    fields.append(('%s(%d)' % (str_mode, mois+1), heures[mois]))

            if sum(previsionnel):
                fields.append(('total_enfant', '(%d)' % sum(heures)))
            else:
                fields.append(('total_enfant', sum(heures)))
            ReplaceFields(ligne, fields)
        table.removeChild(template)

        # Les totaux des mois
        ligne = lignes.item(premiere_ligne+4)
        fields = []
        for mois in range(12):
            if total_previsionnel[mois]:
                fields.append(('total(%d)' % (mois+1), '(%s)' % total[mois]))
            else:
                fields.append(('total(%d)' % (mois+1), total[mois]))
            if sum(total_previsionnel):
                fields.append(('total', '(%s)' % sum(total)))
            else:
                fields.append(('total', sum(total)))
        ReplaceFields(ligne, fields)


def GenereEtatsTrimestriels(annee, oofilename):
    return GenerateDocument('./templates/Etats trimestriels.ods', oofilename, EtatsTrimestrielsModifications(annee))
