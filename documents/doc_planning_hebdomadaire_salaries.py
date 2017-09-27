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
from __future__ import print_function

from ooffice import *
from documents import templates


class PlanningHebdomadaireSalariesModifications(object):
    title = "Planning hebdomadaire salariés"
    template = "Planning hebdomadaire salaries.ods"

    def __init__(self, debut):
        self.debut = debut
        self.fin = self.debut + datetime.timedelta(5)
        self.multi = False
        self.default_output = "Planning salaries semaine %d.ods" % debut.isocalendar()[1]
        self.email = None
        self.site = None
        self.metas = {}

    def get_metas(self, dom):
        metas = dom.getElementsByTagName('meta:user-defined')
        for meta in metas:
            # print(meta.toprettyxml())
            name = meta.getAttribute('meta:name')
            value = meta.childNodes[0].wholeText
            if meta.getAttribute('meta:value-type') == 'float':
                self.metas[name] = float(value)
            else:
                self.metas[name] = value
            print(name, self.metas[name])

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            self.get_metas(dom)
            return None
        elif filename != 'content.xml':
            return None

        hour_start = self.metas["HourStart"]
        hour_end = self.metas["HourEnd"]

        template_lines_count = int(self.metas["TemplateLinesCount"])

        first_color_line = int(self.metas["FirstColorLine"])
        last_color_line = int(self.metas["LastColorLine"])

        first_color_column = int(self.metas["FirstColorColumn"])
        last_color_column = first_color_column + 4
              
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # lecture des couleurs
        couleurs = {}
        for i, salarie in enumerate(creche.salaries):
            line = lignes[first_color_line + (i % (last_color_line - first_color_line))]
            couleurs[GetPrenomNom(salarie)] = [GetCell(line, j).getAttribute("table:style-name") for j in range(first_color_column, last_color_column)]

        # suppression des lignes des couleurs
        for line in lignes[first_color_line:last_color_line]:
            table.removeChild(line)
        del lignes[first_color_line:last_color_line]

        template = lignes[0:template_lines_count]
        for salarie in GetSalaries(self.debut, self.fin):
            lines = []
            for line in template:
                clone = line.cloneNode(1)
                lines.append(clone)
                table.insertBefore(clone, template[0])

            date = self.debut
            jour = 0
            heures_semaine = 0.0
            while date < self.fin:
                line = lines[3+jour]
                journee = salarie.GetJournee(date)
                if journee:
                    for c in range(int(2*(hour_end-hour_start))):
                        hour = (hour_start + c * 0.5) * 12
                        border_column_offset = 0 if hour % 12 == 0 else 1
                        cell = GetCell(line, c + 1)
                        if IsPresentDuringTranche(journee, hour, hour+6):
                            cell.setAttribute("table:style-name", couleurs[GetPrenomNom(salarie)][2 + border_column_offset])
                        else:
                            cell.setAttribute("table:style-name", couleurs[GetPrenomNom(salarie)][0 + border_column_offset])
                    heures_jour = journee.GetNombreHeures()
                    heures_semaine += heures_jour
                    ReplaceFields(line, [
                        ('heures-jour[%d]' % jour, GetHeureString(heures_jour)),
                        ])
                date += datetime.timedelta(1)
                jour += 1

            # La ligne de titre + le total
            ReplaceFields(lines, [
                ('prenom', salarie.prenom),
                ('nom', salarie.nom),
                ('date-debut', self.debut),
                ('date-fin', self.fin),
                ('heures-semaine', GetHeureString(heures_semaine))
            ])

        for line in template:
            table.removeChild(line)

        # print(dom.toprettyxml())
        return


templates["planning"].append(PlanningHebdomadaireSalariesModifications)


if __name__ == '__main__':
    import __builtin__
    import random
    from config import *
    from data import *
    from functions import *
    __builtin__.creche, result = FileConnection("databases/monteillou.db").Load()
    modifications = PlanningHebdomadaireSalariesModifications(datetime.date(2017, 9, 25))
    filename = "./test-%f.odt" % random.random()
    errors = GenerateOODocument(modifications, filename=filename, gauge=None)
    StartLibreOffice(filename)
