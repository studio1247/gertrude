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
            ReplaceTextFields(dom, GetCrecheFields(creche))
            return []

        elif filename == 'content.xml':
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
            template_table = tables.item(0)

            for m in range(0, 12, 2):
                debut = datetime.date(self.annee, m + 1, 1)
                fin = GetNextMonthStart(debut)
                if fin > today:
                    break
                fin = GetMonthEnd(fin)

                table = template_table.cloneNode(1)
                table.setAttribute("table:name", "%s-%s %d" % (months[m], months[m + 1], self.annee))
                spreadsheet.insertBefore(table, template_table)

                lines = table.getElementsByTagName("table:table-row")
                template_line = lines[2]
                total_line = lines[3]
                total_cell = total_line.getElementsByTagName("table:table-cell")[2]

                inscrits = GetInscrits(debut, fin)
                for i, inscrit in enumerate(inscrits):
                    line = template_line.cloneNode(1)
                    fields = GetInscritFields(inscrit)

                    try:
                        facture = Facture(inscrit, self.annee, m+1, NO_NUMERO)
                        facture2 = Facture(inscrit, self.annee, m+2, NO_NUMERO)
                        facture.jours_realises += facture2.jours_realises
                        for value in creche.activites:
                            label = creche.activites[value].label
                            facture.heures_supplement_activites[label] += facture2.heures_supplement_activites[label]
                        fields.extend(GetFactureFields(facture))
                    except CotisationException, e:
                        pass

                    # print fields
                    ReplaceFields(line, fields)
                    IncrementFormulas(line, row=+i)
                    table.insertBefore(line, template_line)
                table.removeChild(template_line)
                total_cell.setAttribute("table:formula", "of:=SUM([.R3:.R%d])" % (2+len(inscrits)))

            spreadsheet.removeChild(template_table)

        return self.errors

# if __name__ == '__main__':
#     import __builtin__, random
#     from config import *
#     from data import *
#     from functions import *
#     __builtin__.creche, result = FileConnection(DEFAULT_DATABASE).Load()
#     modifications = CompteExploitationModifications(None, 2015)
#     filename = "./test-%f.odt" % random.random()
#     errors = GenerateOODocument(modifications, filename=filename, gauge=None)
#     StartLibreOffice(filename)
