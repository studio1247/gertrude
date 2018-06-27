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

import datetime

from globals import database
from constants import months, REPAS_PUREE, REPAS_MORCEAUX
from functions import date2str, GetCrecheFields, GetPrenomNom, GetInscritFields, IsPresentDuringTranche, GetAge
from generation.opendocument import OpenDocumentSpreadsheet


class PreparationRepasSpreadsheet(OpenDocumentSpreadsheet):
    title = "Préparation des repas"
    template = "Preparation repas.ods"

    def __init__(self, debut):
        OpenDocumentSpreadsheet.__init__(self)
        self.set_default_output("Preparation repas %s.ods" % str(debut))
        self.debut, self.fin = debut, debut + datetime.timedelta(4)

    def modify_content(self, dom):
        spreadsheet = dom.getElementsByTagName("office:spreadsheet").item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        self.replace_cell_fields(lignes, GetCrecheFields(database.creche) + [
            ('date-debut', self.debut),
            ('date-fin', self.fin)])

        table.setAttribute("table:name", '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], self.fin.year, self.fin.day, months[self.fin.month - 1], self.fin.year))

        # Les jours
        ligne = lignes.item(1)
        cellules = ligne.getElementsByTagName("table:table-cell")
        for jour in range(5):
            date = self.debut + datetime.timedelta(jour)
            cellule = cellules.item(2 + jour)
            self.replace_cell_fields([cellule], [("date", date2str(date))])

        # Les lignes
        inscrits = list(database.creche.select_inscrits(self.debut, self.fin))
        inscrits.sort(key=lambda x: GetPrenomNom(x))
        self.print_presences(table, inscrits, 3)

        # La ligne des totaux
        ligne_total = lignes.item(5)
        cellules = ligne_total.getElementsByTagName("table:table-cell")
        for i in range(cellules.length):
            cellule = cellules.item(i)
            if cellule.hasAttribute("table:formula"):
                formule = cellule.getAttribute("table:formula")
                formule = formule.replace("5", str(4 + len(inscrits)))
                cellule.setAttribute("table:formula", formule)

        # print dom.toprettyxml()
        return True

    def print_presences(self, dom, inscrits, ligne_depart):
        template = dom.getElementsByTagName("table:table-row")[ligne_depart]
        if 1:
            line = template.cloneNode(1)
            cells = line.getElementsByTagName("table:table-cell")
            self.replace_cell_fields(cells, [
                ("prenom", "Echantillon"),
                ("nom", None),
                ("age-mois", None),
                ("type-repas-2", None),
                ("lép", 70),
                ("lém", None),
                ("pr", 70),
                ("li", 70),
                ("fé", 70)
            ])
            dom.insertBefore(line, template)
        for inscrit in inscrits:
            line = template.cloneNode(1)
            cells = line.getElementsByTagName("table:table-cell")
            self.replace_cell_fields(cells, GetInscritFields(inscrit))
            for i, cell in enumerate(cells):
                day = (i - 3) // 5
                date = self.debut + datetime.timedelta(day)
                age = GetAge(inscrit.naissance, date)
                fields = [
                    "tranche_4_6",
                    "tranche_6_12",
                    "tranche_12_18",
                    "tranche_18_24",
                    "tranche_24_"]
                field = fields[min(age // 6, len(fields) - 1)]
                journee = inscrit.GetJournee(date)
                present = journee and IsPresentDuringTranche(journee, database.creche.ouverture * 12, 12.5 * 12)
                food_needs = {}
                for food_need in database.creche.food_needs:
                    quantity = getattr(food_need, field) if present else ""
                    food_needs[food_need.label[0:2].lower()] = quantity
                    food_needs[food_need.label[0:2].lower() + "p"] = quantity if inscrit.type_repas == REPAS_PUREE else ""
                    food_needs[food_need.label[0:2].lower() + "m"] = quantity if inscrit.type_repas == REPAS_MORCEAUX else ""
                self.replace_cell_fields(cell, list(food_needs.items()))
            dom.insertBefore(line, template)
        dom.removeChild(template)


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/lutins-miniac.db")
    database.load()
    document = PreparationRepasSpreadsheet(datetime.date(2017, 11, 6))
    if document.available():
        document.generate(filename="./test-%f.ods" % random.random())
        if document.errors:
            print(document.errors)
        StartLibreOffice(document.output)
