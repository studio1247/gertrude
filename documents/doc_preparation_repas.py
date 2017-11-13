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

from ooffice import *


class PreparationRepasModifications(object):
    title = "Préparation des repas"
    template = "Preparation repas.ods"

    def __init__(self, debut):
        self.multi = False
        self.default_output = "Preparation repas %s.ods" % str(debut)
        self.debut = debut
        self.email = None
        self.site = None

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
              
        date_fin = self.debut + datetime.timedelta(4)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes, GetCrecheFields(database.creche) + [
            ('date-debut', self.debut),
            ('date-fin', date_fin)])

        if 1:
            # Le format utilisé par Les petits potes (séparation adaptation / halte-garderie / mi-temps / plein-temps
            # Changé en format utilisé par les petits lutins (sans la séparation)
            table.setAttribute('table:name', '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

            # Les jours
            ligne = lignes.item(1)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for jour in range(5):
                date = self.debut + datetime.timedelta(jour)
                cellule = cellules.item(2 + jour)
                ReplaceFields([cellule], [('date', date)])

            # Les lignes
            table_petits = []
            table_grands = []
            for inscrit in database.creche.select_inscrits(self.debut, date_fin):
                if GetAge(inscrit.naissance) >= 24:
                    table_grands.append(inscrit)
                else:
                    table_petits.append(inscrit)
            table_grands.sort(key=lambda x: GetPrenomNom(x))
            self.printPresences(table, table_grands, 5)
            table_petits.sort(key=lambda x: GetPrenomNom(x))
            self.printPresences(table, table_petits, 3)

            # La ligne des totaux
            ligne_total = lignes.item(7)
            cellules = ligne_total.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('7', str(4 + len(table_grands) + len(table_petits)))
                    cellule.setAttribute('table:formula', formule)

        #print dom.toprettyxml()
        return None

    def printPresences(self, dom, inscrits, ligne_depart):
        template = dom.getElementsByTagName("table:table-row")[ligne_depart]
        for inscrit in inscrits:
            line = template.cloneNode(1)
            cells = line.getElementsByTagName("table:table-cell")
            ReplaceFields(cells, GetInscritFields(inscrit))
            for i, cell in enumerate(cells):
                day = (i - 1) // 4
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
                ReplaceFields(cell, list(food_needs.items()))
            dom.insertBefore(line, template)
        dom.removeChild(template)


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/lutins-miniac.db")
    database.load()
    modifications = PreparationRepasModifications(datetime.date(2017, 11, 6))
    filename = "./test-%f.odt" % random.random()
    errors = GenerateOODocument(modifications, filename=filename, gauge=None)
    StartLibreOffice(filename)
