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
        self.multi = False
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
        template = spreadsheet.getElementsByTagName("table:table").item(0)
        
        if len(creche.sites) > 1:
            spreadsheet.removeChild(template)
            for i, site in enumerate(creche.sites):
                table = template.cloneNode(1)
                spreadsheet.appendChild(table)
                table.setAttribute("table:name", site.nom)
                self.fill_table(table, site, errors)
                if self.gauge:
                    self.gauge.SetValue((90/len(creche.sites)) * (i+1))
        else:
            self.fill_table(template)
            if self.gauge:
                self.gauge.SetValue(90)
        
        return errors

    def fill_table(self, table, site=None, errors={}):
        lignes = table.getElementsByTagName("table:table-row")
            
        # La date
        fields = [('date', self.debut)]
        if site:
            fields.append(('site', site.nom))
        else:
            fields.append(('site', None))
        ReplaceFields(lignes, fields)
        
        # Les cotisations
        lines_template = [lignes.item(7), lignes.item(8)]
        inscrits = GetInscrits(self.debut, self.fin, site=site)
        inscrits.sort(cmp=lambda x,y: cmp(GetPrenomNom(x), GetPrenomNom(y)))
        for i, inscrit in enumerate(inscrits):
            if self.gauge:
                self.gauge.SetValue(10+int(80.0*i/len(inscrits)))
            line = lines_template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month, self.options)
                commentaire = None
            except CotisationException, e:
                facture = None
                commentaire = '\n'.join(e.errors)
                errors[GetPrenomNom(inscrit)] = e.errors
                
            fields = GetCrecheFields(creche) + GetInscritFields(inscrit) + GetFactureFields(facture) + [('commentaire', commentaire)]            
            ReplaceFields(line, fields)
            
            table.insertBefore(line, lines_template[0])
            IncrementFormulas(lines_template[i % 2], row=+2)

        table.removeChild(lines_template[0])
        table.removeChild(lines_template[1])
