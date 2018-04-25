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

from globals import database
from generation.opendocument import OpenDocumentSpreadsheet
from helpers import GetDateString


class EtatPresenceSpreadsheet(OpenDocumentSpreadsheet):
    template = "Etat presence.ods"
    title = "Etat de présence hebdomadaire"

    def __init__(self, debut, fin):
        OpenDocumentSpreadsheet.__init__(self)
        self.date_debut, self.date_fin = debut, fin
        self.set_default_output("Etat presence semaines %s.ods" % GetDateString(debut))

    def modify_content(self, dom):
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")
              
        # Les champs de l'entête
        # ReplaceFields(lignes, [('date', self.date)])

        # Les lignes
        template = lignes.item(3)

        date = self.date_debut
        while date <= self.date_fin:
            ligne = template.cloneNode(1)
            table.insertBefore(ligne, template)
            fields = [("semaine", "Semaine %d" % date.isocalendar()[1])]
            for j in range(7):
                total_matin = total_apres_midi = 0
                if database.creche.is_jour_semaine_travaille(j):
                    for inscrit in database.creche.inscrits:
                        matin = apres_midi = 0
                        day = inscrit.GetJournee(date)
                        if day:
                            for timeslot in day.timeslots:
                                if timeslot.debut is not None and timeslot.is_presence():
                                    if timeslot.debut < 13*12:
                                        matin = 1
                                    if timeslot.fin > 13.25*12:
                                        apres_midi = 1
                        total_matin += matin
                        total_apres_midi += apres_midi
                fields.append(("%d-M" % j, total_matin))
                fields.append(("%d-AM" % j, total_apres_midi))
                date += datetime.timedelta(1)
            self.replace_cell_fields(ligne, fields)

        table.removeChild(template)
        return True
