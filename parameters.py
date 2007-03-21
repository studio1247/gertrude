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


class Facture(object):
    def __init__(self, inscrit, annee, mois):
        self.inscrit = inscrit
        self.annee = annee
        self.mois = mois
        self.cotisation_mensuelle = 0.0
        self.supplement = 0
        self.deduction = 0
        self.jours_supplementaires = []
        self.jours_maladie = []
        self.jours_maladie_deduits = []

        jours = 0
        cotisations_mensuelles = {}
        heures_hebdomadaires = {}

        date = datetime.date(annee, mois, 1)
        while date.month == mois:
            if date.weekday() < 5:
                if not date in [j[1]for j in jours_feries]:
                    jours += 1
                    if inscrit.getInscription(date):
                        cotisation = Cotisation(creche, inscrit, (date, date))
                        if cotisation.cotisation_mensuelle in cotisations_mensuelles:
                            cotisations_mensuelles[cotisation.cotisation_mensuelle] += 1
                        else:
                            cotisations_mensuelles[cotisation.cotisation_mensuelle] = 1
                        if cotisation.total_semaine in heures_hebdomadaires:
                            heures_hebdomadaires[cotisation.total_semaine] += 1
                        else:
                            heures_hebdomadaires[cotisation.total_semaine] = 1

                        presence = inscrit.getPresence(date)
                        if presence == SUPPLEMENT:
                            self.jours_supplementaires.append(date)
                            self.supplement += cotisation.montant_jour_supplementaire
                        elif presence == MALADE:
                            self.jours_maladie.append(date)
                            tmp = date - datetime.timedelta(1)
                            while date - tmp < datetime.timedelta(15):
                                presence_tmp = inscrit.getPresence(tmp)
                                if presence_tmp == PRESENT or presence_tmp == VACANCES:
                                    break
                                tmp -= datetime.timedelta(1)
                            else:
                                self.jours_maladie_deduits.append(date)
                                self.deduction += cotisation.montant_jour_supplementaire
            date += datetime.timedelta(1)

#        for conge in creche.conges:
#            if conge.debut 
        for tmp in cotisations_mensuelles:
            self.cotisation_mensuelle += tmp * float(cotisations_mensuelles[tmp]) / jours

        heures_facturees = 0.0
        for tmp in heures_hebdomadaires:
            heures_facturees += 4 * tmp * float(heures_hebdomadaires[tmp]) / jours
        self.heures_facturees = int(heures_facturees)
