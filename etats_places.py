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

template_total_lines_count = 19
template_first_line = 4
template_lines_count = 8

class EtatsPlacesModifications(object):
    def __init__(self, site, annee):
        self.multi = False
        self.template = 'Etats places.ods'
        self.default_output = "Etats places %d.ods" % annee
        self.site = site
        self.annee = annee
        self.factures = {}
        self.errors = {}
        self.email = None
        self.site = None

    def execute(self, filename, dom):
        print filename
        if filename == 'styles.xml':
            fields = GetCrecheFields(creche)
            ReplaceTextFields(dom, fields)
            return []

        elif filename == 'content.xml':
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
            table = tables.item(0)
            lines = table.getElementsByTagName("table:table-row")
            # line_heures_ouvrees = lines[2]
    
            fields = GetCrecheFields(creche) + GetTarifsHorairesFields(creche)
            fields.append(("annee", self.annee))
            ReplaceFields(lines, fields)
            
            date = datetime.date(self.annee, 1, 1)
            while date.year == self.annee:
                count = 0
                for inscrit in creche.inscrits:
                    inscription = inscrit.GetInscription(date)
                    if inscription and (not self.site or self.site == inscription.site):
                        state = inscrit.getState(date)[0]
                        if state > 0 and state & PRESENT:
                            count += 1
                cell = GetCell(GetRow(table, date.month+3), date.day)
                print cell.toprettyxml()
                SetValue(cell, count)
                print cell.toprettyxml()
                
                date += datetime.timedelta(1)
 
        return self.errors

 

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    filename = 'synthese_financiere_%d.ods' % (today.year - 1)
    print GenerateOODocument(SyntheseFinanciereModifications(today.year - 1), filename)
    print u'Fichier %s généré' % filename
