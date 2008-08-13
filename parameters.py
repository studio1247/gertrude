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

import datetime
from paques import getPaquesDate

# Période de visualisation
today = datetime.date.today()
first_date = today - datetime.timedelta(12*30)
last_date = today + datetime.timedelta(6*30)

# Jours fériés
jours_feries = []
jours_feries.append(("1er janvier", lambda year: datetime.date(year, 1, 1)))
jours_feries.append(("1er mai", lambda year: datetime.date(year, 5, 1)))
jours_feries.append(("8 mai", lambda year: datetime.date(year, 5, 8)))
jours_feries.append(("14 juillet", lambda year: datetime.date(year, 7, 14)))
jours_feries.append((u"15 août", lambda year: datetime.date(year, 8, 15)))
jours_feries.append(("1er novembre", lambda year: datetime.date(year, 11, 1)))
jours_feries.append(("11 novembre", lambda year: datetime.date(year, 11, 11)))
jours_feries.append((u"25 décembre", lambda year: datetime.date(year, 12, 25)))
jours_feries.append((u"Lundi de Pâques", lambda year: getPaquesDate(year) + datetime.timedelta(1)))
jours_feries.append(("Jeudi de l'Ascension", lambda year: getPaquesDate(year) + datetime.timedelta(39)))
# jours_feries.append((u"Lundi de Pentecôte", lambda year: paques + datetime.timedelta(50)))

