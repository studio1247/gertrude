# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from ooffice import *

template_total_lines_count = 19
template_first_line = 4
template_lines_count = 8


class EtatsTrimestrielsModifications(object):
    def __init__(self, site, annee):
        self.multi = False
        self.template = 'Etats trimestriels.ods'
        self.default_output = "Etats trimestriels %d.ods" % annee
        self.site = site
        self.annee = annee
        self.factures = {}
        self.errors = {}
        self.email = None

    def GetPrintableValue(self, value):
        if value == 0:
            return ''
        else:
            return value

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            ReplaceTextFields(dom, GetCrecheFields(database.creche))
            return []

        elif filename == 'content.xml':
            global_indexes = GetTriParCommuneEtNomIndexes(range(len(database.creche.inscrits)))
    
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
    
            # LES 4 TRIMESTRES
            template = tables.item(1)
            spreadsheet.removeChild(template)
            for trimestre in range(4):
                debut = datetime.date(self.annee, trimestre * 3 + 1, 1)
                if debut > datetime.date.today():
                    break
    
                if trimestre == 3:
                    fin = datetime.date(self.annee, 12, 31)
                else:
                    fin = datetime.date(self.annee, trimestre * 3 + 4, 1) - datetime.timedelta(1)
    
                # On retire ceux qui ne sont pas inscrits pendant la periode qui nous interesse
                indexes = GetPresentsIndexes(global_indexes, (debut, fin), self.site)
    
                table = template.cloneNode(1)
                spreadsheet.appendChild(table)
                table.setAttribute("table:name", "%s tr %d" % (ordinaux[trimestre], self.annee))
                lines = table.getElementsByTagName("table:table-row")
                page_template = lines[:template_total_lines_count]
                last_line = lines[template_total_lines_count]
                for line in page_template:
                    table.removeChild(line)
    
                nb_pages = (len(indexes) // template_lines_count) + (len(indexes) % template_lines_count > 0)
                total = [[0, 0, 0], [0, 0, 0]]

                for page in range(nb_pages):
                    lines = []
                    for l, line in enumerate(page_template):
                        clone = line.cloneNode(1)
                        lines.append(clone)
                        table.insertBefore(clone, last_line)
                    
                    # Le titre de la page
                    ReplaceFields(lines[0], [('annee', self.annee),
                                             ('trimestre', ordinaux[trimestre].upper())])
                    # Les mois
                    ReplaceFields(lines[2], [('mois(1)', months[trimestre * 3].upper()),
                                             ('mois(2)', months[(trimestre * 3) + 1].upper()),
                                             ('mois(3)', months[(trimestre * 3) + 2].upper())])

                    sous_total = [[0, 0, 0], [0, 0, 0]]
                    
                    for l, line in enumerate(lines[template_first_line:template_first_line+template_lines_count]):
                        index = page * template_lines_count + l
                        heures = [[0] * 3, [0] * 3]
                        previsionnel = [0] * 3
    
                        if index < len(indexes):
                            inscrit = database.creche.inscrits[indexes[index]]
    
                            # Calcul du nombre d'heures pour chaque mois
                            for i in range(3):
                                mois = trimestre * 3 + i + 1
                                try:
                                    facture = self.get_facture(inscrit, mois)
                                except:
                                    continue
                                previsionnel[i] = facture.previsionnel
                                if config.options & HEURES_CONTRAT:
                                    heures[0][i] = facture.heures_facture - facture.heures_facture_par_mode[MODE_HALTE_GARDERIE]
                                    heures[1][i] = facture.heures_facture_par_mode[MODE_HALTE_GARDERIE]
                                else:
                                    heures[0][i] = facture.heures_facturees - facture.heures_facturees_par_mode[MODE_HALTE_GARDERIE]
                                    heures[1][i] = facture.heures_facturees_par_mode[MODE_HALTE_GARDERIE]
    
                            fields = GetInscritFields(inscrit)
    
                            for m, mode in enumerate(["creche", "halte"]):
                                for i in range(3):
                                    fields.append(('%s(%d)' % (mode, i+1), self.GetPrintableValue(heures[m][i])))
                                    sous_total[m][i] += heures[m][i]
                                    total[m][i] += heures[m][i]
                        else:
                            fields = [(tmp, '') for tmp in ('nom', 'prenom', 'adresse', 'ville', 'code-postal', 'naissance', 'entree', 'sortie')]
                            for mode in ["creche", "halte"]:
                                for i in range(3):
                                    fields.append(('%s(%d)' % (mode, i+1), ''))
    
                        ReplaceFields(line, fields)
                    
                    # La ligne de sous-total
                    line = lines[template_first_line+template_lines_count]
                    if "sous-total" in line.toprettyxml():
                        fields = []
                        for m, mode in enumerate(["creche", "halte"]):
                            for i in range(3):
                                fields.append(('sous-total-%s(%d)' % (mode, i+1), self.GetPrintableValue(sous_total[m][i])))
                        ReplaceFields(line, fields)
                    
                    # La ligne de total
                    line = lines[template_first_line+template_lines_count+1]
                    if "total" in line.toprettyxml():
                        if page == nb_pages-1:
                            fields = []
                            for m, mode in enumerate(["creche", "halte"]):
                                for i in range(3):
                                    fields.append(('total-%s(%d)' % (mode, i+1), self.GetPrintableValue(total[m][i])))
                            ReplaceFields(line, fields)
                        else:
                            table.removeChild(line)
                        
            # LA SYNTHESE ANNUELLE
            table = tables.item(0)
            if datetime.date(self.annee, 9, 1) < datetime.date.today():
                debut = datetime.date(self.annee, 1, 1)
                fin = datetime.date(self.annee, 12, 31)
                if debut < datetime.date.today():
                    lignes = table.getElementsByTagName("table:table-row")
                    # Les inscrits en creche
                    indexes = GetInscritsByMode(debut, fin, MODE_TEMPS_PLEIN | MODE_TEMPS_PARTIEL | MODE_FORFAIT_MENSUEL | MODE_FORFAIT_MENSUEL | MODE_FORFAIT_GLOBAL_CONTRAT, self.site)
                    self.Synthese(table, lignes, indexes, MODE_CRECHE, 'creche', 0)
                    # Les inscrits en halte-garderie
                    indexes = GetInscritsByMode(debut, fin, MODE_HALTE_GARDERIE, self.site)
                    self.Synthese(table, lignes, indexes, MODE_HALTE_GARDERIE, 'halte', 6)
            else:
                spreadsheet.removeChild(table)

        return self.errors

    def get_facture(self, inscrit, mois):
        if (inscrit.idx, mois) not in self.factures:
            try:
                self.factures[inscrit.idx, mois] = Facture(inscrit, self.annee, mois, options=NO_REVENUS|NO_NUMERO)
            except CotisationException as e:
                label = "%s %s" % (inscrit.prenom, inscrit.nom)
                if not label in self.errors:
                    self.errors[label] = set(e.errors)
                else:
                    self.errors[label].update(e.errors)
                raise
        return self.factures[inscrit.idx, mois]

    def Synthese(self, table, lignes, indexes, mode, str_mode, premiere_ligne):
        indexes = GetTriParNomIndexes(indexes)

        # Le titre
        ReplaceFields(lignes.item(premiere_ligne), [('annee', self.annee)])

        # Les mois
        fields = [('mois(%d)' % (mois + 1), months_abbrev[mois].upper()) for mois in range(12)]
        ReplaceFields(lignes.item(premiere_ligne + 2), fields)

        # Les valeurs
        template = lignes.item(premiere_ligne+3)
        #print template.toprettyxml()
        total = [0] * 12
        total_previsionnel = [0] * 12
        for i in range(len(indexes)):
            inscrit = database.creche.inscrits[indexes[i]]
            ligne = template.cloneNode(1)
            table.insertBefore(ligne, template)

            heures = [0] * 12
            previsionnel = [0] * 12

            # Calcul du nombre d'heures pour chaque mois
            for mois in range(12):
                try:
                    facture = self.get_facture(inscrit, mois + 1)
                except:
                    continue
                
                if config.options & HEURES_CONTRAT:
                    if mode == 0:
                        heures[mois] = facture.heures_facture - facture.heures_facture_par_mode[MODE_HALTE_GARDERIE]
                    else:
                        heures[mois] = facture.heures_facture_par_mode[MODE_HALTE_GARDERIE]
                else:
                    if mode == 0:
                        heures[mois] = facture.heures_facturees - facture.heures_facturees_par_mode[MODE_HALTE_GARDERIE]
                    else:
                        heures[mois] = facture.heures_facturees_par_mode[MODE_HALTE_GARDERIE]
                previsionnel[mois] = facture.previsionnel
                total[mois] += heures[mois]
                total_previsionnel[mois] += previsionnel[mois]

            fields = GetInscritFields(inscrit) + GetFamilleFields(inscrit.famille)

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
