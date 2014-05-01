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

class ReleveDetailleModifications(object):
    def __init__(self, site, annee):
        self.multi = False
        self.template = 'Releve detaille.ods'
        self.default_output = "Releve detaille %d.ods" % annee
        self.site = site
        self.annee = annee
        self.errors = {}
        self.email = None
        self.metas = {}

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print meta.toprettyxml()
                name = meta.getAttribute('meta:name')
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = float(value)
                else:
                    self.metas[name] = value
            return None
                
        elif filename == 'styles.xml':
            ReplaceTextFields(dom, GetCrecheFields(creche))
            return []

        elif filename == 'content.xml':
            if self.metas['Format'] == "Optimomes":
                spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
                feuille = spreadsheet.getElementsByTagName("table:table").item(0)
                lines = feuille.getElementsByTagName("table:table-row")
                ReplaceTextFields(lines[0], [('date-debut', datetime.date(self.annee, 1, 1)), ('date-fin', datetime.date(self.annee, 12, 31))])
                template_m4_first = lines[4]
                template_m4 = lines[5]
                feuille.removeChild(template_m4)
                after_m4 = lines[6]
                inscrits = GetInscrits(datetime.date(self.annee, 1, 1), datetime.date(self.annee, 12, 31))
                for i, inscrit in enumerate(inscrits):
                    fields = GetInscritFields(inscrit)
                    
                    if i == 0:
                        clone = template_m4_first
                        first_cell = clone.getElementsByTagName("table:table-cell").item(0)
                        first_cell.setAttribute("table:number-rows-spanned", str(len(inscrits)))
                    else:
                        clone = template_m4.cloneNode(1)
                        feuille.insertBefore(clone, after_m4)

                    ReplaceFields(clone, fields)
                    if i > 1:
                        IncrementFormulas(clone, row=+i-1)
                    
                    for mois in range(12):
                        fields = [('heures-facturees', 0), ('heures-realisees', 0), ('total', 0)]
                        if datetime.date(self.annee, mois+1, 1) <= today:
                            try:
                                facture = Facture(inscrit, self.annee, mois+1)
                                fields = [('heures-facturees', facture.heures_facture), ('heures-realisees', facture.heures_realisees), ('total', facture.total)]
                            except CotisationException, e:
                                self.errors[GetPrenomNom(inscrit)] = e.errors
                        if i==0:
                            cells = clone.getElementsByTagName("table:table-cell")[3+mois*3:6+mois*3]
                        else:
                            cells = clone.getElementsByTagName("table:table-cell")[2+mois*3:5+mois*3]
                        ReplaceFields(cells, fields)
                        
                IncrementFormulas(after_m4, row=+len(inscrits)-2, flags=FLAG_SUM_MAX)                    
            else:
                spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
                feuille = spreadsheet.getElementsByTagName("table:table").item(0)
                lines = feuille.getElementsByTagName("table:table-row")
                template = lines[1:13]
                after = lines[13]
                for line in template:
                    feuille.removeChild(line)
                for inscrit in GetInscrits(datetime.date(self.annee, 1, 1), datetime.date(self.annee, 12, 31)):
                    for i, line in enumerate(template):
                        try:
                            facture = Facture(inscrit, self.annee, i+1)
                        except CotisationException, e:
                            facture = None
                            self.errors[GetPrenomNom(inscrit)] = e.errors                            
                        clone = line.cloneNode(1)
                        ReplaceTextFields(clone, GetInscritFields(inscrit))
                        if facture:
                            ReplaceTextFields(clone, GetFactureFields(facture))
                        feuille.insertBefore(clone, after)
            return self.errors