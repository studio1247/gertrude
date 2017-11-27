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
from generation import templates


class PlanningHebdomadaireModifications(object):
    def __init__(self, debut):
        self.debut = debut
        self.fin = self.debut + datetime.timedelta(5)
        self.multi = False
        self.email = None
        self.site = None
        self.metas = {
            "ColumnsPerHour": 2
        }

    def get_metas(self, dom):
        metas = dom.getElementsByTagName("meta:user-defined")
        for meta in metas:
            # print(meta.toprettyxml())
            name = meta.getAttribute("meta:name")
            value = meta.childNodes[0].wholeText
            if meta.getAttribute("meta:value-type") == "float":
                self.metas[name] = float(value)
            else:
                self.metas[name] = value

    def execute(self, filename, dom):
        if filename == "meta.xml":
            self.get_metas(dom)
            return None
        elif filename != "content.xml":
            return None

        hour_start = self.metas["HourStart"]
        hour_end = self.metas["HourEnd"]

        template_lines_count = int(self.metas["TemplateLinesCount"])

        first_color_line = int(self.metas["FirstColorLine"])
        last_color_line = int(self.metas["LastColorLine"])

        first_color_column = int(self.metas["FirstColorColumn"])
        columns_per_hour = int(self.metas["ColumnsPerHour"])
        column_duration = 12 // columns_per_hour
        last_color_column = first_color_column + 2 * columns_per_hour

        spreadsheet = dom.getElementsByTagName("office:spreadsheet").item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # lecture des couleurs
        couleurs = {}
        for i, person in enumerate(self.get_people()):
            line = lignes[first_color_line + (person.idx % (last_color_line - first_color_line))]
            couleurs[GetPrenomNom(person)] = []
            for j in range(first_color_column, last_color_column):
                couleurs[GetPrenomNom(person)].append(GetCell(line, j).getAttribute("table:style-name"))

        # suppression des lignes des couleurs
        for line in lignes[first_color_line:last_color_line]:
            table.removeChild(line)
        del lignes[first_color_line:last_color_line]

        template = lignes[0:template_lines_count]
        for person in self.get_people():
            lines = []
            for line in template:
                clone = line.cloneNode(1)
                lines.append(clone)
                table.insertBefore(clone, template[0])

            date = self.debut
            jour = 0
            heures_semaine = 0.0
            while date < self.fin:
                line = lines[3 + jour]
                journee = person.GetJournee(date)
                if journee:
                    hour = int(hour_start * 12)
                    c = 1
                    while hour < hour_end * 12:
                        border_column_offset = (hour // column_duration) % columns_per_hour
                        cell = GetCell(line, c)
                        if IsPresentDuringTranche(journee, hour, hour + column_duration):
                            color_column = border_column_offset
                        else:
                            color_column = columns_per_hour + border_column_offset
                        cell.setAttribute("table:style-name", couleurs[GetPrenomNom(person)][color_column])
                        SplitCellRepeat(cell)
                        hour += column_duration
                        c += 1
                    heures_jour = journee.get_duration()
                    heures_semaine += heures_jour
                    ReplaceFields(line, [
                        ('heures-jour[%d]' % jour, GetHeureString(heures_jour)),
                    ])
                date += datetime.timedelta(1)
                jour += 1

            # La ligne de titre + le total
            ReplaceFields(lines, [
                ('prenom', person.prenom),
                ('nom', person.nom),
                ('date-debut', self.debut),
                ('date-fin', self.fin),
                ('heures-semaine', GetHeureString(heures_semaine))
            ])

        for line in template:
            table.removeChild(line)

        # print(dom.toprettyxml())
        return


class PlanningHebdomadaireEnfantsModifications(PlanningHebdomadaireModifications):
    title = "Planning hebdomadaire enfants"
    template = "Planning hebdomadaire enfants.ods"

    def __init__(self, debut):
        PlanningHebdomadaireModifications.__init__(self, debut)
        self.default_output = "Planning enfants semaine %d.ods" % debut.isocalendar()[1]

    def get_people(self):
        return database.creche.select_inscrits(self.debut, self.fin)


class PlanningHebdomadaireSalariesModifications(PlanningHebdomadaireModifications):
    title = "Planning hebdomadaire salariés"
    template = "Planning hebdomadaire salaries.ods"

    def __init__(self, debut):
        PlanningHebdomadaireModifications.__init__(self, debut)
        self.default_output = "Planning salariés semaine %d.ods" % debut.isocalendar()[1]

    def get_people(self):
        return GetSalaries(self.debut, self.fin)


templates["planning"].append(PlanningHebdomadaireEnfantsModifications)
templates["planning"].append(PlanningHebdomadaireSalariesModifications)


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/monteillou.db")
    modifications = PlanningHebdomadaireEnfantsModifications(datetime.date(2017, 9, 25))
    filename = "./test-%f.odt" % random.random()
    errors = GenerateOODocument(modifications, filename=filename, gauge=None)
    StartLibreOffice(filename)
