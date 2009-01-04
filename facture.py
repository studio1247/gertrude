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
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.detail_cotisation_mensuelle = [0.0, 0.0]
        self.heures_facturees = 0
        self.detail_heures_facturees = [0, 0]
        self.supplement = 0
        self.deduction = 0
        self.jours_supplementaires = []
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
            if date.weekday() < 5:
                if date in creche.jours_fermeture:
                    jours_fermeture += 1
                else:
                    jours_ouvres += 1
                    if inscrit.getInscription(date):
                        cotisation = Cotisation(inscrit, (date, date), options=NO_ADDRESS|self.options)
                        if (cotisation.mode_inscription, cotisation.cotisation_mensuelle) in cotisations_mensuelles:
                            cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)][0] += 1
                        else:
                            cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)] = [1, 0]
                        if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                            heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                        else:
                            heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                        presence = inscrit.getState(date)
                        if presence == MALADE:
                            self.jours_maladie.append(date)
                            # recherche du premier et du dernier jour
                            premier_jour_maladie = tmp = date
                            while tmp >= inscrit.inscriptions[0].debut and inscrit.getState(tmp) in (MALADE, ABSENT):
                                tmp -= datetime.timedelta(1)
                                if inscrit.getState(tmp) == MALADE:
                                    premier_jour_maladie = tmp
                            dernier_jour_maladie = tmp = date
                            while (not inscrit.inscriptions[-1].fin or tmp <= inscrit.inscriptions[-1].fin) and inscrit.getState(tmp) in (MALADE, ABSENT):
                                tmp += datetime.timedelta(1)
                                if inscrit.getState(tmp) == MALADE:
                                    dernier_jour_maladie = tmp

                            if creche.mode_maladie == DEDUCTION_TOTALE:
                                nb_jours_maladie = dernier_jour_maladie - premier_jour_maladie + datetime.timedelta(1)
                            else:
                                nb_jours_maladie = date - premier_jour_maladie + datetime.timedelta(1)
                            if nb_jours_maladie > datetime.timedelta(creche.minimum_maladie):
                                self.jours_maladie_deduits.append(date)
                                cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)][1] += 1
                                self.raison_deduction = u'(maladie > %dj consécutifs)' % creche.minimum_maladie
                        elif presence > 0:
                            if presence & PREVISIONNEL:
                                self.previsionnel = True
                            if presence & SUPPLEMENT:
                                self.jours_supplementaires.append(date)
                                self.supplement += cotisation.montant_jour_supplementaire

            date += datetime.timedelta(1)

        
        self.semaines_payantes = 4 - int(jours_fermeture / 5)

        for mode_inscription, cotisation in cotisations_mensuelles:
            cotisation_journaliere = cotisation * self.semaines_payantes / jours_ouvres / 4
            pro_rata = cotisation_journaliere * float(cotisations_mensuelles[mode_inscription, cotisation][0])
            self.cotisation_mensuelle += pro_rata
            self.detail_cotisation_mensuelle[mode_inscription] += pro_rata
            self.deduction += cotisation_journaliere * cotisations_mensuelles[mode_inscription, cotisation][1]

        heures_facturees = 0.0
        detail_heures_facturees = [0.0, 0.0]
        for mode_inscription, heures in heures_hebdomadaires:
            pro_rata = self.semaines_payantes * heures * float(heures_hebdomadaires[mode_inscription, heures]) / jours_ouvres
            heures_facturees += pro_rata
            detail_heures_facturees[mode_inscription] += pro_rata
        self.heures_facturees = int(heures_facturees)
        self.detail_heures_facturees = [int(h) for h in detail_heures_facturees]

        self.total = self.cotisation_mensuelle + self.supplement - self.deduction
