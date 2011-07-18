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
        self.date = self.fin_recap
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.report_cotisation_mensuelle = 0.0
        self.heures_facturees_par_mode = [0.0] * 33
        self.heures_contractualisees = 0.0
        self.heures_realisees = 0.0
        self.heures_previsionnelles = 0.0
        self.total_contractualise = 0.0
        self.total_realise = 0.0
        self.supplement = 0.0
        self.deduction = 0.0
        self.jours_presence_selon_contrat = {}
        self.jours_supplementaires = {}
        self.heures_supplementaires = 0.0
        self.jours_maladie = []
        self.jours_maladie_deduits = []
        self.jours_vacances = []
        self.raison_deduction = []
        self.supplement_activites = 0.0
        self.previsionnel = False
        self.cloture = False
        self.montant_heure_garde = 0.0

        jours_ouvres = 0
        jours_fermeture = 0
        cotisations_mensuelles = []
        heures_hebdomadaires = {}
        last_cotisation = None
        
        if creche.cloture_factures and today > self.fin_recap:
            fin = self.debut_recap - datetime.timedelta(1)
            debut = getMonthStart(fin) 
            if inscrit.GetInscriptions(debut, fin) and debut not in inscrit.factures_cloturees:
                error = u"La facture du mois " + GetDeMoisStr(debut.month-1) + " " + str(debut.year) + u" n'est pas clôturée"
                raise CotisationException([error])

        date = datetime.date(annee, mois, 1)
        while date.month == mois:
            if not (date in creche.jours_fermeture or date in inscrit.jours_conges):
                jours_ouvres += 1
                inscription = inscrit.GetInscription(date)
                if inscription:
                    state, heures_reference, heures_realisees, heures_supplementaires = inscrit.getState(date)
                    
                    if last_cotisation and last_cotisation.Include(date):
                        cotisation = last_cotisation
                        cotisation.jours_ouvres += 1
                        cotisation.heures_reference += heures_reference
                    else:
                        cotisation = Cotisation(inscrit, date, options=NO_ADDRESS|self.options)
                        cotisation.jours_ouvres = 1
                        cotisation.heures_reference = heures_reference
                        cotisation.heures_realisees = 0.0
                        cotisation.nombre_jours_maladie_deduits = 0
                        cotisation.heures_maladie = 0.0
                        cotisation.heures_contractualisees = 0.0
                        cotisation.heures_supplementaires = 0.0
                        cotisations_mensuelles.append(cotisation)
                        last_cotisation = cotisation
                        self.montant_heure_garde = cotisation.montant_heure_garde
                        if options & TRACES: print u"cotisation mensuelle à partir de %s" % date, cotisation.cotisation_mensuelle
                    
                    if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                    else:
                        heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                    if state == HOPITAL:
                        if heures_reference > 0:
                            self.jours_maladie.append(date)
                        self.jours_maladie_deduits.append(date)
                        cotisation.nombre_jours_maladie_deduits += 1
                        cotisation.heures_maladie += heures_reference
                        if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                            self.deduction += 10 * cotisation.montant_heure_garde
                        elif inscription.mode != MODE_FORFAIT_HORAIRE:
                            self.deduction += cotisation.montant_heure_garde * heures_reference                                
                        self.raison_deduction.append('hospitalisation')
                    elif state == MALADE:
                        if heures_reference > 0:
                            self.jours_maladie.append(date)
                        if creche.mode_facturation != FACTURATION_HORAIRES_REELS or inscription.mode == MODE_FORFAIT_HORAIRE:
                            # recherche du premier et du dernier jour
                            premier_jour_maladie = tmp = date
                            nombre_jours_ouvres_maladie = 0
                            while tmp > inscrit.inscriptions[0].debut:
                                if not tmp in creche.jours_fermeture:
                                    nombre_jours_ouvres_maladie += 1
                                tmp -= datetime.timedelta(1)
                                state = inscrit.getState(tmp)[0]
                                if state == MALADE:
                                    premier_jour_maladie = tmp
                                else:
                                    break
                            if creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES:
                                nb_jours_maladie = nombre_jours_ouvres_maladie
                            elif creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES:
                                nb_jours_maladie = (date - premier_jour_maladie).days + 1
                            else:
                                dernier_jour_maladie = tmp = date
                                while not inscrit.inscriptions[-1].fin or tmp < inscrit.inscriptions[-1].fin:
                                    tmp += datetime.timedelta(1)
                                    state = inscrit.getState(tmp)[0]
                                    if state == MALADE:
                                        dernier_jour_maladie = tmp
                                    else:
                                        break
                                nb_jours_maladie = (dernier_jour_maladie - premier_jour_maladie).days + 1
                            
                            if nb_jours_maladie > creche.minimum_maladie:
                                self.jours_maladie_deduits.append(date)
                                cotisation.nombre_jours_maladie_deduits += 1
                                cotisation.heures_maladie += heures_reference
                                if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                    self.deduction += 10 * cotisation.montant_heure_garde
                                elif inscription.mode != MODE_FORFAIT_HORAIRE:
                                    self.deduction += cotisation.montant_heure_garde * heures_reference                                
                                self.raison_deduction.append('maladie > %dj consécutifs' % creche.minimum_maladie)
                    elif state == VACANCES:
                        if heures_reference > 0:
                            self.jours_vacances.append(date)
                    elif state > 0:
                        if state & PREVISIONNEL:
                            self.previsionnel = True

                        if heures_supplementaires > 0:
                            self.jours_supplementaires[date] = heures_realisees
                        else:
                            self.jours_presence_selon_contrat[date] = heures_realisees
                            
                        if heures_supplementaires > 0:
                            if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                self.supplement += 10 * cotisation.montant_heure_garde
                            else:
                                cotisation.heures_supplementaires += heures_supplementaires
                                self.heures_supplementaires += heures_supplementaires
                                if creche.mode_facturation != FACTURATION_HORAIRES_REELS and (creche.facturation_periode_adaptation != FACTURATION_HORAIRES_REELS or not cotisation.inscription.IsInPeriodeAdaptation(date)):
                                    self.supplement += cotisation.montant_heure_garde * heures_supplementaires

                    if creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE or (creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION and inscription.IsInPeriodeAdaptation(date)):
                        activites = inscrit.GetExtraActivites(date)
                        for value in activites:
                            activite = creche.activites[value]
                            self.supplement_activites += activite.tarif

                    self.heures_realisees += heures_realisees
                    cotisation.heures_realisees += heures_realisees
                    if cotisation.inscription.mode != MODE_FORFAIT_HORAIRE:
                        cotisation.heures_contractualisees += heures_reference
                        self.heures_contractualisees += heures_reference
                        if creche.mode_facturation == FACTURATION_HORAIRES_REELS or (creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(date)) or (creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE):
                            self.heures_facturees_par_mode[cotisation.mode_garde] += heures_realisees
                            self.total_contractualise += heures_reference * cotisation.montant_heure_garde
                        else:
                            self.heures_facturees_par_mode[cotisation.mode_garde] += heures_reference + heures_supplementaires                    
                    self.total_realise += heures_realisees * cotisation.montant_heure_garde
                    
            date += datetime.timedelta(1)

        for cotisation in cotisations_mensuelles:
            if creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and cotisation.inscription.IsInPeriodeAdaptation(cotisation.debut):
                if cotisation.inscription.mode == MODE_FORFAIT_HORAIRE:
                    self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees 
                self.cotisation_mensuelle += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                self.report_cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_contractualisees) * cotisation.montant_heure_garde                
            elif cotisation.inscription.mode == MODE_FORFAIT_HORAIRE:
                self.cotisation_mensuelle += cotisation.cotisation_mensuelle * cotisation.jours_ouvres / jours_ouvres
                cotisation.heures_contractualisees = cotisation.inscription.forfait_heures_presence * cotisation.jours_ouvres / jours_ouvres
                self.heures_contractualisees += cotisation.heures_contractualisees
                self.total_contractualise += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                if cotisation.nombre_jours_maladie_deduits > 0:
                    self.deduction += montant * cotisation.nombre_jours_maladie_deduits / cotisation.jours_ouvres
                    heures_contractualisees = cotisation.heures_contractualisees * (cotisation.jours_ouvres - cotisation.nombre_jours_maladie_deduits) / cotisation.jours_ouvres
                else:
                    heures_contractualisees = cotisation.heures_contractualisees
                if cotisation.heures_realisees > heures_contractualisees:
                    cotisation.heures_supplementaires = cotisation.heures_realisees - heures_contractualisees
                    self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees 
                    self.heures_supplementaires += cotisation.heures_supplementaires
                    self.supplement += cotisation.heures_supplementaires * cotisation.montant_heure_garde
                else:
                    self.heures_facturees_par_mode[cotisation.mode_garde] += heures_contractualisees
            elif creche.mode_facturation == FACTURATION_HORAIRES_REELS:
                self.cotisation_mensuelle += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                self.report_cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_contractualisees) * cotisation.montant_heure_garde
            elif creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE and self.heures_contractualisees:
                # On ne met dans la cotisation mensuelle que les heures realisees des heures du contrat
                self.cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_supplementaires) * cotisation.montant_heure_garde
            elif self.heures_contractualisees:
                prorata = cotisation.cotisation_mensuelle * cotisation.heures_reference / self.heures_contractualisees   
                self.cotisation_mensuelle += prorata 
                self.total_contractualise += prorata
        
        self.heures_facturees = sum(self.heures_facturees_par_mode)
        if creche.temps_facturation == FACTURATION_FIN_MOIS:
            self.cotisation_mensuelle += self.report_cotisation_mensuelle
            self.report_cotisation_mensuelle = 0.0

        # arrondi de tous les champs en euros
        self.cotisation_mensuelle = round(self.cotisation_mensuelle, 2)
        self.report_cotisation_mensuelle = round(self.report_cotisation_mensuelle, 2)
        self.supplement = round(self.supplement, 2)
        self.supplement_activites = round(self.supplement_activites, 2)
        self.deduction = round(self.deduction, 2)
        if self.raison_deduction:
            self.raison_deduction = "(" + ", ".join(self.raison_deduction) + ")"
        else:
            self.raison_deduction = "" 
        self.total_contractualise = round(self.total_contractualise, 2)
        self.total_realise = round(self.total_realise, 2)
        
        if creche.majoration_localite and inscrit.majoration:
            self.majoration_mensuelle = creche.majoration_localite
        else:
            self.majoration_mensuelle = 0.0
        
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        self.total_facture = self.total + self.report_cotisation_mensuelle
        
        if options & TRACES:
            print inscrit.prenom
            for var in ["heures_contractualisees", "heures_facturees", "heures_supplementaires", "cotisation_mensuelle", "supplement", "deduction", "total"]:
                print " ", var, eval("self.%s" % var)
                
    def Cloture(self, date=None):
        if not self.cloture:
            if date is None:
                date = datetime.date(self.annee, self.mois, 1)
            self.cloture = True
            self.inscrit.factures_cloturees[date] = self
            if sql_connection:
                sql_connection.execute('INSERT INTO FACTURES (idx, inscrit, date, cotisation_mensuelle, total_contractualise, total_realise, total_facture, supplement_activites, supplement, deduction) VALUES (NULL,?,?,?,?,?,?,?,?,?)', (self.inscrit.idx, date, self.cotisation_mensuelle, self.total_contractualise, self.total_realise, self.total_facture, self.supplement_activites, self.supplement, self.deduction))
                history.append(None)
            
    def Restore(self):
        return self
    
class FactureDebutMois(FactureFinMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureFinMois.__init__(self, inscrit, annee, mois, options)
        self.heures_previsionnelles = self.heures_realisees
        
        if mois == 1:
            self.facture_precedente = FactureFinMois(inscrit, annee-1, 12, options)
        else:
            self.facture_precedente = FactureFinMois(inscrit, annee, mois-1, options)
        self.debut_recap = self.facture_precedente.debut_recap
        self.fin_recap = self.facture_precedente.fin_recap
        self.date = datetime.date(annee, mois, 1)
        self.jours_presence_selon_contrat = self.facture_precedente.jours_presence_selon_contrat
        self.jours_supplementaires = self.facture_precedente.jours_supplementaires
        self.heures_supplementaires = self.facture_precedente.heures_supplementaires
        self.jours_maladie = self.facture_precedente.jours_maladie
        self.jours_maladie_deduits = self.facture_precedente.jours_maladie_deduits
        self.jours_vacances = self.facture_precedente.jours_vacances
        self.raison_deduction = self.facture_precedente.raison_deduction
        self.previsionnel |= self.facture_precedente.previsionnel
        
class FactureDebutMoisContrat(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        self.cotisation_mensuelle += self.facture_precedente.report_cotisation_mensuelle
        self.supplement = self.facture_precedente.supplement
        self.deduction = self.facture_precedente.deduction
        self.supplement_activites = self.facture_precedente.supplement_activites
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction

class FactureDebutMoisPrevisionnel(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        
        if today > self.fin_recap:
            if inscrit.GetInscriptions(self.facture_precedente.debut_recap, self.facture_precedente.fin_recap):
                if self.facture_precedente.fin_recap not in inscrit.factures_cloturees:
                    error = u"La facture du mois " + GetDeMoisStr(self.facture_precedente.fin_recap.month-1) + " " + str(self.facture_precedente.fin_recap.year) + u" n'est pas clôturée"
                    raise CotisationException([error])
                
                facture_cloturee = inscrit.factures_cloturees[self.facture_precedente.fin_recap].Restore()
                self.cotisation_mensuelle += self.facture_precedente.cotisation_mensuelle - facture_cloturee.cotisation_mensuelle
                self.supplement += self.facture_precedente.supplement - facture_cloturee.supplement
                self.deduction += self.facture_precedente.deduction - facture_cloturee.deduction
                self.supplement_activites += self.facture_precedente.supplement_activites - facture_cloturee.supplement_activites            
        
        self.cotisation_mensuelle += self.report_cotisation_mensuelle
        self.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction

    def Cloture(self, date=None):
        if not self.cloture:
            facture_previsionnelle = FactureFinMois(self.inscrit, self.annee, self.mois)
            facture_previsionnelle.Cloture(facture_previsionnelle.fin_recap)
            date = self.date
            while date.month == self.mois:
                if date in self.inscrit.journees:
                    journee = self.inscrit.journees[date]
                    journee.CloturePrevisionnel()
                elif not (date in creche.jours_fermeture or date in self.inscrit.jours_conges):
                    journee = self.inscrit.getReferenceDayCopy(date)
                    if journee:
                        self.inscrit.journees[date] = journee
                        journee.CloturePrevisionnel()
                        journee.Save()
                date += datetime.timedelta(1)
            FactureFinMois.Cloture(self)       

class FactureCloturee:
    def __init__(self, inscrit, date, cotisation_mensuelle, total_contractualise, total_realise, total_facture, supplement_activites, supplement, deduction):
        self.inscrit = inscrit
        self.date = date
        self.cotisation_mensuelle = cotisation_mensuelle
        self.total_contractualise = total_contractualise
        self.total_realise = total_realise
        self.total_facture = total_facture
        self.supplement_activites = supplement_activites
        self.supplement = supplement
        self.deduction = deduction
        self.facture = None
        
    def Restore(self):
        if not self.facture:
            if self.date.day == 1:
                self.facture = FactureDebutMois(self.inscrit, self.date.year, self.date.month)
            else:
                self.facture = FactureFinMois(self.inscrit, self.date.year, self.date.month)
            self.facture.cotisation_mensuelle = self.cotisation_mensuelle
            self.facture.total_contractualise = self.total_contractualise
            self.facture.total_realise = self.total_realise
            self.facture.total_facture = self.total_facture
            self.facture.supplement_activites = self.supplement_activites
            self.facture.supplement = self.supplement
            self.facture.deduction = self.deduction
            self.facture.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction
        return self.facture
            
def Facture(inscrit, annee, mois, options=0):
    date = datetime.date(annee, mois, 1)
    if date in inscrit.factures_cloturees:
        return inscrit.factures_cloturees[date].Restore()        
    elif creche.temps_facturation == FACTURATION_FIN_MOIS:
        return FactureFinMois(inscrit, annee, mois, options)
    elif creche.temps_facturation == FACTURATION_DEBUT_MOIS_CONTRAT:
        return FactureDebutMoisContrat(inscrit, annee, mois, options)
    else:
        return FactureDebutMoisPrevisionnel(inscrit, annee, mois, options)           

