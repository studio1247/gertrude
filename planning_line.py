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

from functions import *
from database import *


class BasePlanningSeparator:
    def __init__(self, label=""):
        self.label = label
        self.readonly = True
        self.commentaire = None
        self.options = 0
        self.timeslots = []

    def get_badge_text(self):
        return None

    def get_summary(self):
        return {}


class BasePlanningLine(object):
    def __init__(self, label="", timeslots=None, options=ACTIVITES | COMMENTS):
        self.label = label
        self.state = PRESENT
        self.sublabel = None
        self.timeslots = [] if timeslots is None else timeslots
        self.reference = None
        self.readonly = False
        self.commentaire = None
        self.options = options

    def get_badge_text(self):
        return ""

    def add_timeslot(self, start, end, activity):
        self.timeslots.append(Timeslot(start, end, activity))

    def delete_timeslot(self, i, check=True):
        del self.timeslots[i]

    def set_comment(self, comment):
        self.commentaire = comment

    def set_checkbox(self, activity):
        self.add_timeslot(None, None, activity)

    def clear_checkbox(self, activity):
        for i, timeslot in enumerate(self.timeslots):
            if timeslot.activity == activity:
                self.delete_timeslot(i)
                break

    def set_activity(self, start, end, value):
        if self.options & DRAW_VALUES:
            for i, timeslot in enumerate(self.timeslots):
                if timeslot.value == value:
                    if start <= timeslot.fin + 1 and end >= timeslot.debut - 1:
                        start, end = min(timeslot.debut, start), max(timeslot.fin, end)
                        self.delete_timeslot(i, False)
            self.add_timeslot(start, end, value)
        else:
            for i, timeslot in reversed(list(enumerate(self.timeslots))):
                if value == timeslot.activity:
                    if start <= timeslot.fin + 1 and end >= timeslot.debut - 1:
                        start, end = min(timeslot.debut, start), max(timeslot.fin, end)
                        self.delete_timeslot(i, False)
                elif value.mode in (MODE_LIBERE_PLACE, MODE_CONGES, MODE_ABSENCE_NON_PREVENUE) and start < timeslot.fin and end > timeslot.debut:
                    self.delete_timeslot(i, False)
                    if timeslot.debut < start:
                        self.add_timeslot(timeslot.debut, start, timeslot.activity)
                    if timeslot.fin > end:
                        self.add_timeslot(end, timeslot.fin, timeslot.activity)
                elif timeslot.activity.mode in (MODE_LIBERE_PLACE, MODE_CONGES, MODE_ABSENCE_NON_PREVENUE) and start < timeslot.fin and end > timeslot.debut:
                    self.delete_timeslot(i, False)
                    if timeslot.debut < start:
                        self.add_timeslot(timeslot.debut, start, timeslot.activity)
                    if timeslot.fin > end:
                        self.add_timeslot(end, timeslot.fin, timeslot.activity)
            self.add_timeslot(start, end, value)
            if value.mode in (MODE_NORMAL, MODE_PRESENCE_NON_FACTUREE):
                self.set_activity(start, end, database.creche.states[0])

    def clear_activity(self, start, end, value):
        if self.options & DRAW_VALUES:
            for i in reversed(range(len(self.timeslots))):
                timeslot = self.timeslots[i]
                if start <= timeslot.fin + 1 and end >= timeslot.debut - 1:
                    if start <= timeslot.debut and end >= timeslot.fin:
                        self.delete_timeslot(i)
                    else:
                        if start > timeslot.debut:
                            timeslot.fin = start
                        if end < timeslot.fin:
                            timeslot.debut = end
        else:
            for i, timeslot in enumerate(self.timeslots):
                if value == timeslot.activity:
                    if start <= timeslot.fin + 1 and end >= timeslot.debut - 1:
                        if start > timeslot.debut:
                            self.add_timeslot(timeslot.debut, start, timeslot.activity)
                        if end < timeslot.fin:
                            self.add_timeslot(end, timeslot.fin, timeslot.activity)
                        self.delete_timeslot(i)
                elif timeslot.activity.mode == MODE_NORMAL and start < timeslot.fin and end > timeslot.debut:
                    if timeslot.debut < start:
                        self.add_timeslot(timeslot.debut, start, timeslot.activity)
                    if timeslot.fin > end:
                        self.add_timeslot(end, timeslot.fin, timeslot.activity)
                    self.delete_timeslot(i)

    def is_timeslot_checked(self, activity):
        for timeslot in self.timeslots:
            if timeslot.activity == activity:
                return True
        else:
            return False

    def clear_timeslots(self):
        while self.timeslots:
            self.delete_timeslot(0, check=False)  # TODO tout retirer d'un coup ?

    def set_state(self, state):
        # print("set_state", state)
        self.clear_timeslots()
        self.state = state
        if state == PRESENT:
            self.add_timeslots(self.reference.timeslots)
        else:
            for debut, fin in database.creche.GetPlagesOuvertureArray():
                self.add_timeslots([Timeslot(debut, fin, database.creche.states[state])])
        self.update()

    def get_summary(self):
        return {}


class ChildPlanningLine(BasePlanningLine):
    def __init__(self, inscription, date):
        self.inscription = inscription
        self.inscrit = inscription.inscrit
        self.who = self.inscrit
        self.idx = self.inscrit.idx
        self.site = self.inscription.site
        self.date = date
        BasePlanningLine.__init__(self, GetPrenomNom(self.inscrit))
        if database.creche.conges_inscription in (GESTION_CONGES_INSCRIPTION_MENSUALISES, GESTION_CONGES_INSCRIPTION_NON_MENSUALISES) and date in self.inscrit.jours_conges:
            self.state = VACANCES
            self.day = Day()
            self.timeslots = []
            self.reference = Day()  # semble nécessaire
            self.commentaire = self.inscrit.jours_conges[date].label
            self.readonly = True
        else:
            commentaire = self.inscrit.commentaires.get(date, None)
            self.commentaire = commentaire.commentaire if commentaire else ""
            if database.creche.conges_inscription == GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT and date in self.inscrit.jours_conges:
                self.reference = Day()
                if not self.commentaire:
                    self.commentaire = self.inscrit.jours_conges[date].label
            else:
                self.reference = inscription.get_day_from_date(date)
            self.update()

    def get_badge_text(self):
        heures_reference = self.reference.get_duration() if self.reference else 0
        heures = self.day.get_duration() if self.day else heures_reference
        if heures > 0 or heures_reference > 0:
            return GetHeureString(heures) + '/' + GetHeureString(heures_reference)
        else:
            return None

    def update(self):
        self.day = self.inscrit.days.get(self.date, None)
        self.timeslots = self.day.timeslots if self.day else self.reference.timeslots[:]
        self.timeslots.sort(key=lambda timeslot: timeslot.activity.mode)
        self.state = self.day.get_state() if self.day else self.reference.get_state()
        # print("update =>", self.day, self.timeslots, self.state)
        if self.state == VACANCES:
            if self.inscription.IsNombreSemainesCongesDepasse(self.date):
                self.state = CONGES_DEPASSEMENT

    def add_timeslots(self, timeslots):
        # print("add_timeslots", timeslots)
        for timeslot in timeslots:
            self.inscrit.days.add(TimeslotInscrit(date=self.date, debut=timeslot.debut, fin=timeslot.fin, activity=timeslot.activity))

    def add_timeslot(self, debut, fin, activity):
        # print("add_timeslot", debut, fin, value, self.day, self.state)
        if not self.day:
            self.add_timeslots(self.timeslots)
        elif self.state < 0:
            self.clear_timeslots()
        self.inscrit.days.add(TimeslotInscrit(date=self.date, debut=debut, fin=fin, activity=activity))
        self.update()

    def delete_timeslot(self, i, check=True):
        # print("delete_timeslot", i, check, self.day)
        if self.day:
            self.inscrit.days.remove(self.timeslots[i])
        else:
            del(self.timeslots[i])
            if check and self.timeslots:
                self.add_timeslots(self.timeslots)
        if check:
            if len(self.timeslots) == 0:
                self.day = None  # pour éviter que set_state essaie de supprimer des activités qui n'existent plus
                self.set_state(VACANCES)
            self.update()

    def set_comment(self, comment):
        self.inscrit.commentaires[self.date] = CommentaireInscrit(date=self.date, commentaire=comment)
        self.commentaire = comment

    def get_states(self):
        states = [PRESENT]
        reference_state = self.reference.get_state()
        if reference_state == PRESENT:
            states.append(VACANCES)
            if database.creche.gestion_preavis_conges:
                states.append(ABSENCE_CONGE_SANS_PREAVIS)
            if database.creche.gestion_absences_non_prevenues:
                states.append(ABSENCE_NON_PREVENUE)
            states.append(MALADE)
            if database.creche.gestion_maladie_hospitalisation:
                states.append(HOPITAL)
            if database.creche.gestion_maladie_sans_justificatif:
                states.append(MALADE_SANS_JUSTIFICATIF)
        return states

    def get_summary(self):
        summary = {}
        if self.state > 0:
            for timeslot in self.timeslots:
                activity = timeslot.activity
                if activity.has_summary():
                    if activity not in summary:
                        summary[activity] = [timeslot]
                    else:
                        summary[activity].append(timeslot)
        return summary

    @classmethod
    def select(cls, date, site=None, groupe=None):
        result = []
        for inscrit in database.creche.inscrits:
            inscription = inscrit.get_inscription(date)
            if inscription is not None and (site is None or len(database.creche.sites) <= 1 or inscription.site is site) and (groupe is None or inscription.groupe == groupe):
                line = cls(inscription, date)
                result.append(line)

        if database.creche.tri_planning & TRI_GROUPE:
            result = GetEnfantsTriesParGroupe(result)
        else:
            result.sort(key=lambda line: line.label)

        return result


class StateDay:
    def __init__(self, state):
        self.state = state
        self.timeslots = []

    def get_state(self):
        return self.state


class SalariePlanningLine(BasePlanningLine):
    def __init__(self, planning, date, options=0):
        self.planning = planning
        self.contrat = self.planning.contrat
        self.site = self.contrat.site
        self.salarie = self.contrat.salarie
        self.who = self.salarie
        self.idx = self.salarie.idx
        BasePlanningLine.__init__(self, GetPrenomNom(self.salarie), options)
        self.date = date
        if date in self.salarie.jours_conges and self.salarie.jours_conges[date].type is not None:
            self.state = self.salarie.jours_conges[date].type
            self.reference = StateDay(self.state)
            self.commentaire = self.salarie.jours_conges[date].label
            self.readonly = True
        else:
            commentaire = self.salarie.commentaires.get(date, None)
            self.commentaire = commentaire.commentaire if commentaire else ""
            self.reference = self.planning.get_day_from_date(date)
        self.update()

    def get_badge_text(self):
        debut_semaine = self.date - datetime.timedelta(self.date.weekday())
        fin_semaine = debut_semaine + datetime.timedelta(6)
        debut_mois = GetMonthStart(self.date)
        fin_mois = GetMonthEnd(self.date)
        heures_jour = 0
        heures_semaine = 0
        heures_mois = 0
        date = min(debut_semaine, debut_mois)
        fin = max(fin_semaine, fin_mois)
        while date <= fin:
            day = self.salarie.GetJournee(date)
            if day:
                heures = self.salarie.GetJournee(date).get_duration()
                if date == self.date:
                    heures_jour = heures
                if debut_semaine <= date <= fin_semaine:
                    heures_semaine += heures
                if date.month == self.date.month:
                    heures_mois += heures
            date += datetime.timedelta(1)
        return GetHeureString(heures_jour) + '/' + GetHeureString(heures_semaine) + '/' + GetHeureString(heures_mois)

    def update(self):
        self.day = self.salarie.days.get(self.date, None)
        if self.day:
            self.state = self.day.get_state()
            self.timeslots = self.day.timeslots
        else:
            self.state = self.reference.get_state()
            self.timeslots = self.reference.timeslots[:]

    def add_timeslots(self, timeslots):
        for timeslot in timeslots:
            self.salarie.days.add(TimeslotSalarie(date=self.date, debut=timeslot.debut, fin=timeslot.fin, activity=timeslot.activity))

    def add_timeslot(self, debut, fin, activity):
        # print("add_timeslot", debut, fin, value)
        if not self.day:
            self.add_timeslots(self.timeslots)
        elif self.state < 0:
            self.clear_timeslots()
        self.salarie.days.add(TimeslotSalarie(date=self.date, debut=debut, fin=fin, activity=activity))
        self.update()

    def delete_timeslot(self, i, check=True):
        # print("delete_timeslot", i)
        if self.day:
            self.salarie.days.remove(self.timeslots[i])
        else:
            del self.timeslots[i]
            if check and self.timeslots:
                self.add_timeslots(self.timeslots)
        if check:
            if len(self.timeslots) == 0:
                self.day = None  # pour éviter que set_state essaie de supprimer des activités qui n'existent plus
                self.set_state(VACANCES)
            self.update()

    def set_comment(self, comment):
        self.salarie.commentaires[self.date] = CommentaireSalarie(date=self.date, commentaire=comment)
        self.commentaire = comment

    def get_states(self):
        return [PRESENT, VACANCES, CONGES_SANS_SOLDE, MALADE]

    def get_summary(self):
        return {database.creche.states[PRESENCE_SALARIE]: [timeslot for timeslot in self.timeslots if timeslot.activity.mode == 0]}

    @classmethod
    def select(cls, date, site=None):
        result = []
        for salarie in database.creche.salaries:
            planning = salarie.get_planning(date)
            if planning is not None and (site is None or len(database.creche.sites) <= 1 or planning.contrat.site is site):
                line = cls(planning, date)
                result.append(line)
        result.sort(key=lambda line: line.label)
        return result
