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
        self.erreurs = {}


def GetStatistiques(start, end, site=None):
    result = Statistiques()
    debut = start
    while debut < end:
        fin = GetMonthEnd(debut)
        result.heures_accueil += GetHeuresAccueil(debut.year, debut.month, site)
        print "[Statistiques %s %d]" % (months[debut.month-1], debut.year)
        for inscrit in creche.inscrits:
            try:
                inscriptions = inscrit.GetInscriptions(debut, fin)
                if inscriptions and (site is None or inscriptions[0].site == site):
                    facture = Facture(inscrit, debut.year, debut.month, NO_NUMERO)
                    if config.options & HEURES_CONTRAT:
                        result.heures_contrat += facture.heures_contrat
                        result.heures_facture += facture.heures_facture
                    else:
                        result.heures_contrat += facture.heures_contractualisees
                        result.heures_facture += facture.heures_facturees
                    result.heures_reel += facture.heures_realisees
                    result.jours_contrat += facture.jours_contractualises
                    result.jours_reel += facture.jours_realises
                    result.jours_facture += facture.jours_factures
                    result.cotisations_contrat += facture.total_contractualise
                    result.cotisations_reel += facture.total_realise
                    result.cotisations_facture += facture.total_facture
                    print inscrit.prenom, inscrit.nom, facture.date
                    print ' ', "heures contractualisées :", facture.heures_contractualisees, ", heures contrat :", facture.heures_contrat
                    print ' ', "heures réalisées :", facture.heures_realisees
                    print ' ', "heures facturées :", facture.heures_facturees, ", heures facture :", facture.heures_facture
                    print ' ', "jours contractualisés :", facture.jours_contractualises
                    print ' ', "jours réalisés :", facture.jours_realises
                    print ' ', "jours facturés :", facture.jours_factures
                    print ' ', "total contractualisé", facture.total_contractualise
                    print ' ', "total réalisé :", facture.total_realise
                    print ' ', "total facturé :", facture.total_facture
            except CotisationException as e:
                result.erreurs[GetPrenomNom(inscrit)] = e.errors
        debut = fin + datetime.timedelta(1)

    if result.heures_accueil:
        result.percent_contrat = (100.0 * result.heures_contrat) / result.heures_accueil
        result.percent_reel = (100.0 * result.heures_reel) / result.heures_accueil
        result.percent_facture = (100.0 * result.heures_facture) / result.heures_accueil

    return result
