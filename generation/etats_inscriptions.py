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


class EtatsInscriptionsModifications(object):
    def __init__(self, site, date):
        self.multi = False
        self.template = 'Etats inscriptions.ods'
        self.site = site
        if date is None:
            self.date = datetime.date.today()
        else:
            self.date = date
        self.default_output = "Etats inscriptions %s.ods" % GetDateString(self.date, weekday=False)
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
        ReplaceFields(lignes, [('date', self.date)])
        
        # Les lignes
        template = lignes.item(7)
        
        for inscrit in database.creche.inscrits:
            inscription = inscrit.get_inscription(self.date)
            if inscription and (not self.site or inscription.site == self.site):
                ligne = template.cloneNode(1)                        
                fields = GetInscritFields(inscrit) + GetInscriptionFields(inscription)
                ReplaceFields(ligne, fields)
                table.insertBefore(ligne, template)

        table.removeChild(template)
        if self.gauge:
            self.gauge.SetValue(90)
        return errors
