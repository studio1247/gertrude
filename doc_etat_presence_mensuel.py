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
from ooffice import *

class EtatPresenceMensuelModifications(object):
    def __init__(self, site, date):
        self.multi = False
        self.template = "Etat presence mensuel.ods"
        self.default_output = "Etat presence mensuel %s %d.ods" % (months[date.month - 1], date.year)
        self.date = date
        self.site = site
        self.gauge = None
        self.email = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")
              
        # Les champs de l'entête
        ReplaceFields(lignes, [('mois', months[self.date.month-1]),
                               ('annee', self.date.year),
                              ])
        
        # Les lignes
        #for i, ligne in enumerate(lignes):
        #    print i, ligne.toprettyxml()
            
        #return errors

        inscrits = GetInscrits(self.date, GetMonthEnd(self.date))
        inscrits.sort(cmp=lambda x,y: cmp(GetPrenomNom(x), GetPrenomNom(y)))
        
        template = lignes.item(5)
        for inscrit in inscrits:           
            cantine, garderie = 0, 0
            date = self.date
            while date.month == self.date.month:
                journee = inscrit.GetJournee(date)
                if journee:
                    if journee.GetActivity(8.0):
                        garderie += 1
                    if journee.GetActivity(12.5):
                        cantine += 1
                    if journee.GetActivity(13.5):
                        garderie += 1
                    if journee.GetActivity(18.0):
                        garderie += 1
                date += datetime.timedelta(days=1)
            
            ligne = template.cloneNode(1)
            fields = GetInscritFields(inscrit)
            fields.extend([('cantine', cantine),
                           ('garderie', garderie),
                          ])
            ReplaceFields(ligne, fields)
            table.insertBefore(ligne, template)

        table.removeChild(template)
        
        totaux = lignes.item(6)
        IncrementFormulas(totaux, row=+len(inscrits)-1, flags=FLAG_SUM_MAX)
        
        if self.gauge:
            self.gauge.SetValue(90)
            
        return errors
