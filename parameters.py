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

import datetime
from paques import getPaquesDate
import __builtin__


def getWeekDays(year, weekday):
    result = []
    date = datetime.date(year, 1, 1)
    while date.weekday() != weekday:
        date += datetime.timedelta(1)
    while date <= datetime.date(year, 12, 31):
        result.append(date)
        date += datetime.timedelta(7)
    return result


def getWeekEnds(year):
    return getWeekDays(year, 5) +  getWeekDays(year, 6)

today = datetime.date.today()

# Jours fériés
jours_fermeture = []
jours_fermeture.append(("Week-end", lambda year: getWeekEnds(year), True))
jours_fermeture.append(("Lundi", lambda year: getWeekDays(year, 0), True))
jours_fermeture.append(("Mercredi", lambda year: getWeekDays(year, 2), True))
jours_fermeture.append(("1er janvier", lambda year: datetime.date(year, 1, 1), True))
jours_fermeture.append(("1er mai", lambda year: datetime.date(year, 5, 1), True))
jours_fermeture.append(("8 mai", lambda year: datetime.date(year, 5, 8), True))
jours_fermeture.append(("14 juillet", lambda year: datetime.date(year, 7, 14), True))
jours_fermeture.append(("15 août", lambda year: datetime.date(year, 8, 15), True))
jours_fermeture.append(("1er novembre", lambda year: datetime.date(year, 11, 1), True))
jours_fermeture.append(("11 novembre", lambda year: datetime.date(year, 11, 11), True))
jours_fermeture.append(("25 décembre", lambda year: datetime.date(year, 12, 25), True))
jours_fermeture.append(("Lundi de Pâques", lambda year: getPaquesDate(year) + datetime.timedelta(1), True))
jours_fermeture.append(("Jeudi de l'Ascension", lambda year: getPaquesDate(year) + datetime.timedelta(39), True))
jours_fermeture.append(("Lundi de Pentecôte", lambda year: getPaquesDate(year) + datetime.timedelta(50), False))

