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
from ooffice import *


class ExportTabletteModifications(object):
    title = "Export tablette"
    template = "Export tablette.ods"

    def __init__(self, site, date):
        self.multi = False
        self.default_output = "Export tablette.ods"
        self.site, self.date = site, date
        self.gauge = None
        self.email = None
        self.site = None

    def FetchJournal(self):
        journal = config.connection.LoadJournal()
        self.array_enfants = {}
        self.array_salaries = {}
        lines = journal.split("\n")
        for line in lines:
            try:
                salarie, label, idx, date, heure = SplitLineTablette(line)
                if date.year != self.date.year or date.month != self.date.month:
                    continue
                if salarie:
                    array = self.array_salaries
                else:
                    array = self.array_enfants
                if idx not in array:
                    array[idx] = { }
                if date not in array[idx]:
                    array[idx][date] = []
                if label == "arrivee":
                    array[idx][date].append(PeriodePresence(date, heure))
                elif label == "depart":
                    if len(array[idx][date]):
                        last = array[idx][date][-1]
                        if last.date == date and last.arrivee:
                            last.depart = heure
                        else:
                            array[idx][date].append(PeriodePresence(date, None, heure))
                    else:
                        array[idx][date].append(PeriodePresence(date, None, heure))
                elif label == "absent":
                    array[idx][date].append(PeriodePresence(date, absent=True))
                elif label == "malade":
                    array[idx][date].append(PeriodePresence(date, malade=True))
                else:
                    print "Ligne %s inconnue" % label
            except Exception, e:
                print e
                pass
    
    def GetHeureString(self, value):
        if value is None:
            return ""
        heures = value / 60
        minutes = value % 60
        return "%dh%02d" % (heures, minutes)

    def AddSheet(self, who, array, fields):
        table = self.template.cloneNode(1)
        table.setAttribute("table:name", GetPrenomNom(who))
        self.spreadsheet.insertBefore(table, self.template)
        lignes = table.getElementsByTagName("table:table-row")
        ReplaceFields(lignes, fields)
        lineTemplate = lignes.item(3)
        dates = array.keys()
        dates.sort()
        for date in dates:
            for jour in array[date]:
                ligne = lineTemplate.cloneNode(1)
                lineFields = fields + [('date', date),
                                       ('heure-arrivee', self.GetHeureString(jour.arrivee)),
                                       ('heure-depart', self.GetHeureString(jour.depart))]
                ReplaceFields(ligne, lineFields)
                table.insertBefore(ligne, lineTemplate)
        table.removeChild(lineTemplate)

    
    def SortedKeys(self, array, function):
        keys = array.keys()
        keys.sort(key=lambda key: GetPrenomNom(function(key)))
        return keys
            
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        self.FetchJournal()    
        errors = {}
        self.spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        self.template = self.spreadsheet.getElementsByTagName("table:table").item(0)

        for key in self.SortedKeys(self.array_enfants, creche.GetInscrit):
            inscrit = creche.GetInscrit(key)
            if inscrit:
                self.AddSheet(inscrit, self.array_enfants[key], GetInscritFields(inscrit))
            else:
                print "Inscrit %d inconnu"
                
        for key in self.SortedKeys(self.array_salaries, creche.GetSalarie):
            salarie = creche.GetSalarie(key)
            if salarie:
                self.AddSheet(salarie, self.array_salaries[key], GetSalarieFields(salarie))
            else:
                print "Salarie %d inconnu"
                        
        self.spreadsheet.removeChild(self.template)
        
        if self.gauge:
            self.gauge.SetValue(90)

        return errors
