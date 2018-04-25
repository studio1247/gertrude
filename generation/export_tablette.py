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
from __future__ import print_function
from constants import *
from database import Salarie
from functions import *
from facture import *
from ooffice import *
from tablette import JournalTablette, PeriodePresence


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
        self.array_enfants = {}
        self.array_salaries = {}

    def FetchJournal(self):
        journal = JournalTablette()
        self.array_enfants = {}
        self.array_salaries = {}
        for who, label, date, heure in journal.get_month_lines(self.date.year, self.date.month):
            if isinstance(who, Salarie):
                array = self.array_salaries
            else:
                array = self.array_enfants
            if who not in array:
                array[who] = {}
            if date not in array[who]:
                array[who][date] = []
            array_result = array[who][date]
            if label == "arrivee":
                if len(array_result) == 0 or array_result[-1].debut != heure:
                    array_result.append(PeriodePresence(date=date, debut=heure))
            elif label == "depart":
                if len(array_result):
                    last = array_result[-1]
                    if last.date == date and last.debut:
                        last.fin = heure
                    else:
                        array_result.append(PeriodePresence(date=date, debut=None, fin=heure))
                else:
                    array_result.append(PeriodePresence(date=date, debut=None, fin=heure))
            elif label == "absent":
                array_result.append(PeriodePresence(date=date, state=VACANCES))
            elif label == "malade":
                array_result.append(PeriodePresence(date=date, state=MALADE))
            else:
                print("Ligne %s inconnue" % label)

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
        line_template = lignes.item(3)
        dates = list(array.keys())
        dates.sort()
        for date in dates:
            for jour in array[date]:
                ligne = line_template.cloneNode(1)
                line_fields = fields + [("date", date),
                                        ("heure-arrivee", self.GetHeureString(jour.debut)),
                                        ("heure-depart", self.GetHeureString(jour.fin))]
                ReplaceFields(ligne, line_fields)
                table.insertBefore(ligne, line_template)
        table.removeChild(line_template)
            
    def execute(self, filename, dom):
        if filename != "content.xml":
            return None
        
        self.FetchJournal()    
        errors = {}
        self.spreadsheet = dom.getElementsByTagName("office:spreadsheet").item(0)
        self.template = self.spreadsheet.getElementsByTagName("table:table").item(0)

        for inscrit in sorted(self.array_enfants, key=lambda enfant: GetPrenomNom(enfant)):
            self.AddSheet(inscrit, self.array_enfants[inscrit], GetInscritFields(inscrit))

        for salarie in sorted(self.array_salaries, key=lambda salarie: GetPrenomNom(salarie)):
            self.AddSheet(salarie, self.array_salaries[salarie], GetSalarieFields(salarie))

        self.spreadsheet.removeChild(self.template)
        
        if self.gauge:
            self.gauge.SetValue(90)

        return errors
