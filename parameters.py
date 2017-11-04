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
    return getWeekDays(year, 5) + getWeekDays(year, 6)


today = datetime.date.today()

# Jours fériés
jours_fermeture = [("Week-end", lambda year: getWeekEnds(year), True),
                   ("Lundi", lambda year: getWeekDays(year, 0), True),
                   ("Mercredi", lambda year: getWeekDays(year, 2), True),
                   ("1er janvier", lambda year: [datetime.date(year, 1, 1)], True),
                   ("1er mai", lambda year: [datetime.date(year, 5, 1)], True),
                   ("8 mai", lambda year: [datetime.date(year, 5, 8)], True),
                   ("14 juillet", lambda year: [datetime.date(year, 7, 14)], True),
                   ("15 août", lambda year: [datetime.date(year, 8, 15)], True),
                   ("1er novembre", lambda year: [datetime.date(year, 11, 1)], True),
                   ("11 novembre", lambda year: [datetime.date(year, 11, 11)], True),
                   ("25 décembre", lambda year: [datetime.date(year, 12, 25)], True),
                   ("Lundi de Pâques", lambda year: [getPaquesDate(year) + datetime.timedelta(1)], True),
                   ("Jeudi de l'Ascension", lambda year: [getPaquesDate(year) + datetime.timedelta(39)], True),
                   ("Lundi de Pentecôte", lambda year: [getPaquesDate(year) + datetime.timedelta(50)], False)
                   ]
