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

import __builtin__
import datetime
from parameters import today
from functions import GetInscriptions
from sqlobjects import Alerte

def GetAlertes():
    alertes = []
    for inscription in GetInscriptions(today, today):
        inscrit = inscription.inscrit
        if inscrit.naissance:
            if inscrit.naissance.month > 3:
                date = datetime.date(inscrit.naissance.year+3, inscrit.naissance.month-3, inscrit.naissance.day)
            else:
                date = datetime.date(inscrit.naissance.year+2, inscrit.naissance.month+9, inscrit.naissance.day)
            texte = "%s %s a 3 ans le %02d/%02d/%04d" % (inscrit.prenom, inscrit.nom, inscrit.naissance.day, inscrit.naissance.month, inscrit.naissance.year+3)      
            alertes.append((date, texte))
        if inscription.debut and inscription.debut.year != today.year:
            date = datetime.date(today.year, inscription.debut.month, inscription.debut.day)
            texte = "l'inscription de %s %s passe un an au %02d/%02d/%04d" % (inscrit.prenom, inscrit.nom, date.day, date.month, date.year)
            alertes.append((date, texte))
    return alertes

def CheckAlertes():
    nouvelles_alertes = []
    for date, texte in GetAlertes():
        if date <= today and not texte in creche.alertes:
            alerte = Alerte(date, texte, creation=False)
            nouvelles_alertes.append(alerte)
            creche.alertes[texte] = alerte
                
    alertes_non_acquittees = [alerte for alerte in creche.alertes.values() if not alerte.acquittement]
    alertes_non_acquittees.sort(key=lambda alerte: alerte.date)    
    return nouvelles_alertes, alertes_non_acquittees
    
if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
    
    CheckAlarms()