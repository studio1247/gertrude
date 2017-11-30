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

from constants import *
from functions import *
from facture import *
from ooffice import *


class EtatPresenceModifications(object):
    template = "Etat presence.ods"
    title = "Etat de présence hebdomadaire"

    def __init__(self, site, date_debut, date_fin):
        self.multi = False
        self.site = site
        self.date_debut, self.date_fin = date_debut, date_fin
        self.default_output = "Etat presence semaines %s.ods" % GetDateString(date_debut)
        self.gauge = None
        self.email = None
        self.site = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
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
                                if timeslot.debut is not None and timeslot.value >= 0:
                                    if timeslot.debut < 13*12:
                                        matin = 1
                                    if timeslot.fin > 13.25*12:
                                        apres_midi = 1
                        total_matin += matin
                        total_apres_midi += apres_midi
                fields.append(("%d-M" % j, total_matin))
                fields.append(("%d-AM" % j, total_apres_midi))
                date += datetime.timedelta(1)
            ReplaceFields(ligne, fields)

        table.removeChild(template)
        if self.gauge:
            self.gauge.SetValue(90)
        return errors
