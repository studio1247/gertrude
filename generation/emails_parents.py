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


class EmailsParentsModifications(object):
    title = "Export des adresses email"
    template = "Export adresses email.ods"

    def __init__(self, site, date, selection=EXPORT_FAMILLES_PRESENTES):
        self.multi = False
        self.site = site
        if date is None:
            self.date = today
        else:
            self.date = date
        self.selection = selection
        self.default_output = "Export adresses email.ods"
        self.gauge = None
        self.email = None
        self.site = None

    def get_familles(self):
        result = []
        for famille in database.creche.familles:
            temporalite = 0
            for inscrit in famille.inscrits:
                for inscription in inscrit.inscriptions:
                    if self.site is None or inscription.site == self.site:
                        if inscription.debut and inscription.debut > datetime.date.today():
                            temporalite = EXPORT_FAMILLES_FUTURES
                        elif inscription.fin and inscription.fin < datetime.date.today():
                            temporalite = EXPORT_FAMILLES_PARTIES
                        else:
                            temporalite = EXPORT_FAMILLES_PRESENTES
                            break
                    if temporalite == EXPORT_FAMILLES_PRESENTES:
                        break
            if temporalite & self.selection:
                result.append(famille)
        return result

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")
        template = lignes[0]

        for famille in self.get_familles():
            for parent in famille.parents:
                if parent.email:
                    ligne = template.cloneNode(1)
                    ReplaceFields(ligne, [("email", parent.email)])
                    table.insertBefore(ligne, template)
        table.removeChild(template)

        if self.gauge:
            self.gauge.SetValue(90)
        return errors
