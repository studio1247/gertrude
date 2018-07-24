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
from facture import *
from ooffice import *

template_total_lines_count = 19
template_first_line = 4
template_lines_count = 8


class ExportFacturationModifications(object):
    def __init__(self, annee):
        self.multi = False
        self.template = 'Export facturation.ods'
        self.default_output = "Export facturation %d.ods" % annee
        self.annee = annee
        self.site = None
        self.errors = {}
        self.email = None

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            ReplaceTextFields(dom, GetCrecheFields(database.creche))
            return []

        elif filename == 'content.xml':
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
            template_table = tables.item(0)

            for m in range(0, 12, 2):
                debut = datetime.date(self.annee, m + 1, 1)
                fin = GetNextMonthStart(debut)
                if fin > datetime.date.today():
                    break
                fin = GetMonthEnd(fin)

                table = template_table.cloneNode(1)
                table.setAttribute("table:name", "%s-%s %d" % (months[m], months[m + 1], self.annee))
                spreadsheet.insertBefore(table, template_table)

                lines = table.getElementsByTagName("table:table-row")
                template_line = lines[2]
                total_line = lines[3]
                total_cell = total_line.getElementsByTagName("table:table-cell")[2]

                inscrits = database.creche.select_inscrits(debut, fin)
                index = 0
                for i, inscrit in enumerate(inscrits):
                    try:
                        facture = Facture(inscrit, self.annee, m+1, NO_NUMERO)
                        if facture.total > 0:
                            facture2 = Facture(inscrit, self.annee, m+2, NO_NUMERO)
                            facture.jours_realises += facture2.jours_realises
                            for value in database.creche.activites:
                                label = database.creche.activites[value].label
                                facture.heures_supplement_activites[label] += facture2.heures_supplement_activites[label]
                        else:
                            facture = Facture(inscrit, self.annee, m+2, NO_NUMERO)
                        if facture.total == 0:
                            continue
                        line = template_line.cloneNode(1)
                        fields = GetInscritFields(inscrit) + GetFactureFields(facture)
                    except CotisationException as e:
                        self.errors[GetPrenomNom(inscrit)] = e.errors
                        continue

                    # print fields
                    ReplaceFields(line, fields)
                    IncrementFormulas(line, row=+index)
                    table.insertBefore(line, template_line)
                    index += 1

                table.removeChild(template_line)
                total_cell.setAttribute("table:formula", "of:=SUM([.R3:.R%d])" % (2+index))

            spreadsheet.removeChild(template_table)

        return self.errors
