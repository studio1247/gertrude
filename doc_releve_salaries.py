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
from ooffice import *

class ReleveSalariesModifications(object):
    def __init__(self, salaries, periode):
        self.salaries = salaries
        self.periode = periode
        self.email = None
        self.site = None
        self.multi = False
        self.template = 'Releve salaries.ods'
        if len(salaries) > 1:
            self.default_output = u"Releve salaries %s %d.odt" % (months[periode.month-1], periode.year)
        else:
            who = salaries[0]
            self.default_output = u"Releve salaries %s - %s %d.odt" % (GetPrenomNom(who), months[periode.month - 1], periode.year)
    
    def GetFields(self, salarie):
        fields = [('nom-creche', creche.nom),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('departement-creche', GetDepartement(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('telephone-creche', creche.telephone),
                ('email-creche', creche.email),
                ('prenom', salarie.prenom),
                ('nom', salarie.nom),
                ('mois', months[self.periode.month-1]),
                ('annee', self.periode.year)
                ]
        day = self.periode
        weekday = day.weekday()
        if weekday >= 1 or weekday <= 4:
            day -= datetime.timedelta(weekday)
        semaine = 0
        while day.year <= self.periode.year and day.month <= self.periode.month:
            semaine += 1
            for i in range(7):
                contrat = salarie.GetContrat(day)
                if contrat is not None:
                    if day in salarie.journees:
                        heures = salarie.journees[day].GetNombreHeures()
                    else:
                        heures = contrat.getJourneeReference(day).GetNombreHeures()
                else:
                    heures = 0
                if heures == 0:
                    heures = ""
                fields.append(("%s-%d" % (days[i].lower(), semaine), heures))                    
                day += datetime.timedelta(1)
        return fields

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)       
        lignes = table.getElementsByTagName("table:table-row")
        
        LINES = 16
        template = lignes[1:LINES+1]
        last_line = lignes[LINES+1]
        for line in template:
            table.removeChild(line)

        inc = 0
        for salarie in self.salaries:
            lignes = []
            for l, line in enumerate(template):
                clone = line.cloneNode(1)
                lignes.append(clone)
                IncrementFormulas(clone, row=+inc)
                table.insertBefore(clone, last_line)
                        
            fields = self.GetFields(salarie)
            ReplaceFields(lignes, fields)
            inc += LINES