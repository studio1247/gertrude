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

from facture import *
from cotisation import CotisationException
from generation.opendocument import OpenDocumentSpreadsheet, FLAG_SUM_MAX


class AppelCotisationsSpreadsheet(OpenDocumentSpreadsheet):
    title = "Appel de cotisations"
    template = "Appel cotisations.ods"

    def __init__(self, date, options=0):
        OpenDocumentSpreadsheet.__init__(self)
        self.set_default_output("Appel cotisations %s %d.ods" % (months[date.month - 1], date.year))
        self.debut, self.fin = date, GetMonthEnd(date)
        self.options = options

    def get_custom_fields(self, facture):
        return self.get_fields_from_meta(names={"inscrit": facture.inscrit if facture else None, "famille": facture.inscrit.famille if facture else None, "facture": facture})

    def modify_content(self, dom):
        self.modify_content_bitmaps(dom)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet')[0]
        templates = spreadsheet.getElementsByTagName("table:table")
        template = templates[0]
                
        if len(database.creche.sites) > 1:
            spreadsheet.removeChild(template)
            for i, site in enumerate(database.creche.sites):
                table = template.cloneNode(1)
                spreadsheet.appendChild(table)
                table.setAttribute("table:name", site.nom)
                self.remplit_feuille_mois(table, site)
        else:
            self.remplit_feuille_mois(template, None)

        if len(templates) > 1:
            self.remplit_feuille_enfants(templates[1])
        if len(templates) > 2:
            self.remplit_feuille_mois(templates[2])
            
        return True

    def remplit_feuille_mois(self, table, site=None):
        lignes = table.getElementsByTagName("table:table-row")
            
        # La date
        fields = GetSiteFields(site) + [("date", self.debut)]
        self.replace_cell_fields(lignes, fields)
        
        inscrits = list(database.creche.select_inscrits(self.debut, self.fin, site=site))
        inscrits.sort(key=lambda x: GetPrenomNom(x))
        
        # Les cotisations
        lines_template = [lignes.item(7), lignes.item(8)]
        for i, inscrit in enumerate(inscrits):
            line = lines_template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month, self.options)
                commentaire = ""
            except CotisationException as e:
                facture = None
                commentaire = '\n'.join(e.errors)
                self.errors[GetPrenomNom(inscrit)] = e.errors

            fields = GetCrecheFields(database.creche) + GetInscritFields(inscrit) + GetFactureFields(facture) + self.get_custom_fields(facture) + GetReglementFields(inscrit.famille, self.debut.year, self.debut.month) + [('commentaire', commentaire)]
            self.replace_cell_fields(line, fields)

            table.insertBefore(line, lines_template[0])
            self.increment_formulas(lines_template[i % 2], row=+2)

        table.removeChild(lines_template[0])
        table.removeChild(lines_template[1])

        if len(lignes) >= 11:
            line_total = lignes.item(10)
            self.increment_formulas(line_total, row=+len(inscrits) - 2, flags=FLAG_SUM_MAX)

    def remplit_feuille_enfants(self, template):
        inscrits = list(database.creche.select_inscrits(self.debut, self.fin))
        inscrits.sort(key=lambda x: GetPrenomNom(x))
        lines_template = template.getElementsByTagName("table:table-row")[1:21]
        for i, inscrit in enumerate(inscrits):
            inscrit_fields = GetCrecheFields(database.creche) + GetInscritFields(inscrit)
            mois = 1
            for line in lines_template:
                clone = line.cloneNode(1)
                if "cotisation-mensuelle" in clone.toprettyxml():
                    if datetime.date(self.debut.year, mois, 1) > today:
                        continue
                    try:
                        facture = Facture(inscrit, self.debut.year, mois, self.options)
                        commentaire = None
                    except CotisationException as e:
                        self.errors[GetPrenomNom(inscrit)] = e.errors
                        continue
                    fields = inscrit_fields + GetFactureFields(facture) + GetReglementFields(inscrit.famille, self.debut.year, mois) + [('commentaire', commentaire)]
                    mois += 1
                else:
                    fields = inscrit_fields
                self.replace_cell_fields(clone, fields)
                template.insertBefore(clone, lines_template[0])
            for line in lines_template:
                self.increment_formulas(line, row=+7 + mois)
            
        for line in lines_template:
            template.removeChild(line)


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/ptits-mathlos.db")
    database.load()
    document = AppelCotisationsSpreadsheet(datetime.date.today())
    document.generate(filename="./test-%f.ods" % random.random())
    if document.errors:
        print(document.errors)
    StartLibreOffice(document.output)
