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

class FactureFinMois(object):
    def __init__(self, inscrit, annee, mois, options=0):
        self.inscrit = inscrit
        self.annee = annee
        self.mois = mois
        self.debut_recap = datetime.date(annee, mois, 1)
        self.fin_recap = getMonthEnd(self.debut_recap)
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.heures_facturees = [0.0, 0.0]
        self.heures_contractualisees = 0.0
        self.heures_realisees = 0.0
        self.supplement = 0
        self.deduction = 0
        self.jours_supplementaires = []
        self.heures_contrat = 0.0
        self.heures_supplementaires = 0.0
        self.jours_maladie = []
        self.jours_maladie_deduits = []
        self.raison_deduction = ""
        self.supplement_activites = 0.0
        self.previsionnel = False

        jours_ouvres = 0
        jours_fermeture = 0
        cotisations_mensuelles = {}
        heures_hebdomadaires = {}
        last_cotisation = None

        date = datetime.date(annee, mois, 1)
        while date.month == mois:
            if not date in creche.jours_fermeture:
                jours_ouvres += 1
                inscription = inscrit.getInscription(date)
                if inscription:
                    if last_cotisation and last_cotisation.Include(date):
                        cotisation = last_cotisation
                    else:
                        cotisation = Cotisation(inscrit, (date, date), options=NO_ADDRESS|self.options)
                        last_cotisation = cotisation
                        if options & TRACES: print "cotisation mensuelle à partir de %s" % date, cotisation.cotisation_mensuelle
                        
                    state, heures_reference, heures_realisees, heures_supplementaires = inscrit.getState(date)
                    
                    self.heures_contractualisees += heures_reference
                    self.heures_realisees += heures_realisees
                    self.heures_facturees[cotisation.mode_inscription] += heures_reference + heures_supplementaires
                                       
                    if (cotisation.mode_inscription, cotisation.cotisation_mensuelle) in cotisations_mensuelles:
                        cotisation = cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)]
                        cotisation.heures_reference += heures_reference
                    else:
                        cotisation.heures_reference = heures_reference
                        cotisation.heures_maladie = 0.0
                        cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)] = cotisation
                    if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                    else:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                    if state == MALADE:
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

                        if creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE:
                            nb_jours_maladie = date - premier_jour_maladie + datetime.timedelta(1)
                        else:
                            nb_jours_maladie = dernier_jour_maladie - premier_jour_maladie + datetime.timedelta(1)
                            
                        if nb_jours_maladie > datetime.timedelta(creche.minimum_maladie):
                            self.jours_maladie_deduits.append(date)
                            if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                self.deduction += cotisation.montant_jour_garde
                            else:
                                self.deduction += cotisation.montant_heure_garde * heures_reference
                            cotisations_mensuelles[(cotisation.mode_inscription, cotisation.cotisation_mensuelle)].heures_maladie += heures_reference
                            self.raison_deduction = u'(maladie > %dj consécutifs)' % creche.minimum_maladie
                    elif state > 0:
                        if state & PREVISIONNEL:
                            self.previsionnel = True
                        if state & SUPPLEMENT:
                            self.jours_supplementaires.append(date)
                            if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                self.supplement += cotisation.montant_jour_garde
                        if creche.mode_facturation != FACTURATION_FORFAIT_10H:
                            self.heures_supplementaires += heures_supplementaires
                            self.supplement += cotisation.montant_heure_garde * heures_supplementaires
                        if creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE or (creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE_PERIODE_ESSAI and inscription.fin_periode_essai and date >= inscription.debut and date < inscription.fin_periode_essai):
                            activites = inscrit.getActivites(date)
                            for index in activites:
                                activite = creche.activites[index]
                                self.supplement_activites += activite.tarif
                    
            date += datetime.timedelta(1)
            
        self.total_realise = self.heures_realisees * cotisation.montant_heure_garde

        for mode_inscription, montant in cotisations_mensuelles:
            cotisation = cotisations_mensuelles[mode_inscription, montant]
            self.cotisation_mensuelle += montant * cotisation.heures_reference / self.heures_contractualisees
            self.heures_contrat += cotisation.heures_mois * cotisation.heures_reference / self.heures_contractualisees
        
        if self.heures_contrat > 0:
            self.tarif_horaire = self.cotisation_mensuelle / self.heures_contrat
        else:
            self.tarif_horaire = 0
        
        if creche.mode_facturation == FACTURATION_PSU: # on arrondit parce qu'ils veulent des multiplications avec chiffres arrondis !!!
            self.tarif_horaire = round(self.tarif_horaire, 2)
            self.cotisation_mensuelle = self.tarif_horaire * self.heures_contrat
            self.supplement = round(self.supplement, 2) # normalement pas necessaire
            self.deduction = round(self.deduction, 2) # normalement pas necessaire
            
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        if options & TRACES: print "cotisation mensuelle", self.cotisation_mensuelle
        
        if 0:
            print inscrit.prenom
            for var in ["heures_contrat", "heures_facturees", "heures_supplementaires", "tarif_horaire", "cotisation_mensuelle", "supplement", "deduction", "total"]:
                print " ", var, eval("self.%s" % var)
                
class FactureDebutMois(FactureFinMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureFinMois.__init__(self, inscrit, annee, mois, options)
        if mois == 1:
            facture_precedente = FactureFinMois(inscrit, annee-1, 12, options)
        else:
            facture_precedente = FactureFinMois(inscrit, annee, mois-1, options)
        self.debut_recap = facture_precedente.debut_recap
        self.fin_recap = facture_precedente.fin_recap
        # self.heures_facturees = [0.0, 0.0]
        self.supplement = facture_precedente.supplement
        self.deduction = facture_precedente.deduction
        self.jours_supplementaires = facture_precedente.jours_supplementaires
        # self.heures_contrat = 0.0
        self.heures_supplementaires = facture_precedente.heures_supplementaires
        self.jours_maladie = facture_precedente.jours_maladie
        self.jours_maladie_deduits = facture_precedente.jours_maladie_deduits
        self.raison_deduction = facture_precedente.raison_deduction
        self.supplement_activites = facture_precedente.supplement_activites
        self.previsionnel |= facture_precedente.previsionnel
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        
def Facture(inscrit, annee, mois, options=0):      
    if creche.temps_facturation == FACTURATION_FIN_MOIS:
        return FactureFinMois(inscrit, annee, mois, options)
    else:
        return FactureDebutMois(inscrit, annee, mois, options)           

