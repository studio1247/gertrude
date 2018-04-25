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

import argparse
import urllib
import pytz
from database import Day, TimeslotInscrit, Inscrit, TimeslotSalarie, GetUnionTimeslots
from connection import get_connection_from_config
from functions import *
from globals import *


def write_apache_logs_to_journal(filename):
    # Recuperation des logs Apache
    lines = open(filename).readlines()
    result = []
    for line in lines:
        print(line)
        splitted = line.split()
        url = splitted[6]
        action = None
        combinaison = None
        ts = None
        params = url.split("?")[1].split("&")
        for param in params:
            key, val = param.split("=")
            if key == "action":
                action = val
            elif key == "combinaison":
                combinaison = val
            elif key == "ts":
                ts = int(val)

        who = None
        for inscrit in database.creche.inscrits:
            letter = inscrit.nom[0] if len(inscrit.nom) > 0 else ""
            name = urllib.quote_plus(inscrit.prenom.encode("utf-8")) + "+" + urllib.quote_plus(letter.encode("utf-8"))
            # print("comparaison", name, combinaison)
            if name == combinaison:
                who = inscrit

        if who is None:
            for inscrit in database.creche.salaries:
                letter = inscrit.nom[0] if len(inscrit.nom) > 0 else ""
                name = urllib.quote_plus(inscrit.prenom.encode("utf-8")) + "+" + urllib.quote_plus(letter.encode("utf-8"))
                # print("comparaison", name, combinaison)
                if name == combinaison:
                    action += "_salarie"
                    who = inscrit

        if who is None:
            if combinaison.strip():
                print("-----ERREUR-----", action, combinaison, ts)
        else:
            date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d@%H:%M')
            if (action, who.idx, date) in result:
                print("-----ENTREE EN DOUBLE-----", url)
            else:
                result.append((action, who.idx, date))

    result.sort(key=lambda tup: tup[-1])  # sorts in place
    f = open("journal.txt", "w")
    for action, idx, date in result:
        print(action, idx, date)
        f.write("%s %d %s\n" % (action, idx, date))
    f.close()


class PeriodePresence(object):
    def __init__(self, date=None, debut=None, fin=None, state=0):
        self.date = date
        self.debut = debut
        self.fin = fin
        self.state = state

    def __repr__(self):
        return "%s-%s" % (self.debut, self.fin)


class JournalTablette:
    def __init__(self, traces=False):
        self.lines = []
        self.traces = traces

    def load(self):
        if not self.lines:
            journal = config.connection.LoadJournal()
            if journal:
                self.lines = journal.split("\n")

    @staticmethod
    def split_line(line):
        label, idx, date = line.split()
        tm = time.strptime(date, "%Y-%m-%d@%H:%M")
        date = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
        heure = tm.tm_hour * 60 + tm.tm_min
        if label.endswith("_salarie"):
            salarie = database.creche.GetSalarie(idx)
            return salarie, label[:-8], date, heure
        else:
            inscrit = database.creche.GetInscrit(idx)
            return inscrit, label, date, heure

    def get_date_lines(self, date):
        self.load()
        s = "%04d-%02d-%02d" % (date.year, date.month, date.day)
        lines = set([line for line in self.lines if s in line])
        result = []
        for line in lines:
            splitted = self.split_line(line)
            if splitted[0]:
                result.append(splitted)
        result.sort(key=lambda line: line[-1])
        return result

    def get_month_lines(self, year, month):
        self.load()
        s = "%04d-%02d-" % (year, month)
        lines = set([line for line in self.lines if s in line])
        result = []
        for line in lines:
            splitted = self.split_line(line)
            if splitted[0]:
                result.append(splitted)
        result.sort(key=lambda line: 20000000 * line[-2].year + 200000 * line[-2].month + 2000 * line[-2].day + line[-1])
        return result

    def get_periods_by_person(self, date):
        lines = self.get_date_lines(date)
        periodes = {}
        for who, label, date, heure in lines:
            result = periodes.get(who, None)
            if result is None:
                result = []
                periodes[who] = result
            if label == "arrivee":
                if len(result) == 0 or (result[-1].debut and result[-1].fin):
                    if not result or result[-1].fin != heure:
                        result.append(PeriodePresence(debut=heure))
                elif result[-1].fin:
                    result[-1].debut = min(heure, result[-1].fin)
                    result[-1].fin = None
                else:
                    result[-1].fin = heure
            elif label == "depart":
                if len(result) > 0:
                    last = result[-1]
                    last.fin = heure
                else:
                    result.append(PeriodePresence(debut=None, fin=heure))
            elif label == "absent":
                result.append(PeriodePresence(state=VACANCES))
            elif label == "malade":
                result.append(PeriodePresence(state=MALADE))
            else:
                print("Ligne %s inconnue" % label)
        return periodes

    @staticmethod
    def clear_day(who, date):
        day = who.days.get(date, Day())
        for timeslot in day.timeslots[:]:
            if timeslot.activity.mode in (MODE_PRESENCE, MODE_PLACE_SOUHAITEE):
                who.days.remove(timeslot)

    def add_periods(self, who, date, periods):
        state_before = str(who.days.get(date, None))

        # we clear the day timeslots (only PRESENCE + PLACE SOUHAITEE)
        self.clear_day(who, date)
        # we fix timeslots start / end
        for period in periods:
            self.fix_period(period)
        # if the last one is absent / malade it's the only one
        period = periods[-1]
        if period.state != 0:
            self.add_period(who, date, period, period.state, TimeslotInscrit if isinstance(who, Inscrit) else TimeslotSalarie)
            return
        # does the job
        periods = GetUnionTimeslots([period for period in periods if period.state == 0])
        for period in periods:
            self.add_period(who, date, period, 0, TimeslotInscrit if isinstance(who, Inscrit) else TimeslotSalarie)

        state_after = str(who.days.get(date, None))
        if state_after != state_before:
            print("%s: before=%s periods=%s after=%s" % (GetPrenomNom(who), state_before, periods, state_after))

    @staticmethod
    def fix_period(period):
        period.activity = None
        if period.state == 0 and period.debut:
            period.debut = (period.debut + TABLETTE_MARGE_ARRIVEE) // database.creche.granularite * (database.creche.granularite // BASE_GRANULARITY)
        else:
            period.debut = int(database.creche.ouverture * (60 // BASE_GRANULARITY))
        if period.state == 0 and period.fin:
            period.fin = (period.fin + database.creche.granularite - TABLETTE_MARGE_ARRIVEE) // database.creche.granularite * (database.creche.granularite // BASE_GRANULARITY)
        else:
            period.fin = int(database.creche.fermeture * (60 // BASE_GRANULARITY))

    def add_period(self, who, date, period, value, cls):
        if self.traces:
            print("Nouveau timeslot pour", date)
        who.days.add(cls(date=date, debut=period.debut, fin=period.fin, activity=database.creche.states[value]))
        history.Append(None)

    def sync(self, date, update_adults=True):
        print("Synchro tablette %s" % date2str(date))
        periods = self.get_periods_by_person(date)
        for person in periods:
            # if not database.creche.cloture_facturation or not inscrit.get_facture_cloturee(date):
            if update_adults or isinstance(person, Inscrit):
                self.add_periods(person, date, periods[person])
        database.commit()

    def sync_period(self, start, end, update_synchro_date=True, update_adults=True):
        date = start
        while date <= end:
            self.sync(date, update_adults)
            date += datetime.timedelta(1)
        if update_synchro_date:
            database.creche.last_tablette_synchro = end
            database.commit()

    def sync_until_now(self):
        tz = pytz.timezone('Europe/Paris')
        end = datetime.date.today()
        date = datetime.datetime.now(tz=tz)
        hour = float(date.hour) + float(date.minute) / 60
        if hour < database.creche.fermeture:
            end -= datetime.timedelta(1)
        start = str2date(database.creche.last_tablette_synchro) if database.creche.last_tablette_synchro else None
        if not start:
            start = end
            print("Synchro tablette activée le %s" % end.isoformat())
        self.sync_period(start + datetime.timedelta(1), end)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="config filename")
    parser.add_argument("start", help="start date")
    parser.add_argument("end", help="end date", default=None)
    parser.add_argument("--nosync", help="don't update the last synchronisation date", action="store_true")
    parser.add_argument("--traces", help="enable traces", action="store_true")
    parser.add_argument("--noadults", help="modify only children", action="store_true")
    args = parser.parse_args()

    config.load(args.config)
    start = str2date(args.start)
    if args.end:
        end = str2date(args.end)
    else:
        end = start

    config.connection = get_connection_from_config()
    database.init(config.database)
    database.load()

    journal = JournalTablette(traces=args.traces)
    journal.sync_period(start, end, update_synchro_date=not args.nosync, update_adults=not args.noadults)


if __name__ == "__main__":
    main()
