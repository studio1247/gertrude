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

import urllib
from database import Day, TimeslotInscrit, Inscrit, TimeslotSalarie
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


def sync_tablette_lines(lines, tz=None, traces=False):
    last_imported_day = datetime.date.today()
    date = datetime.datetime.now(tz=tz)
    hour = float(date.hour) + float(date.minute) / 60
    if hour < database.creche.fermeture:
        last_imported_day -= datetime.timedelta(1)

    def AddPeriodes(who, date, periodes):
        day = who.days.get(date, Day())
        while day.timeslots:
            who.days.remove(day.timeslots[0])
        for periode in periodes:
            AddPeriode(who, date, periode, TimeslotInscrit if isinstance(who, Inscrit) else TimeslotSalarie)

    def AddPeriode(who, date, periode, cls):
        arrivee = int(database.creche.ouverture * (60 // BASE_GRANULARITY))
        depart = int(database.creche.fermeture * (60 // BASE_GRANULARITY))
        if periode.absent:
            value = VACANCES
        elif periode.malade:
            value = MALADE
        else:
            value = 0
            if periode.arrivee:
                arrivee = periode.arrivee
            else:
                errors.append("%s : Pas d'arrivée enregistrée le %s" % (GetPrenomNom(who), periode.date))
            if periode.depart:
                depart = periode.depart
            else:
                errors.append("%s : Pas de départ enregistré le %s" % (GetPrenomNom(who), periode.date))

        if traces:
            print("Nouveau timeslot pour", date)
        who.days.add(cls(date=date, debut=arrivee, fin=depart, value=value))
        history.Append(None)

    array_enfants = {}
    array_salaries = {}

    for line in lines:
        if len(line) < 20:
            break

        try:
            salarie, label, idx, date, heure = SplitLineTablette(line)
            if date > last_imported_day:
                break
            if salarie:
                array = array_salaries
            else:
                array = array_enfants
            if idx not in array:
                array[idx] = {}
            if date not in array[idx]:
                array[idx][date] = []
            if label == "arrivee":
                arrivee = (heure + TABLETTE_MARGE_ARRIVEE) // database.creche.granularite * (database.creche.granularite // BASE_GRANULARITY)
                if len(array[idx][date]) == 0 or (array[idx][date][-1].arrivee and array[idx][date][-1].depart):
                    array[idx][date].append(PeriodePresence(date, arrivee))
                elif array[idx][date][-1].depart:
                    array[idx][date][-1].arrivee = array[idx][date][-1].depart
                    array[idx][date][-1].depart = None
            elif label == "depart":
                depart = (heure + database.creche.granularite - TABLETTE_MARGE_ARRIVEE) // database.creche.granularite * (database.creche.granularite // BASE_GRANULARITY)
                if len(array[idx][date]) > 0:
                    last = array[idx][date][-1]
                    last.depart = depart
                else:
                    array[idx][date].append(PeriodePresence(date, None, depart))
            elif label == "absent":
                array[idx][date].append(PeriodePresence(date, absent=True))
            elif label == "malade":
                array[idx][date].append(PeriodePresence(date, malade=True))
            else:
                print("Ligne %s inconnue" % label)
            database.creche.last_tablette_synchro = line
        except Exception as e:
            print(e)

    # print(array_salaries)

    errors = []
    for key in array_enfants:
        inscrit = database.creche.GetInscrit(key)
        if inscrit:
            for date in array_enfants[key]:
                if not database.creche.cloture_facturation or date not in inscrit.clotures:
                    AddPeriodes(inscrit, date, array_enfants[key][date])
        else:
            errors.append("Inscrit %d: Inconnu!" % key)
    for key in array_salaries:
        salarie = database.creche.GetSalarie(key)
        if salarie:
            for date in array_salaries[key]:
                # print(key, GetPrenomNom(salarie), periode)
                AddPeriodes(salarie, date, array_salaries[key][date])
        else:
            errors.append("Salarié %d: Inconnu!" % key)

    database.commit()
    return errors


def sync_tablette(traces=False):
    print("Synchro tablette ...")

    journal = config.connection.LoadJournal()
    if not journal:
        return

    lines = journal.split("\n")

    index = -1
    if len(database.creche.last_tablette_synchro) > 20:
        try:
            index = lines.index(database.creche.last_tablette_synchro)
        except:
            pass

    if config.saas_port:
        import pytz
        tz = pytz.timezone('Europe/Paris')
    else:
        tz = None
    sync_tablette_lines(lines[index + 1:], tz, traces=traces)


if __name__ == "__main__":
    config.load(sys.argv[1])
    config.connection = get_connection_from_config()
    database.init(config.database)
    database.load()

    database.creche.last_tablette_synchro = sys.argv[2]
    sync_tablette(traces=True)
