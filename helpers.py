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
from __future__ import division
from builtins import str
import datetime
import unicodedata
from constants import *


def is_power_of_two(x):
    return (x != 0) and (x & (x - 1)) == 0


def Number2String(value):
    if isinstance(value, float):
        return "%.2f" % value
    else:
        return "%d" % value


def GetDeStr(s):
    if len(s) > 0 and s[0].lower() in ('a', 'e', 'i', 'o', 'u'):
        return "d'" + s
    else:
        return "de " + s


def GetDeMoisStr(mois):
    return GetDeStr(months[mois].lower())


def GetBoolStr(val):
    if val:
        return "OUI"
    else:
        return "NON"


def date2str(date):
    try:
        return '%.02d/%.02d/%.04d' % (date.day, date.month, date.year)
    except:
        return ''


def GetPeriodeString(o):
    if not o.debut and not o.fin:
        return "Toujours"
    elif o.debut and not o.fin:
        return "A partir du " + date2str(o.debut)
    elif o.fin and not o.debut:
        return "Jusqu'au " + date2str(o.fin)
    elif o.debut == datetime.date(o.fin.year, 1, 1) and o.fin == datetime.date(o.debut.year, 12, 31):
        return "Année %d" % o.debut.year
    else:
        return date2str(o.debut) + ' - ' + date2str(o.fin)


def GetYearStart(date):
    return datetime.date(date.year, 1, 1)


def GetYearEnd(date):
    return datetime.date(date.year, 12, 31)


def IncrDate(date, years=0, months=0, days=0):
    day, month, year = date.day + days, date.month + months, date.year + years
    while month > 12:
        year += 1
        month -= 12
    while month <= 0:
        year -= 1
        month += 12
    return datetime.date(year, month, 1) + datetime.timedelta(day - 1)


def GetDateAnniversaire(date, count=1):
    return IncrDate(date, years=count)


def GetMonthStart(date):
    return datetime.date(date.year, date.month, 1)


def GetMonthEnd(date):
    if date.month == 12:
        return datetime.date(date.year, 12, 31)
    else:
        return datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(1)


def GetMonthDaysCount(date):
    return (GetNextMonthStart(date) - GetMonthStart(date)).days


def GetNextMonthStart(date):
    if date.month == 12:
        return datetime.date(date.year+1, 1, 1)
    else:
        return datetime.date(date.year, date.month+1, 1)


def GetDurationMonths(start, end):
    if start and end:
        return end.year * 12 + end.month - start.year * 12 - start.month + 1
    else:
        return None


def GetTrimestreStart(date):
    return datetime.date(date.year, 1 + 3 * ((date.month - 1) // 3), 1)


def GetTrimestreEnd(date):
    nextTrimestre = GetTrimestreStart(date) + datetime.timedelta(80)
    return GetTrimestreStart(nextTrimestre) - datetime.timedelta(1)


def str2date(string, year=None, day=None):
    s = string.strip()
    if s.count("-") == 2:
        year, month, day = s.split("-")
        if not day.isdigit() or not month.isdigit() or not year.isdigit():
            return None
        day, month, year = int(day), int(month), int(year)
    elif s.count("/") == 2:
        day, month, year = s.split("/")
        if not day.isdigit() or not month.isdigit() or not year.isdigit():
            return None
        day, month, year = int(day), int(month), int(year)
    elif year and s.count("/") == 1:
        day, month = s.split("/")
        if not day.isdigit() or not month.isdigit():
            return None
        day, month = int(day), int(month)
    elif day and s.count("/") == 1:
        month, year = map(lambda x: x, s.split("/"))
        if not month.isdigit() or not year.isdigit():
            return None
        month, year = int(month), int(year)
    else:
        return None
    if year < 1900:
        return None
    else:
        return datetime.date(year, month, day)


def GetDureeArrondie(mode, start, end):
    if start is None or end is None:
        return 0
    elif mode == ARRONDI_HEURE_ARRIVEE_DEPART:
        return (((end + 11) // 12) - (start // 12)) * 12
    elif mode == ARRONDI_HEURE:
        return ((end - start + 11) // 12) * 12
    elif mode == ARRONDI_HEURE_MARGE_DEMI_HEURE:
        return ((end - start + 5) // 12) * 12
    elif mode == ARRONDI_DEMI_HEURE:
        return ((end - start + 5) // 6) * 6
    else:
        return end - start


def GetDureeArrondieHeures(mode, heures):
    return GetDureeArrondie(mode, 0, int(12 * heures)) / 12


def GetDateIntersection(periodes):
    for one in range(0, len(periodes)-1):
        i1 = periodes[one]
        if i1.debut:
            for two in range(one+1, len(periodes)):
                i2 = periodes[two]
                if i2.debut:
                    latest_start = max(i1.debut, i2.debut)
                    earliest_end = min(i1.GetFin(), i2.GetFin())
                    if (earliest_end - latest_start).days > 0:
                        return latest_start
    return None


def GetHeureString(value):
    # prend en paramètre une heure (float)
    if value is None:
        return ""
    minutes = round(value * 60)
    if value >= 0:
        heures = minutes // 60
        minutes -= heures * 60
        return "%dh%02d" % (heures, minutes)
    else:
        minutes = -minutes
        heures = (minutes // 60)
        minutes -= heures * 60
        return "-%dh%02d" % (heures, minutes)


def normalize_filename(filename):
    return unicodedata.normalize("NFKD", filename)


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def get_emails(str):
    if str is None:
        return []
    else:
        return [email.strip() for email in str.split(",") if email.strip() != ""]


def truncate(string, length):
    if len(string) > length:
        return string[:length] + "..."
    else:
        return string


def Select(obj, date):
    for o in obj:
        if (not o.debut or date >= o.debut) and (not o.fin or date <= o.fin):
            return o
    return None


def GetAge(naissance, date=datetime.date.today()):
    age = 0
    if naissance:
        age = (date.year - naissance.year) * 12 + date.month - naissance.month
        if date.day < naissance.day:
            age -= 1
    return age


def GetAgeString(naissance, date=datetime.date.today()):
    if naissance:
        age = GetAge(naissance, date)
        annees, mois = age / 12, age % 12
        if annees < 0:
            return ""
        elif annees and mois:
            return "%d ans et %d mois" % (annees, mois)
        elif annees:
            return "%d ans" % annees
        else:
            return "%d mois" % mois
    else:
        return ""


def GetDateString(date, weekday=True, annee=True):
    if date.day == 1:
        date_str = "1er %s" % (months[date.month - 1].lower())
    else:
        date_str = "%d %s" % (date.day, months[date.month - 1].lower())
    if annee:
        date_str += " %d" % date.year
    if weekday:
        return days[date.weekday()].lower() + " " + date_str
    else:
        return date_str