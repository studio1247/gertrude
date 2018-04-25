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

import datetime

from helpers import GetDateString, date2str
from globals import database
from functions import GetInscritFields, GetInscriptionFields
from generation.opendocument import OpenDocumentSpreadsheet


class EtatsInscriptionsSpreadsheet(OpenDocumentSpreadsheet):
    title = "Inscriptions en cours"
    template = "Etats inscriptions.ods"

    def __init__(self, site, date):
        OpenDocumentSpreadsheet.__init__(self)
        self.site = site
        self.date = date if date else datetime.date.today()
        self.set_default_output("Etats inscriptions %s.ods" % GetDateString(self.date, weekday=False))

    def modify_content(self, dom):
        OpenDocumentSpreadsheet.modify_content(self, dom)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")
              
        # Les champs de l'entête
        self.replace_cell_fields(lignes, [('date', date2str(self.date))])
        
        # Les lignes
        template = lignes.item(7)

        inscrits = sorted(database.creche.inscrits, key=lambda inscrit: (inscrit.get_groupe_order(self.date), inscrit.nom, inscrit.prenom))
        for inscrit in inscrits:
            inscription = inscrit.get_inscription(self.date)
            if inscription and (not self.site or inscription.site == self.site):
                ligne = template.cloneNode(1)                        
                fields = GetInscritFields(inscrit) + GetInscriptionFields(inscription)
                self.replace_cell_fields(ligne, fields)
                table.insertBefore(ligne, template)

        table.removeChild(template)
        return True
