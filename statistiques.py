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

from constants import *
from functions import *
from facture import *


class Statistiques(object):
    def __init__(self):
        self.heures_contrat = 0.0
        self.heures_reel = 0.0
        self.heures_facture = 0.0
        self.jours_contrat = 0
        self.jours_reel = 0
        self.jours_facture = 0
        self.cotisations_contrat = 0.0
        self.cotisations_reel = 0.0
        self.cotisations_facture = 0.0
        self.heures_accueil = 0.0
        self.percent_contrat = 0.0
        self.percent_reel = 0.0
        self.percent_facture = 0.0
        self.bargraph = [[0.0 for i in range(12)] for j in range(3)]
        self.bargraph_year = 0
        self.erreurs = {}


def GetStatistiques(start, end, site=None, bargraph=False):
    result = Statistiques()
    if bargraph:
        debut = datetime.date(start.year, 1, 1)
        fin = datetime.date(start.year, 12, 31)
        result.bargraph_year = start.year
    else:
        debut = start
        fin = end
    date = debut
    while date <= fin:
        print("[Statistiques %s %d]" % (months[date.month-1], date.year))
        fin_mois = GetMonthEnd(date)
        if start <= date <= end:
            result.heures_accueil += GetHeuresAccueil(date.year, date.month, site)
        for inscrit in database.creche.inscrits:
            try:
                # TODO il y a un problème pour les crèches en facturation debut de mois, le total_facture ! total
                inscriptions = inscrit.get_inscriptions(date, fin_mois)
                if inscriptions and (site is None or inscriptions[0].site == site):
                    if database.creche.nom in ("Les Renardeaux", "Les ptits loups"):
                        facture_heures = FactureFinMois(inscrit, date.year, date.month, NO_NUMERO)
                        next_month = GetNextMonthStart(date)
                        if next_month in inscrit.clotures:
                            facture = Facture(inscrit, next_month.year, next_month.month, NO_NUMERO)
                        else:
                            facture = facture_heures
                    else:
                        facture = Facture(inscrit, date.year, date.month, NO_NUMERO)
                        facture_heures = facture
                    if config.options & HEURES_CONTRAT:
                        heures_contrat = facture_heures.heures_contrat
                        heures_facture = facture_heures.heures_facture
                    else:
                        heures_contrat = facture_heures.heures_contractualisees
                        heures_facture = facture_heures.heures_facturees
                    if start <= date <= end:
                        result.heures_contrat += heures_contrat
                        result.heures_reel += facture_heures.heures_realisees
                        result.heures_facture += heures_facture
                        result.jours_contrat += facture_heures.jours_contractualises
                        result.jours_reel += facture_heures.jours_realises
                        result.jours_facture += facture_heures.jours_factures
                        result.cotisations_contrat += facture.total_contractualise
                        result.cotisations_reel += facture.total_realise
                        result.cotisations_facture += facture.total_facture
                        print(GetPrenomNom(inscrit), "au", facture.date)
                        print(' ', "heures contractualisées :", facture_heures.heures_contractualisees, ", heures contrat :", facture_heures.heures_contrat)
                        print(' ', "heures réalisées :", facture_heures.heures_realisees)
                        print(' ', "heures facturées :", facture_heures.heures_facturees, ", heures facture :", facture_heures.heures_facture, "=>", heures_facture)
                        print(' ', "jours contractualisés :", facture_heures.jours_contractualises)
                        print(' ', "jours réalisés :", facture_heures.jours_realises)
                        print(' ', "jours facturés :", facture_heures.jours_factures)
                        print(' ', "total contractualisé", facture.total_contractualise)
                        print(' ', "total réalisé :", facture.total_realise)
                        print(' ', "total facturé :", facture.total_facture)
                    result.bargraph[0][date.month-1] += heures_contrat
                    result.bargraph[1][date.month-1] += facture_heures.heures_realisees
                    result.bargraph[2][date.month-1] += heures_facture
            except CotisationException as e:
                if date <= datetime.date.today():
                    result.erreurs[GetPrenomNom(inscrit)] = e.errors
        date = fin_mois + datetime.timedelta(1)

    if result.heures_accueil:
        result.percent_contrat = (100.0 * result.heures_contrat) / result.heures_accueil
        result.percent_reel = (100.0 * result.heures_reel) / result.heures_accueil
        result.percent_facture = (100.0 * result.heures_facture) / result.heures_accueil

    return result
