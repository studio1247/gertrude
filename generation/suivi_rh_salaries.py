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

import datetime

from constants import months, MODE_SALARIE_HEURES_SUPP, MODE_SALARIE_RECUP_HEURES_SUPP, CONGES_PAYES, ABSENT, days, \
    PRESENT, CONGES_RECUP_HEURES_SUPP, CONGES_SANS_SOLDE, MALADE, CONGES_MATERNITE
from functions import GetPrenomNom, GetCrecheFields, GetSalarieFields
from helpers import GetMonthEnd, str2date, date2str
from generation.email_helpers import SendToSalariesMixin
from generation.opendocument import OpenDocumentSpreadsheet, FLAG_SUM_MAX


class SuiviRHSalariesSpreadsheet(OpenDocumentSpreadsheet, SendToSalariesMixin):
    title = "Suivi RH salariés"
    template = "Suivi RH salaries.ods"

    def __init__(self, salaries, periode, details=True):
        OpenDocumentSpreadsheet.__init__(self)
        self.periode = periode
        self.month_end = GetMonthEnd(periode)
        self.salaries = [salarie for salarie in salaries if salarie.GetContrats(periode, self.month_end)]
        self.salaries.sort(key=lambda salarie: salarie.nom + " " + salarie.prenom)
        self.reservataire = None
        self.details = details
        if self.periode.month >= 6:
            self.debut_conges_payes = datetime.date(self.periode.year, 6, 1)
            self.fin_conges_payes = datetime.date(self.periode.year + 1, 5, 31)
        else:
            self.debut_conges_payes = datetime.date(self.periode.year - 1, 6, 1)
            self.fin_conges_payes = datetime.date(self.periode.year, 5, 31)
        if len(salaries) > 1:
            self.set_default_output("Suivi RH salaries %s %d.ods" % (months[periode.month - 1], periode.year))
        else:
            who = salaries[0]
            self.set_default_output("Suivi RH %s %s %d.ods" % (GetPrenomNom(who), months[periode.month - 1], periode.year))
        SendToSalariesMixin.__init__(self, self.default_output[:-4], "Accompagnement suivi RH.txt", "%(count)d suivis envoyés")

    def split(self, who):
        return SuiviRHSalariesSpreadsheet([who], self.periode, self.details)

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
            if timeslot.activity.mode == MODE_SALARIE_HEURES_SUPP:
                value = (timeslot.get_duration() / 60) * 1.1
            elif timeslot.activity.mode == MODE_SALARIE_RECUP_HEURES_SUPP:
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
                        if date not in salarie.creche.jours_fete:
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
        header1 = lines[4]
        template1 = lines[5]
        total1 = lines[6]
        template2_headers = [lines[10], lines[11], lines[14]]
        template2 = lines[13]

        # l'entête
        global_fields = GetCrecheFields(salarie.creche) + GetSalarieFields(salarie)
        global_fields += [
            ("annee", self.periode.year),
            ("debut-conges-payes", date2str(self.debut_conges_payes)),
            ("fin-conges-payes", date2str(self.fin_conges_payes)),
            ("mois", months[self.periode.month - 1])]
        for line in lines[0:5]:
            self.replace_cell_fields(line, global_fields)

        # le mois jour par jour
        if self.details:
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
                    ("present", 1 if state == PRESENT else None),
                    ("ferie", 1 if date in salarie.creche.jours_fete else None),
                    ("cp", 1 if state == CONGES_PAYES else None),
                    ("recup", 1 if state == CONGES_RECUP_HEURES_SUPP else None),
                    ("sans-solde", 1 if state == CONGES_SANS_SOLDE else None),
                    ("maternite", 1 if state == CONGES_MATERNITE else None),
                    ("malade", 1 if state == MALADE else None),
                ]
                self.replace_cell_fields(line, fields)
                tab.insertBefore(line, template1)
                date += datetime.timedelta(1)
            self.increment_formulas(total1, row=+count-1, flags=FLAG_SUM_MAX)
            tab.removeChild(template1)
        else:
            for line in (header1, template1, total1):
                tab.removeChild(line)

        # suivi des heures supp et des congés (2 tableaux côte à côte)
        lines_heures_supp, solde_heures_supp, compteur_heures_supp = self.get_salarie_heures_supp(salarie)
        lines_conges, solde_conges = self.get_salarie_conges_payes(salarie)
        global_fields.extend([
            ("solde-heures-supp", solde_heures_supp),
            ("compteur-heures-supp", solde_heures_supp + compteur_heures_supp),
            ("droit-conges-payes", solde_conges)
        ])
        for line in template2_headers:
            self.replace_cell_fields(line, global_fields)
        for i in range(max(len(lines_heures_supp), len(lines_conges))):
            line = template2.cloneNode(1)
            fields = []
            fields.extend(lines_heures_supp[i] if i < len(lines_heures_supp) else [("date", ""), ("heures-supp", "")])
            fields.extend(lines_conges[i] if i < len(lines_conges) else [("debut", ""), ("fin", ""), ("jours", ""), ("compteur", "")])
            self.replace_cell_fields(line, fields)
            tab.insertBefore(line, template2)
        tab.removeChild(template2)

    def modify_content(self, dom):
        spreadsheet = dom.getElementsByTagName("office:spreadsheet").item(0)
        template = spreadsheet.getElementsByTagName("table:table").item(0)

        for salarie in self.salaries:
            tab = template.cloneNode(1)
            self.fill_salarie_tab(salarie, tab)
            spreadsheet.insertBefore(tab, template)

        spreadsheet.removeChild(template)

        return True


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    from globals import database
    database.init("../databases/lutinsminiac.db")
    database.load()
    document = SuiviRHSalariesSpreadsheet(database.creche.salaries, datetime.date(2018, 1, 1))
    if 0:
        document.generate(filename="./test-%f.ods" % random.random())
        if document.errors:
            print(document.errors)
        StartLibreOffice(document.output)
    else:
        database.creche.smtp_server = "test"
        document.send_to_salaries(debug=True)
