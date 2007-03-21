# -*- coding: cp1252 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import datetime
from paques import getPaquesDate

# Période de visualisation
today = datetime.date.today()
first_date = today - datetime.timedelta(12*30)
last_date = today + datetime.timedelta(6*30)

# Paramètres d'affichage du planning
heureOuverture = 7.75
heureFermeture = 18.5
heureAffichageMin = 7.75
heureAffichageMax = 20
heureGranularite = 4 # au quart d'heure

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

# Tranches horaires
tranches = [(heureOuverture, 12, 4), (12, 14, 2), (14, heureFermeture, 4)]

def get_total_heures_jour(presence):
    # Total en tout ou rien
    if self.value == 0:
        for i in self.details:
            if i != 0:
                return sum([t[2] for t in tranches])
    return 0
##    # Total en tranches
##    total = 0
##    if self.value == 0:
##        for debut, fin, valeur in tranches:
##            for i in self.details[int((debut-BASE_MIN_HOUR) * 4), int((fin-BASE_MIN_HOUR) * 4)]:
##                if i != 0:
##                    total += valeur
##                    break
##    return total



