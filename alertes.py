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

import __builtin__
from constants import *
import datetime
from functions import GetInscriptions, GetDateMinus


def GetAlertes():
    alertes = []
    def add_alerte(date, message):
        alertes.append((date, message, message in creche.alertes))
    today = datetime.date.today()
    for inscription in GetInscriptions(today, today):
        inscrit = inscription.inscrit
        if (creche.masque_alertes & ALERTE_3MOIS_AVANT_AGE_MAXIMUM) and inscrit.naissance:
            date = GetDateMinus(inscrit.naissance, years=-creche.age_maximum, months=3)
            if today > date:
                message = "%s %s aura %d ans dans 3 mois" % (inscrit.prenom, inscrit.nom, creche.age_maximum)
                add_alerte(date, message)
        if (creche.masque_alertes & ALERTE_1AN_APRES_INSCRIPTION) and inscription.debut:
            date = datetime.date(inscription.debut.year+1, inscription.debut.month, inscription.debut.day)
            if today > date:
                message = "L'inscription de %s %s passe un an aujourd'hui" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)
        if (creche.masque_alertes & ALERTE_2MOIS_AVANT_FIN_INSCRIPTION) and inscription.fin:
            date = GetDateMinus(inscription.fin, years=0, months=2)
            if today > date:
                message = "L'inscription de %s %s se terminera dans 2 mois" % (inscrit.prenom, inscrit.nom)
                add_alerte(date, message)
    alertes.sort(key=lambda (date, message, ack): date)
    return alertes

