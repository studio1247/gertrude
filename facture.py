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
from constants import *
from cotisation import *

class Facture(object):
    def __init__(self, inscrit, annee, mois, options=0):
        self.inscrit = inscrit
        self.annee = annee
        self.mois = mois
        self.debut = datetime.date(annee, mois, 1)
        self.fin = getMonthEnd(self.debut)
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.heures_facturees = [0.0, 0.0]
        self.supplement = 0
        self.deduction = 0
        self.jours_supplementaires = []
        self.heures_mensuelles = 0.0
        self.heures_supplementaires = 0.0
        self.jours_maladie = []
        self.jours_maladie_deduits = []
        self.raison_deduction = ""
        self.previsionnel = False

        jours_ouvres = 0
        jours_fermeture = 0
        cotisations_mensuelles = {}
        heures_hebdomadaires = {}

        date = datetime.date(annee, mois, 1)
        while date.month == mois:
            if not date in creche.jours_fermeture:
                jours_ouvres += 1
                if inscrit.getInscription(date):
                    cotisation = Cotisation(inscrit, (date, date), options=NO_ADDRESS|self.options)
                    heures_presence = cotisation.inscription.getReferenceDay(date).get_heures()
                    if (cotisation.mode_inscription, cotisation.cotisation_mensuelle) in cotisations_mensuelles:
                        cotisation = cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)]
                        cotisation.heures_presence += heures_presence
                    else:
                        cotisation.heures_presence = heures_presence
                        cotisation.heures_maladie = 0.0
                        cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)] = cotisation
                    if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                    else:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                    presence, supplement = inscrit.getState(date)
                    if presence == MALADE:
                        self.jours_maladie.append(date)
                        # recherche du premier et du dernier jour
                        premier_jour_maladie = tmp = date
                        while tmp >= inscrit.inscriptions[0].debut and inscrit.getState(tmp)[0] in (MALADE, ABSENT):
                            tmp -= datetime.timedelta(1)
                            if inscrit.getState(tmp)[0] == MALADE:
                                premier_jour_maladie = tmp
                        dernier_jour_maladie = tmp = date
                        while (not inscrit.inscriptions[-1].fin or tmp <= inscrit.inscriptions[-1].fin) and inscrit.getState(tmp)[0] in (MALADE, ABSENT):
                            tmp += datetime.timedelta(1)
                            if inscrit.getState(tmp)[0] == MALADE:
                                dernier_jour_maladie = tmp

                        if creche.mode_facturation & DEDUCTION_MALADIE_AVEC_CARENCE:
                            nb_jours_maladie = date - premier_jour_maladie + datetime.timedelta(1)
                        else:
                            nb_jours_maladie = dernier_jour_maladie - premier_jour_maladie + datetime.timedelta(1)
                            
                        if nb_jours_maladie > datetime.timedelta(creche.minimum_maladie):
                            self.jours_maladie_deduits.append(date)
                            if creche.mode_facturation & FACTURATION_PSU:
                                self.deduction += cotisation.montant_heure_garde * heures_presence
                            else:
                                self.deduction += cotisation.montant_jour_garde
                            cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)].heures_maladie += heures
                            self.raison_deduction = u'(maladie > %dj consécutifs)' % creche.minimum_maladie
                    elif presence > 0:
                        if presence & PREVISIONNEL:
                            self.previsionnel = True
                        if presence & SUPPLEMENT:
                            self.jours_supplementaires.append(date)
                            if not creche.mode_facturation & FACTURATION_PSU:
                                self.supplement += cotisation.montant_jour_garde
                        if creche.mode_facturation & FACTURATION_PSU:
                            self.heures_supplementaires += supplement
                            self.supplement += cotisation.montant_heure_garde * supplement

            date += datetime.timedelta(1)

        for mode_inscription, montant in cotisations_mensuelles:
            cotisation = cotisations_mensuelles[mode_inscription, montant]
            cotisation.heures_mensuelles = 0.0
            date = datetime.date(annee, mois, 1)
            while date.month == mois:
                if date not in creche.jours_fermeture:
                    cotisation.heures_mensuelles += cotisation.inscription.getReferenceDay(date).get_heures()
                date += datetime.timedelta(1)
            self.heures_mensuelles += cotisation.heures_mensuelles
            prorata = montant * cotisation.heures_presence / cotisation.heures_mensuelles
            self.cotisation_mensuelle += prorata
            
            if creche.mode_facturation & FACTURATION_PSU:
                self.heures_facturees[mode_inscription] += cotisation.heures_mensuelles + self.heures_supplementaires
            else:
                prorata_heures = cotisation.heures_mois * cotisation.heures_presence / cotisation.heures_mensuelles
                self.heures_facturees[mode_inscription] += prorata_heures

        self.total = self.cotisation_mensuelle + self.supplement - self.deduction
