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


class ExportInscritsModifications(object):
    def __init__(self, annee):
        self.multi = False
        self.template = 'Export inscrits ALSH.ods'
        self.default_output = "Export inscrits %d.ods" % annee
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
            table = tables.item(0)

            debut = datetime.date(self.annee, 1, 1)
            fin = datetime.date(self.annee, 12, 31)

            lines = table.getElementsByTagName("table:table-row")
            title_line = lines[0]
            ReplaceFields(title_line, [("debut", debut),
                                       ("fin", fin)])

            template_line = lines[2]
            inscrits = GetInscrits(debut, fin)

            for inscrit in inscrits:
                facture_annee = None
                for month in range(12):
                    try:
                        facture = Facture(inscrit, self.annee, month + 1, NO_NUMERO)
                        if facture_annee:
                            facture_annee.jours_realises += facture.jours_realises
                            facture_annee.taux_effort = max(facture_annee.taux_effort, facture.taux_effort)
                            for value in creche.activites:
                                label = creche.activites[value].label
                                facture_annee.heures_supplement_activites[label] += facture.heures_supplement_activites[label]
                        else:
                            facture_annee = facture
                    except CotisationException, e:
                        self.errors[GetPrenomNom(inscrit)] = e.errors
                        continue

                line = template_line.cloneNode(1)
                fields = GetInscritFields(inscrit) + GetFactureFields(facture_annee)
                # print fields
                ReplaceFields(line, fields)
                # IncrementFormulas(line, row=+index)
                table.insertBefore(line, template_line)
                # index += 1

            table.removeChild(template_line)

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
