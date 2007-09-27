# -*- coding: utf8 -*-

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
from constants import *
from cotisation import *

class Facture(object):
    def __init__(self, inscrit, annee, mois):
        self.inscrit = inscrit
        self.annee = annee
        self.mois = mois
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
                        cotisation = Cotisation(inscrit, (date, date), options=NO_ADDRESS)
                        if (cotisation.mode_garde, cotisation.cotisation_mensuelle) in cotisations_mensuelles:
                            cotisations_mensuelles[(cotisation.mode_garde, cotisation.cotisation_mensuelle)] += 1
                        else:
                            cotisations_mensuelles[(cotisation.mode_garde, cotisation.cotisation_mensuelle)] = 1
                        if (cotisation.mode_garde, cotisation.total_semaine) in heures_hebdomadaires:
                            heures_hebdomadaires[(cotisation.mode_garde, cotisation.total_semaine)] += 1
                        else:
                            heures_hebdomadaires[(cotisation.mode_garde, cotisation.total_semaine)] = 1

                        presence, previsionnel = inscrit.getPresence(date)
                        if previsionnel:
                            self.previsionnel = True
                        if presence == SUPPLEMENT:
                            self.jours_supplementaires.append(date)
                            self.supplement += cotisation.montant_jour_supplementaire
                        elif presence == MALADE:
                            self.jours_maladie.append(date)
                            tmp = date - datetime.timedelta(1)
                            while date - tmp < datetime.timedelta(15):
                                presence_tmp = inscrit.getPresence(tmp)[0]
                                if presence_tmp == PRESENT or presence_tmp == VACANCES:
                                    break
                                tmp -= datetime.timedelta(1)
                            else:
                                self.jours_maladie_deduits.append(date)
                                self.deduction += cotisation.montant_jour_supplementaire
                                self.raison_deduction = u'(maladie > 15j consécutifs)'
            date += datetime.timedelta(1)

        self.semaines_payantes = 4 - int(jours_fermeture / 5)

        for mode_garde, cotisation in cotisations_mensuelles:
            pro_rata = cotisation * self.semaines_payantes * float(cotisations_mensuelles[mode_garde, cotisation]) / jours_ouvres / 4
            self.cotisation_mensuelle += pro_rata
            self.detail_cotisation_mensuelle[mode_garde] += pro_rata

        heures_facturees = 0.0
        detail_heures_facturees = [0.0, 0.0]
        for mode_garde, heures in heures_hebdomadaires:
            pro_rata = self.semaines_payantes * heures * float(heures_hebdomadaires[mode_garde, heures]) / jours_ouvres
            heures_facturees += pro_rata
            detail_heures_facturees[mode_garde] += pro_rata
        self.heures_facturees = int(heures_facturees)
        self.detail_heures_facturees = [int(h) for h in detail_heures_facturees]

        self.total = self.cotisation_mensuelle + self.supplement - self.deduction
