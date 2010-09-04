# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from constants import *
from functions import *
from facture import *
from cotisation import Cotisation, CotisationException
from ooffice import *

class EtatsPresenceModifications(object):
    def __init__(self, debut, fin, site, inscrit, selection):
        self.template = 'Etats presence.ods'
        self.default_output = "Etats presence"
        if site:
            self.default_output += " %s" % site.nom
        if inscrit:
            self.default_output += " %s %s" % (inscrit.prenom, inscrit.nom)
        self.default_output += ".ods"
        self.debut, self.fin, self.site, self.inscrit, self.selection = debut, fin, site, inscrit, selection
        self.gauge = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")

        # Les champs de l'entête
        ReplaceFields(lignes, [('debut', self.debut),
                               ('fin', self.fin),
                               ('critere-site', self.site.nom),
                               ('critere-inscrit', self.inscrit)])
        
        # Les lignes
        template = lignes.item(7)
        dates = self.selection.keys()
        dates.sort()
        for date in dates:
            for site, inscrit, heures in self.selection[date]:
                ligne = template.cloneNode(1)
                ReplaceFields(ligne, [('date', date),
                                      ('prenom', inscrit.prenom),
                                      ('nom', inscrit.nom),
                                      ('site', site.nom),
                                      ('heures', heures)])
                table.insertBefore(ligne, template)

        table.removeChild(template)
        if self.gauge:
            self.gauge.SetValue(90)
        return errors
