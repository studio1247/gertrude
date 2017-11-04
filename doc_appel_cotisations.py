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

from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from ooffice import *


class AppelCotisationsModifications(object):
    title = "Appel de cotisations"
    template = "Appel cotisations.ods"

    def __init__(self, date, options=0):
        self.multi = False
        self.default_output = u"Appel cotisations %s %d.ods" % (months[date.month - 1], date.year)
        self.debut, self.fin = date, GetMonthEnd(date)
        self.options = options
        self.gauge = None
        self.email = None
        self.site = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet')[0]
        templates = spreadsheet.getElementsByTagName("table:table")
        template = templates[0]
                
        if len(database.creche.sites) > 1:
            spreadsheet.removeChild(template)
            for i, site in enumerate(database.creche.sites):
                table = template.cloneNode(1)
                spreadsheet.appendChild(table)
                table.setAttribute("table:name", site.nom)
                self.RemplitFeuilleMois(table, site, errors)
                if self.gauge:
                    self.gauge.SetValue((90/len(database.creche.sites)) * (i+1))
        else:
            self.RemplitFeuilleMois(template, None, errors)
            if self.gauge:
                self.gauge.SetValue(90)
                
        if len(templates) > 1:
            self.RemplitFeuilleEnfants(templates[1], errors)
            
        return errors

    def RemplitFeuilleMois(self, table, site=None, errors={}):
        lignes = table.getElementsByTagName("table:table-row")
            
        # La date
        fields = [('date', self.debut)]
        if site:
            fields.append(('site', site.nom))
        else:
            fields.append(('site', None))
        ReplaceFields(lignes, fields)
        
        inscrits = list(database.creche.select_inscrits(self.debut, self.fin, site=site))
        inscrits.sort(key=lambda x: GetPrenomNom(x))
        
        # Les cotisations
        lines_template = [lignes.item(7), lignes.item(8)]
        for i, inscrit in enumerate(inscrits):
            if self.gauge:
                self.gauge.SetValue(10+int(80.0*i/len(inscrits)))
            line = lines_template[i % 2].cloneNode(1)
            try:
                facture = Facture(inscrit, self.debut.year, self.debut.month, self.options)
                commentaire = None
            except CotisationException as e:
                facture = None
                commentaire = '\n'.join(e.errors)
                errors[GetPrenomNom(inscrit)] = e.errors
                
            fields = GetCrecheFields(database.creche) + GetInscritFields(inscrit) + GetFactureFields(facture) + GetReglementFields(inscrit.famille, self.debut.year, self.debut.month) + [('commentaire', commentaire)]
            ReplaceFields(line, fields)
            
            table.insertBefore(line, lines_template[0])
            IncrementFormulas(lines_template[i % 2], row=+2)

        table.removeChild(lines_template[0])
        table.removeChild(lines_template[1])
        
    def RemplitFeuilleEnfants(self, template, errors):
        inscrits = list(database.creche.select_inscrits(self.debut, self.fin))
        inscrits.sort(cmp=lambda x,y: cmp(GetPrenomNom(x), GetPrenomNom(y)))
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
                        errors[GetPrenomNom(inscrit)] = e.errors
                        continue
                    fields = inscrit_fields + GetFactureFields(facture) + GetReglementFields(inscrit.famille, self.debut.year, mois) + [('commentaire', commentaire)]
                    mois += 1
                else:
                    fields = inscrit_fields
                ReplaceFields(clone, fields)
                template.insertBefore(clone, lines_template[0])
            for line in lines_template:
                IncrementFormulas(line, row=+7 + mois)
            
        for line in lines_template:
            template.removeChild(line)
