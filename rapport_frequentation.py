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

template_total_lines_count = 19
template_first_line = 4
template_lines_count = 8

class RapportFrequentationModifications(object):
    def __init__(self, annee):
        self.template = 'Rapport frequentation.ods'
        self.default_output = "Rapport frequentation %d.ods" % annee
        self.annee = annee
        self.factures = {}
        self.errors = {}
    
    def execute(self, filename, dom):
        fields = GetCrecheFields(creche)
                      
        if filename == 'styles.xml':
            ReplaceTextFields(dom, fields)
            return []

        elif filename == 'content.xml':
            ReplaceFields(dom, fields)
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
            
            inscrits_annee = {}
            jours_mois = []
    
            # les 12 mois
            template = tables.item(0)
            for mois in range(1, 13):
                debut = datetime.date(self.annee, mois, 1)
                fin = getMonthEnd(debut)
                if fin > today:
                    break
    
                inscrits = GetInscrits(debut, fin)
                inscrits.sort(lambda x, y: cmp(x.nom.lower(), y.nom.lower()))
                if not inscrits:
                    continue
                
                jours = [jour for jour in range(debut.day, fin.day+1) if datetime.date(debut.year, debut.month, jour) not in creche.jours_fermeture]
                
                table = template.cloneNode(1)
                spreadsheet.insertBefore(table, template)
                table.setAttribute("table:name", months[mois-1])
                columns = table.getElementsByTagName("table:table-column")
                column_template = columns[2]
                lines = table.getElementsByTagName("table:table-row")
                first_line = lines[0]
                line_template = lines[1]
                sum_line = lines[2]
                cell_template = line_template.getElementsByTagName("table:table-cell")[2]
                first_line_cell_template = first_line.getElementsByTagName("table:table-cell")[2]
                sum_line_cell_template = sum_line.getElementsByTagName("table:table-cell")[1]
                for jour in jours:
                    column = column_template.cloneNode(1)
                    table.insertBefore(column, column_template)
                    cell = first_line_cell_template.cloneNode(1)
                    first_line.insertBefore(cell, first_line_cell_template)
                    ReplaceFields(cell, [('jour', jour)])
                    cell = cell_template.cloneNode(1)
                    line_template.insertBefore(cell, cell_template)
                    cell = sum_line_cell_template.cloneNode(1)
                    sum_line.insertBefore(cell, sum_line_cell_template)
                table.removeChild(column_template)
                first_line.removeChild(first_line_cell_template)
                line_template.removeChild(cell_template)
                sum_line.removeChild(sum_line_cell_template)
                
                for i, inscrit in enumerate(inscrits):
                    line = line_template.cloneNode(1)
                    table.insertBefore(line, line_template)
                    ReplaceFields(line, [('prenom', inscrit.prenom),
                                         ('nom', inscrit.nom)])
                    cells = line.getElementsByTagName("table:table-cell")
                    for j, jour in enumerate(jours):
                        date = datetime.date(debut.year, debut.month, jour)
                        state, heures_reference, heures_realisees, heures_supplementaires = inscrit.getState(date)
                        heures_facturees = heures_reference + heures_supplementaires
                        if not heures_facturees:
                            heures_facturees = ""
                        if not heures_realisees:
                            heures_realisees = ""
                        ReplaceFields(cells[2+j], [('heures-realisees', heures_realisees),
                                                   ('heures-facturees', heures_facturees)])
                    total_cell = cells[len(jours)+2]
                    total_cell.setAttribute("table:formula", "of:=SUM([.C%d:.%s%d])" % (i+2, GetColumnName(1+len(jours)), i+2))
                    if i == 0:
                        IncrementFormulas(cells[len(jours)+4:], column=len(jours)-1)
                        cells[len(jours)+5].setAttribute("table:formula", "of:=COUNT([.C1:.%s1])" % GetColumnName(1+len(jours)))
                        for cell in line_template.getElementsByTagName("table:table-cell")[len(jours)+3:]:
                            line_template.removeChild(cell)
                    if not inscrit in inscrits_annee:
                        inscrits_annee[inscrit] = []
                    inscrits_annee[inscrit].append("%s.%s%d" % (months[mois-1], GetColumnName(2+len(jours)), i+2))
                table.removeChild(line_template)
                last_line = 1 + len(inscrits)
                for i, cell in enumerate(sum_line.getElementsByTagName("table:table-cell")[1:2+len(jours)]):
                    column = GetColumnName(2+i)
                    cell.setAttribute("table:formula", "of:=SUM([.%s2:.%s%d])" % (column, column, last_line))
                jours_mois.append("%s.%s2" % (months[mois-1], GetColumnName(5+len(jours))))
            spreadsheet.removeChild(template)
            
            # La recap de l'annee
            table = tables[-1]
            lines = table.getElementsByTagName("table:table-row")
            template = lines[1]
            keys = inscrits_annee.keys()
            keys.sort(lambda x, y: cmp(x.nom.lower(), y.nom.lower()))
            for i, inscrit in enumerate(keys):
                line = template.cloneNode(1)
                table.insertBefore(line, template)
                ReplaceFields(line, [('prenom', inscrit.prenom),
                                     ('nom', inscrit.nom),
                                     ('naissance', inscrit.naissance),
                                     ('ville', inscrit.ville)])
                cells = line.getElementsByTagName("table:table-cell")
                cells[4].setAttribute("table:formula", "of:=SUM(%s)" % ';'.join(["[%s]" % c for c in inscrits_annee[inscrit]]))
                if i == 0:
                    cells[7].setAttribute("table:formula", "of:=SUM(%s)" % ';'.join(["[%s]" % m for m in jours_mois]))
                    for cell in template.getElementsByTagName("table:table-cell")[5:]:
                        template.removeChild(cell)
            table.removeChild(template)
            total_cell = lines[3].getElementsByTagName("table:table-cell")[2]
            total_cell.setAttribute("table:formula", "of:=SUM([.E2:.E%d])" % (1+len(keys)))
            taux_occupation_cell = lines[5].getElementsByTagName("table:table-cell")[2]
            taux_occupation_cell.setAttribute("table:formula", "of:=E%d/G2" % (3+len(keys)))
            demi_journees_reelles_cell = lines[6].getElementsByTagName("table:table-cell")[2]
            demi_journees_reelles_cell.setAttribute("table:formula", "of:=J2*I2*C%d" % (6+len(keys)))
               
        return self.errors

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    filename = 'rapport_frequentation_%d.ods' % (today.year)
    print 'erreurs :', GenerateOODocument(RapportFrequentationModifications(today.year), filename)
    print u'Fichier %s généré' % filename
