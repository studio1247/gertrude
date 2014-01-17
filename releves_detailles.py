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

class RelevesDetaillesModifications(object):
    def __init__(self, site, annee):
        self.multi = False
        self.template = 'Releve detaille.ods'
        self.default_output = "Releve detaille %d.ods" % annee
        self.site = site
        self.annee = annee
        self.errors = {}
        self.email = None

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            ReplaceTextFields(dom, GetCrecheFields(creche))
            return []

        elif filename == 'content.xml':
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            feuille = spreadsheet.getElementsByTagName("table:table").item(0)
            lines = feuille.getElementsByTagName("table:table-row")
            template = lines[1:13]
            after = lines[13]
            for line in template:
                feuille.removeChild(line)
            for inscription in GetInscriptions(datetime.date(self.annee, 1, 1), datetime.date(self.annee, 12, 31)):
                if not self.site or inscription.site == self.site:
                    for i, line in enumerate(template):
                        try:
                            facture = Facture(inscription.inscrit, self.annee, i+1)
                        except CotisationException, e:
                            facture = None
                            self.errors[GetPrenomNom(inscription.inscrit)] = e.errors                            
                        clone = line.cloneNode(1)
                        ReplaceTextFields(clone, GetInscritFields(inscription.inscrit))
                        if facture:
                            ReplaceTextFields(clone, GetFactureFields(facture))
                        feuille.insertBefore(clone, after)
            return self.errors