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
from cotisation import CotisationException
from ooffice import *

class AppelCotisationsModifications(object):
    def __init__(self, date, options=0):
        self.template = 'Appel cotisations.ods'
        self.default_output = u"Appel cotisations %s %d.ods" % (months[date.month - 1], date.year)
        self.debut, self.fin = date, getMonthEnd(date)
        self.options = options
        self.gauge = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")

        # La date
        ReplaceFields(lignes, [('date', self.debut)])
        template = [lignes.item(5), lignes.item(6)]

        # Les cotisations
        inscrits = getInscrits(self.debut, self.fin)
        for i, inscrit in enumerate(inscrits):
            if self.gauge:
                self.gauge.SetValue(10+int(80.0*i/len(inscrits)))
            line = template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month, self.options)
                cotisation, supplement = facture.cotisation_mensuelle, facture.supplement
                commentaire = None
            except CotisationException, e:
                cotisation, supplement = '?', None
                commentaire = '\n'.join(e.errors)
                errors[GetPrenomNom(inscrit)] = e.errors
            ReplaceFields(line, [('prenom', inscrit.prenom),
                                 ('cotisation', cotisation),
                                 ('supplement', supplement),
                                 ('commentaire', commentaire)])
            table.insertBefore(line, template[0])
            IncrementFormulas(template[i % 2], row=+2)

        table.removeChild(template[0])
        table.removeChild(template[1])
        if self.gauge:
            self.gauge.SetValue(90)
        return errors
