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
from ooffice import *


class SuiviRHSalariesModifications(object):
    title = "Suivi RH salariés"
    template = "Suivi RH salaries.ods"

    def __init__(self, salaries, periode):
        self.salaries = salaries
        self.periode = periode
        if self.periode.month >= 6:
            self.debut_conges_payes = datetime.date(self.periode.year, 6, 1)
            self.fin_conges_payes = datetime.date(self.periode.year + 1, 5, 31)
        else:
            self.debut_conges_payes = datetime.date(self.periode.year - 1, 6, 1)
            self.fin_conges_payes = datetime.date(self.periode.year, 5, 31)
        self.email = None
        self.site = None
        self.multi = False
        self.errors = {}
        if len(salaries) > 1:
            self.default_output = "Suivi RH salaries %s %d.ods" % (months[periode.month - 1], periode.year)
        else:
            who = salaries[0]
            self.default_output = "Suivi RH salaries %s - %s %d.ods" % (GetPrenomNom(who), months[periode.month - 1], periode.year)

    def get_salarie_heures_supp(self, salarie):
        solde_heures_supp, compteur_heures_supp = 0.0, 0.0
        lines_heures_supp = []
        for line in salarie.heures_supp:
            if line.date < self.periode:
                solde_heures_supp += line.value
            elif line.date.month == self.periode.month:
                compteur_heures_supp += line.value
                lines_heures_supp.append([
                    ("date", line.date),
                    ("heures-supp", line.value)])
        for timeslot in salarie.days:
            activity = database.creche.activites.get(timeslot.value, None)
            if activity:
                if activity.mode == MODE_SALARIE_HEURES_SUPP:
                    value = timeslot.get_duration() / 60
                elif activity.mode == MODE_SALARIE_RECUP_HEURES_SUPP:
                    value = - timeslot.get_duration() / 60
                else:
                    continue
                if timeslot.date < self.periode:
                    solde_heures_supp += value
                elif timeslot.date.month == self.periode.month:
                    compteur_heures_supp += value
                    lines_heures_supp.append([
                        ("date", timeslot.date),
                        ("heures-supp", value)])
        lines_heures_supp.sort(key=lambda l: l[0][1])
        return lines_heures_supp, solde_heures_supp, compteur_heures_supp

    def get_salarie_conges_payes(self, salarie):
        solde_conges = 0
        for line in salarie.credit_conges:
            if line.date == self.debut_conges_payes:
                solde_conges = line.value
                break
        lines_conges = []
        for conge in salarie.conges:
            if conge.type == CONGES_PAYES:
                debut, fin = str2date(conge.debut), str2date(conge.fin)
                if debut and fin and debut >= self.debut_conges_payes and fin <= self.fin_conges_payes:
                    date, value = debut, 0
                    while date <= fin and value < 100:
                        if date not in database.creche.jours_fete:
                            weekday = date.weekday()
                            if weekday < 4:
                                value -= 1
                            elif weekday == 4:
                                value -= 2
                        date += datetime.timedelta(1)
                    lines_conges.append([
                        ("debut", debut),
                        ("fin", fin),
                        ("jours", value)])
        lines_conges.sort(key=lambda l: l[0][1])
        compteur = solde_conges
        for line in lines_conges:
            compteur += line[-1][1]
            line.append(("compteur", compteur))
        return lines_conges, solde_conges

    def fill_salarie_tab(self, salarie, tab):
        lines = tab.getElementsByTagName("table:table-row")
        template1 = lines[5]
        total1 = lines[6]
        template2_headers = [lines[10], lines[11], lines[14]]
        template2 = lines[13]

        # l'entête
        global_fields = GetCrecheFields(database.creche) + GetSalarieFields(salarie)
        global_fields += [
            ("annee", self.periode.year),
            ("debut-conges-payes", date2str(self.debut_conges_payes)),
            ("fin-conges-payes", date2str(self.fin_conges_payes)),
            ("mois", months[self.periode.month - 1])]
        for line in lines[0:5]:
            ReplaceTextFields(line, global_fields)

        # le mois jour par jour
        date = self.periode
        count = 0
        while date.month == self.periode.month:
            count += 1
            line = template1.cloneNode(1)
            if date.weekday() == 6:
                state = ABSENT
            elif date.weekday() == 5:
                state = salarie.get_state(date - datetime.timedelta(1))
                if state != CONGES_PAYES:
                    state = ABSENT
            else:
                state = salarie.get_state(date)
            fields = [
                ("day", date.day),
                ("weekday", days[date.weekday()]),
                ("present", 1 if state == PRESENT else 0),
                ("ferie", 1 if date in database.creche.jours_fete else 0),
                ("cp", 1 if state == CONGES_PAYES else 0),
                ("recup", 1 if state == CONGES_RECUP_HEURES_SUPP else 0),
                ("sans-solde", 1 if state == CONGES_SANS_SOLDE else 0),
                ("maternite", 1 if state == CONGES_MATERNITE else 0),
                ("malade", 1 if state == MALADE else 0),
            ]
            ReplaceFields(line, fields)
            tab.insertBefore(line, template1)
            date += datetime.timedelta(1)
        IncrementFormulas(total1, row=+count-1, flags=FLAG_SUM_MAX)
        tab.removeChild(template1)

        # suivi des heures supp et des congés (2 tableaux côte à côte)
        lines_heures_supp, solde_heures_supp, compteur_heures_supp = self.get_salarie_heures_supp(salarie)
        lines_conges, solde_conges = self.get_salarie_conges_payes(salarie)
        global_fields.extend([
            ("solde-heures-supp", solde_heures_supp),
            ("compteur-heures-supp", solde_heures_supp + compteur_heures_supp),
            ("droit-conges-payes", solde_conges)
        ])
        for line in template2_headers:
            ReplaceTextFields(line, global_fields)
        for i in range(max(len(lines_heures_supp), len(lines_conges))):
            line = template2.cloneNode(1)
            fields = []
            fields.extend(lines_heures_supp[i] if i < len(lines_heures_supp) else [("date", ""), ("heures-supp", "")])
            fields.extend(lines_conges[i] if i < len(lines_conges) else [("debut", ""), ("fin", ""), ("jours", ""), ("compteur", "")])
            ReplaceTextFields(line, fields)
            tab.insertBefore(line, template2)
        tab.removeChild(template2)

    def execute(self, filename, dom):
        if filename != "content.xml":
            return None

        spreadsheet = dom.getElementsByTagName("office:spreadsheet").item(0)
        template = spreadsheet.getElementsByTagName("table:table").item(0)

        for salarie in self.salaries:
            if salarie.GetContrats(self.periode, GetMonthEnd(self.periode)):
                tab = template.cloneNode(1)
                self.fill_salarie_tab(salarie, tab)
                spreadsheet.insertBefore(tab, template)

        spreadsheet.removeChild(template)

        return self.errors
