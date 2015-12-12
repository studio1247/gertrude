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

import locale
import __builtin__
from cotisation import *


class FactureFinMois(object):
    def CalculeDeduction(self, cotisation, heures):
        deduction = cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees) - cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees-heures)
        cotisation.heures_mois_ajustees -= heures
        self.deduction += deduction 
        if cotisation.montant_heure_garde:
            self.formule_deduction.append("%s * %.2f" % (GetHeureString(heures), cotisation.montant_heure_garde))
        else:
            self.formule_deduction.append("%s = %.2f" % (GetHeureString(heures), deduction))
            
    def CalculeSupplement(self, cotisation, heures):
        supplement = cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees+heures) - cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees)
        cotisation.heures_mois_ajustees += heures
        if supplement != 0:
            self.supplement += supplement
            self.raison_supplement.add(u"heures supplémentaires")
            if cotisation.montant_heure_garde is not None:
                self.formule_supplement.append(u"%s * %.2f" % (GetHeureString(heures), cotisation.montant_heure_garde))
            else:
                self.formule_supplement.append(u"%s = %.2f" % (GetHeureString(heures), supplement))
        return supplement

    def GetNumeroFacture(self):
        try:
            numero = int(creche.numeros_facture[self.debut_recap].valeur)
        except:
            numero = 0
        
        if (config.options & GROUPES_SITES) and self.site:
            inscrits = []
            for site in creche.sites:
                if site.groupe == self.site.groupe:
                    inscrits.extend(GetInscrits(self.debut_recap, self.fin_recap, site))
        else:
            inscrits = creche.inscrits[:]
        
        inscrits = GetEnfantsTriesSelonParametreTriFacture(inscrits)
            
        if config.options & FACTURES_FAMILLES:
            # print u"Calcul du numéro de facture de", GetPrenomNom(self.inscrit)
            done = []
            for inscrit in inscrits:
                if inscrit.famille is self.inscrit.famille:
                    # print " => %d" % numero
                    return numero
                elif inscrit.HasFacture(self.debut_recap) and inscrit.famille not in done:
                    # print u"  Facture de %s: %d" % (GetPrenomNom(inscrit), numero)
                    numero += 1
                    done.append(inscrit.famille)
                # else:
                    # print u"  Facture de %s sautée" % GetPrenomNom(inscrit)
        else:
            return numero + inscrits.index(self.inscrit) 
            
    def __init__(self, inscrit, annee, mois, options=0):
        creche = __builtin__.creche
        self.inscrit = inscrit
        self.site = None
        self.annee = annee
        self.mois = mois
        self.debut_recap = datetime.date(annee, mois, 1)
        self.fin_recap = GetMonthEnd(self.debut_recap)
        self.date = self.fin_recap
        self.options = options
        self.cotisation_mensuelle = 0.0
        self.report_cotisation_mensuelle = 0.0
        self.heures_facture_par_mode = [0.0] * (MODE_MAX + 1)
        self.heures_contrat = 0.0  # heures réellement contractualisées, tient compte des prorata
        self.heures_maladie = 0.0
        self.heures_facturees_par_mode = [0.0] * (MODE_MAX + 1)
        self.heures_contractualisees = 0.0
        self.heures_contractualisees_realisees = 0.0
        self.heures_realisees = 0.0
        self.heures_realisees_non_facturees = 0.0
        self.heures_facturees_non_realisees = 0.0
        self.heures_previsionnelles = 0.0
        self.jours_contractualises = 0
        self.jours_realises = 0
        self.jours_factures = 0        
        self.total_contractualise = 0.0
        self.total_realise = 0.0
        self.total_realise_non_facture = 0.0
        self.taux_effort = 0.0
        self.supplement = 0.0
        self.deduction = 0.0
        self.formule_supplement = []
        self.formule_deduction = []
        self.jours_presence_non_facturee = {}
        self.jours_presence_selon_contrat = {}
        self.jours_supplementaires = {}
        self.jours_absence_non_prevenue = {}
        self.heures_supplementaires = 0.0
        self.jours_maladie = []
        self.jours_maladie_deduits = []
        self.jours_vacances = []
        self.jours_conges_non_factures = []
        self.raison_deduction = set()
        self.raison_supplement = set()
        self.supplement_activites = 0.0
        self.detail_supplement_activites = {}
        for value in creche.activites:
            self.detail_supplement_activites[creche.activites[value].label] = 0.0
        self.previsionnel = False
        self.cloture = False
        self.montant_heure_garde = 0.0
        self.correction = 0.0
        self.libelle_correction = ""
        self.regularisation = 0.0
        if self.debut_recap in inscrit.corrections:
            try:
                if inscrit.corrections[self.debut_recap].valeur:
                    self.correction = float(inscrit.corrections[self.debut_recap].valeur)
                    self.libelle_correction = inscrit.corrections[self.debut_recap].libelle
            except:
                print "Warning", GetPrenomNom(inscrit), ": correction invalide", inscrit.corrections[self.debut_recap].valeur

        jours_ouvres = 0
        cotisations_mensuelles = []
        heures_hebdomadaires = {}
        last_cotisation = None

        if options & TRACES:
            print '\nFacture de', inscrit.prenom, inscrit.nom, 'pour', months[mois - 1], annee
               
        if inscrit.HasFacture(self.debut_recap) and creche.cloture_factures and today > self.fin_recap:
            fin = self.debut_recap - datetime.timedelta(1)
            debut = GetMonthStart(fin)
            if inscrit.GetInscriptions(debut, fin) and debut not in inscrit.factures_cloturees and IsFacture(debut) and self.debut_recap >= first_date:
                error = u" - La facture du mois " + GetDeMoisStr(debut.month-1) + " " + str(debut.year) + u" n'est pas clôturée"
                raise CotisationException([error])

        if creche.mode_saisie_planning == SAISIE_HORAIRE:
            date = self.debut_recap
            while date.month == mois:
                if date not in creche.jours_fermeture and (creche.conges_inscription != GESTION_CONGES_INSCRIPTION_SIMPLE or date not in inscrit.jours_conges):
                    jours_ouvres += 1
                    inscription = inscrit.GetInscription(date)
                    if inscription:
                        self.site = inscription.site
                        inscritState = inscrit.GetState(date)
                        # print date, str(inscritState)
                        state, heures_reference, heures_realisees, heures_facturees = inscritState.state, inscritState.heures_contractualisees, inscritState.heures_realisees, inscritState.heures_facturees
                        if heures_reference > 0:
                            self.jours_contractualises += 1
                        if heures_realisees > 0:
                            self.jours_realises += 1
                        if heures_facturees > 0:
                            self.jours_factures += 1
                        heures_facturees_non_realisees = 0.0
                        heures_realisees_non_facturees = inscrit.GetTotalActivitesPresenceNonFacturee(date)
                        heures_supplementaires_facturees = (heures_facturees - heures_reference)
                        if heures_realisees_non_facturees > heures_reference:
                            heures_supplementaires_facturees -= heures_realisees_non_facturees - heures_reference

                        if last_cotisation and last_cotisation.Include(date):
                            cotisation = last_cotisation
                            cotisation.jours_ouvres += 1
                            cotisation.heures_reference += heures_reference
                        else:
                            cotisation = Cotisation(inscrit, date, options=NO_ADDRESS|self.options)
                            cotisation.jours_ouvres = 1
                            cotisation.heures_mois_ajustees = cotisation.heures_mois
                            cotisation.heures_reference = heures_reference
                            cotisation.heures_realisees = 0.0
                            cotisation.heures_realisees_non_facturees = 0.0
                            cotisation.heures_facturees_non_realisees = 0.0
                            cotisation.nombre_jours_maladie_deduits = 0
                            cotisation.heures_maladie = 0.0
                            cotisation.heures_contractualisees = 0.0
                            cotisation.heures_supplementaires = 0.0
                            cotisation.total_realise_non_facture = 0.0
                            cotisations_mensuelles.append(cotisation)
                            last_cotisation = cotisation
                            self.taux_effort = cotisation.taux_effort
                            self.montant_heure_garde = cotisation.montant_heure_garde
                            if options & TRACES:
                                print u" cotisation mensuelle à partir de %s" % date, cotisation.cotisation_mensuelle

                        if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                            heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                        else:
                            heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                        if state == HOPITAL:
                            if options & TRACES:
                                print "jour maladie hospitalisation", date
                            if heures_reference > 0:
                                self.jours_maladie.append(date)
                            self.jours_maladie_deduits.append(date)
                            cotisation.nombre_jours_maladie_deduits += 1
                            cotisation.heures_maladie += heures_reference
                            self.heures_facturees_par_mode[cotisation.mode_garde] -= heures_reference
                            if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                self.CalculeDeduction(cotisation, 10)
                            elif inscription.mode != MODE_FORFAIT_HORAIRE:
                                self.CalculeDeduction(cotisation, heures_reference)
                            self.raison_deduction.add('hospitalisation')
                        elif state == MALADE or state == MALADE_SANS_JUSTIFICATIF:
                            if options & TRACES:
                                print "jour maladie", date
                            if heures_reference > 0:
                                self.jours_maladie.append(date)
                            if state == MALADE and (creche.mode_facturation != FACTURATION_HORAIRES_REELS or inscription.mode == MODE_FORFAIT_HORAIRE):
                                # recherche du premier et du dernier jour
                                premier_jour_maladie = tmp = date
                                nombre_jours_ouvres_maladie = 0
                                while tmp > inscrit.inscriptions[0].debut:
                                    tmp -= datetime.timedelta(1)
                                    state = inscrit.GetState(tmp).state
                                    if state == MALADE:
                                        premier_jour_maladie = tmp
                                        if not tmp in creche.jours_fermeture:
                                            nombre_jours_ouvres_maladie += 1
                                    elif state != ABSENT:
                                        break
                                if creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES:
                                    nb_jours_maladie = nombre_jours_ouvres_maladie + 1
                                elif creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES:
                                    nb_jours_maladie = (date - premier_jour_maladie).days + 1
                                else:
                                    dernier_jour_maladie = tmp = date
                                    while not inscrit.inscriptions[-1].fin or tmp < inscrit.inscriptions[-1].fin:
                                        tmp += datetime.timedelta(1)
                                        state = inscrit.GetState(tmp).state
                                        if state == MALADE:
                                            dernier_jour_maladie = tmp
                                        else:
                                            break
                                    nb_jours_maladie = (dernier_jour_maladie - premier_jour_maladie).days + 1

                                if options & TRACES:
                                    print "nombre de jours : %d (minimum=%d)" % (nb_jours_maladie, creche.minimum_maladie)
                                if nb_jours_maladie > creche.minimum_maladie:
                                    self.jours_maladie_deduits.append(date)
                                    cotisation.nombre_jours_maladie_deduits += 1
                                    cotisation.heures_maladie += heures_reference
                                    if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                        self.CalculeDeduction(cotisation, 10)
                                    elif inscription.mode != MODE_FORFAIT_HORAIRE:
                                        self.CalculeDeduction(cotisation, heures_reference)
                                    self.raison_deduction.add(u"maladie > %dj consécutifs" % creche.minimum_maladie)
                        elif state == VACANCES:
                            if heures_reference > 0:
                                self.jours_vacances.append(date)
                            if creche.repartition==REPARTITION_SANS_MENSUALISATION and not inscription.IsNombreSemainesCongesAtteint(date):
                                self.jours_conges_non_factures.append(date)
                                self.heures_facturees_par_mode[cotisation.mode_garde] -= heures_reference
                                self.CalculeDeduction(cotisation, heures_reference)
                                self.raison_deduction.add(u"absence prévenue")
                        elif state == ABSENCE_NON_PREVENUE or state == ABSENCE_CONGE_SANS_PREAVIS:
                            heures_facturees_non_realisees = heures_reference
                            self.jours_absence_non_prevenue[date] = heures_reference
                        elif state > 0:
                            if state & PREVISIONNEL:
                                self.previsionnel = True

                            supplement = 0.0
                            if heures_supplementaires_facturees > 0:
                                if creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                    supplement = self.CalculeSupplement(cotisation, 10)
                                elif cotisation.inscription.mode != MODE_FORFAIT_HORAIRE:
                                    cotisation.heures_supplementaires += heures_supplementaires_facturees
                                    self.heures_supplementaires += heures_supplementaires_facturees
                                    self.heures_facture_par_mode[cotisation.mode_garde] += heures_supplementaires_facturees
                                    if creche.mode_facturation != FACTURATION_HORAIRES_REELS and (creche.facturation_periode_adaptation == PERIODE_ADAPTATION_FACTUREE_NORMALEMENT or not cotisation.inscription.IsInPeriodeAdaptation(date)):
                                        supplement = self.CalculeSupplement(cotisation, heures_supplementaires_facturees)

                            if supplement > 0:
                                self.jours_supplementaires[date] = heures_realisees
                            else:
                                self.jours_presence_selon_contrat[date] = heures_realisees

                            if cotisation.majoration_journaliere:
                                self.supplement += cotisation.majoration_journaliere
                                self.raison_supplement = self.raison_supplement.union(cotisation.raison_majoration_journaliere)

                        if creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE or (creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION and inscription.IsInPeriodeAdaptation(date)):
                            activites = inscrit.GetExtraActivites(date)
                            for value in activites:
                                if value in creche.activites:
                                    activite = creche.activites[value]
                                    tarif = activite.EvalTarif(self.inscrit, date)
                                    self.supplement_activites += tarif
                                    self.detail_supplement_activites[activite.label] += tarif

                        if 0 < heures_realisees_non_facturees == heures_realisees:
                            self.jours_presence_non_facturee[date] = heures_realisees_non_facturees

                        realise_non_facture = cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees+heures_realisees_non_facturees) - cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees)
                        cotisation.total_realise_non_facture += realise_non_facture
                        self.total_realise_non_facture += realise_non_facture

                        self.heures_realisees += heures_realisees
                        self.heures_realisees_non_facturees += heures_realisees_non_facturees
                        self.heures_facturees_non_realisees += heures_facturees_non_realisees
                        cotisation.heures_realisees += heures_realisees
                        cotisation.heures_realisees_non_facturees += heures_realisees_non_facturees
                        cotisation.heures_facturees_non_realisees += heures_facturees_non_realisees

                        if cotisation.inscription.mode != MODE_FORFAIT_HORAIRE:
                            cotisation.heures_contractualisees += heures_reference
                            self.heures_contractualisees += heures_reference
                            self.heures_contractualisees_realisees += min(heures_realisees, heures_reference)
                            if creche.mode_facturation == FACTURATION_HORAIRES_REELS or (creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(date)) or (creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE):
                                self.heures_facturees_par_mode[cotisation.mode_garde] += heures_realisees - heures_realisees_non_facturees + heures_facturees_non_realisees
                                self.total_contractualise += cotisation.CalculeFraisGarde(heures_reference)
                            else:
                                self.heures_facturees_par_mode[cotisation.mode_garde] += heures_facturees - heures_realisees_non_facturees
                        self.total_realise += cotisation.CalculeFraisGarde(heures_realisees - heures_realisees_non_facturees)

                date += datetime.timedelta(1)
        else:
            date = GetNextMonday(self.debut_recap)
            while date.month == mois:
                if date in inscrit.semaines:
                    cotisation = Cotisation(inscrit, date, options=NO_ADDRESS|self.options)
                    semaine = inscrit.semaines[date]
                    for key in semaine.activities:
                        if key in creche.activites:
                            activite = creche.activites[key]
                            compteur = semaine.activities[key]
                            if activite.mode == MODE_SANS_HORAIRES:
                                tarif = compteur.value * activite.EvalTarif(inscrit, date)
                                self.supplement_activites += tarif
                                self.detail_supplement_activites[activite.label] += tarif
                            else:
                                self.heures_realisees += compteur.value
                                self.heures_facturees_par_mode[cotisation.mode_garde] += compteur.value
                                self.cotisation_mensuelle += compteur.value * cotisation.montant_heure_garde

                date += datetime.timedelta(7)
            
        if options & NO_NUMERO:
            self.numero = 0
        else:
            self.numero = self.GetNumeroFacture()

        if inscrit.HasFacture(self.debut_recap):
            for cotisation in cotisations_mensuelles:
                inscription = cotisation.inscription
                self.heures_maladie += cotisation.heures_maladie
                self.heures_facture_par_mode[cotisation.mode_garde] -= cotisation.heures_maladie
                if creche.repartition == REPARTITION_SANS_MENSUALISATION:
                    if creche.mode_facturation == FACTURATION_HORAIRES_REELS or (creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(cotisation.debut)):
                        montant = (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees) * cotisation.montant_heure_garde
                    else:
                        montant = (cotisation.heures_contractualisees - cotisation.heures_realisees_non_facturees) * cotisation.montant_heure_garde
                    self.cotisation_mensuelle += montant
                    self.total_contractualise += montant
                elif creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(cotisation.debut):
                    if inscription.mode == MODE_FORFAIT_HORAIRE:
                        self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees - cotisation.heures_realisees_non_facturees
                    report = cotisation.CalculeFraisGarde(cotisation.heures_realisees)
                    self.report_cotisation_mensuelle += report
                    cotisation.prorata_effectue = True
                    if options & TRACES:
                        print " cotisation periode adaptation :", report
                elif inscription.mode == MODE_FORFAIT_HORAIRE:
                    self.cotisation_mensuelle += cotisation.cotisation_mensuelle * cotisation.jours_ouvres / jours_ouvres
                    cotisation.heures_contractualisees = inscription.forfait_mensuel_heures * cotisation.jours_ouvres / jours_ouvres
                    self.heures_contractualisees += cotisation.heures_contractualisees
                    self.total_contractualise += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                    if cotisation.nombre_jours_maladie_deduits > 0:
                        # retire parce que "montant" non defini ... self.deduction += montant * cotisation.nombre_jours_maladie_deduits / cotisation.jours_ouvres
                        heures_contractualisees = cotisation.heures_contractualisees * (cotisation.jours_ouvres - cotisation.nombre_jours_maladie_deduits) / cotisation.jours_ouvres
                    else:
                        heures_contractualisees = cotisation.heures_contractualisees
                    if cotisation.heures_realisees - cotisation.heures_realisees_non_facturees > heures_contractualisees:
                        cotisation.heures_supplementaires = cotisation.heures_realisees - cotisation.heures_realisees_non_facturees - heures_contractualisees
                        self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees - cotisation.heures_realisees_non_facturees
                        self.heures_supplementaires += cotisation.heures_supplementaires
                        self.heures_facture_par_mode[cotisation.mode_garde] += cotisation.heures_supplementaires
                        self.CalculeSupplement(cotisation, cotisation.heures_supplementaires)
                    else:
                        self.heures_facturees_par_mode[cotisation.mode_garde] += heures_contractualisees
                elif creche.mode_facturation == FACTURATION_HORAIRES_REELS:
                    self.cotisation_mensuelle += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                    self.report_cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees - cotisation.heures_contractualisees) * cotisation.montant_heure_garde
                elif creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE:
                    if self.heures_contractualisees:
                        # On ne met dans la cotisation mensuelle que les heures realisees des heures du contrat
                        self.cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees + cotisation.heures_facturees_non_realisees - cotisation.heures_supplementaires) * cotisation.montant_heure_garde
                        # print '(', cotisation.heures_realisees, '-', cotisation.heures_realisees_non_facturees, '+', cotisation.heures_facturees_non_realisees, '-', cotisation.heures_supplementaires, ') *', cotisation.montant_heure_garde, '=', self.cotisation_mensuelle  
                elif creche.mode_facturation == FACTURATION_PSU and self.heures_contractualisees:
                    prorata_heures = cotisation.heures_mois * cotisation.jours_ouvres / jours_ouvres
                    if not cotisation.prorata_effectue:
                        prorata = cotisation.cotisation_mensuelle * cotisation.jours_ouvres / jours_ouvres
                    else:
                        prorata = cotisation.cotisation_mensuelle
                    if cotisation.total_realise_non_facture:
                        self.deduction += cotisation.total_realise_non_facture
                        self.raison_deduction.add(u"heures non facturées")
                    self.cotisation_mensuelle += prorata
                    self.total_contractualise += prorata
                    self.heures_contrat += prorata_heures
                    self.heures_facture_par_mode[cotisation.mode_garde] += prorata_heures
                else:
                    if self.heures_contractualisees:
                        if cotisation.heures_reference != self.heures_contractualisees:
                            prorata = cotisation.cotisation_mensuelle * cotisation.heures_reference / self.heures_contractualisees
                            prorata_heures = cotisation.heures_mois * cotisation.heures_reference / self.heures_contractualisees
                            cotisation.prorata_effectue = True
                            if options & TRACES: 
                                print " prorata : %f * %f / %f = %f" % (cotisation.cotisation_mensuelle, cotisation.heures_reference, self.heures_contractualisees, prorata)
                        else:
                            prorata = cotisation.cotisation_mensuelle
                            prorata_heures = cotisation.heures_mois
                    else:
                        prorata = cotisation.cotisation_mensuelle
                        prorata_heures = cotisation.heures_mois
                    # ajoute FACTURATION_PSU bloc plus haut pour eviter 2 * la regle de 3
                    # avant il y avait ce commentaire: ne marche pas pour saint julien, mais c'est redemande (2 octobre 2012), normal pour le premier mois pour un enfant qui arrive mi-septembre
                    # avec le test suivant on devrait etre bon, parce que sinon on effectue la regle de 3 dans la cotisation + ici
                    if not cotisation.prorata_effectue:                            
                        new_prorata = (prorata * cotisation.jours_ouvres) / jours_ouvres
                        if options & TRACES:
                            print " prorata : %f * %f / %f = %f" % (prorata, cotisation.jours_ouvres, jours_ouvres, new_prorata)
                        prorata = new_prorata                     

                    self.cotisation_mensuelle += prorata
                    self.total_contractualise += prorata
                    self.heures_contrat += prorata_heures
                    self.heures_facture_par_mode[cotisation.mode_garde] += prorata_heures
                
                if creche.regularisation_fin_contrat:
                    depart_anticipe = creche.gestion_depart_anticipe and inscription.depart and self.debut_recap <= inscription.depart <= self.fin_recap
                    dernier_mois = (depart_anticipe or inscription.fin and self.debut_recap <= inscription.fin <= self.fin_recap)

                    if depart_anticipe and cotisation.Include(inscription.depart):
                        date = cotisation.debut
                        while date <= inscription.depart:
                            cotisation_regularisee = Cotisation(inscrit, date, options=NO_ADDRESS|self.options|DEPART_ANTICIPE)
                            regularisation_cotisation = cotisation_regularisee.cotisation_mensuelle - cotisation.cotisation_mensuelle
                            if options & TRACES:
                                print u" régularisation cotisation : %f - %f = %f par mois" % (cotisation_regularisee.cotisation_mensuelle, cotisation.cotisation_mensuelle, regularisation_cotisation)
                            self.regularisation += regularisation_cotisation 
                            date = GetNextMonthStart(date)
    
                    jours_presence = inscription.GetNombreJoursPresenceSemaine()
                    if jours_presence and inscription.semaines_conges:
                        if dernier_mois:
                            semaines_conges_non_pris = inscription.semaines_conges - float(inscription.GetNombreJoursCongesPoses()) / jours_presence
                            if semaines_conges_non_pris > 0:
                                heures = cotisation.heures_semaine * semaines_conges_non_pris
                                regularisation_conges_non_pris = heures * cotisation.montant_heure_garde
                                if options & TRACES:
                                    print u" régularisation congés non pris (%d semaines, %d jours pris) : %dh * %f = %f" % (inscription.semaines_conges, inscription.GetNombreJoursCongesPoses(), heures, cotisation.montant_heure_garde, regularisation_conges_non_pris)
                                self.regularisation += regularisation_conges_non_pris
        
        if self.regularisation > 0:
            self.supplement += self.regularisation
            self.raison_supplement.add(u"régularisation")
        elif self.regularisation < 0:
            self.deduction -= self.regularisation
            self.raison_deduction.add(u"régularisation")
            
        self.heures_facturees = sum(self.heures_facturees_par_mode)
        if creche.mode_saisie_planning == SAISIE_HORAIRE:
            self.heures_facture = self.heures_contrat + self.heures_supplementaires - self.heures_maladie
        else:
            self.heures_facture = self.heures_facturees
        if creche.temps_facturation == FACTURATION_FIN_MOIS:
            self.cotisation_mensuelle += self.report_cotisation_mensuelle
            self.report_cotisation_mensuelle = 0.0

        # arrondi de tous les champs en euros
        if IsContratFacture(self.debut_recap):
            self.cotisation_mensuelle = round(self.cotisation_mensuelle, 2)
        else:
            self.cotisation_mensuelle = 0.0
        if not self.montant_heure_garde:
            self.heures_cotisation_mensuelle = 0
        else:
            self.heures_cotisation_mensuelle = self.cotisation_mensuelle / self.montant_heure_garde
        self.report_cotisation_mensuelle = round(self.report_cotisation_mensuelle, 2)
        self.supplement = round(self.supplement, 2)
        self.formule_supplement = ' + '.join(self.formule_supplement)
        self.supplement_activites = round(self.supplement_activites, 2)
        self.deduction = round(self.deduction, 2)
        self.formule_deduction = ' + '.join(self.formule_deduction)
        if self.raison_deduction:
            self.raison_deduction = "(" + ", ".join(self.raison_deduction) + ")"
        else:
            self.raison_deduction = "" 
        if self.raison_supplement:
            self.raison_supplement = "(" + ", ".join(self.raison_supplement) + ")"
        else:
            self.raison_supplement = "" 
        self.total_contractualise = round(self.total_contractualise, 2)
        self.total_realise = round(self.total_realise, 2)
        
        self.majoration_mensuelle = 0.0
        for tarif in creche.tarifs_speciaux:
            if tarif.unite == TARIF_SPECIAL_UNITE_EUROS and self.inscrit.famille.tarifs & (1 << tarif.idx):
                if tarif.type == TARIF_SPECIAL_REDUCTION:
                    self.majoration_mensuelle -= tarif.valeur
                elif tarif.type == TARIF_SPECIAL_MAJORATION:
                    self.majoration_mensuelle += tarif.valeur
                else:
                    self.cotisation_mensuelle = tarif.valeur
                
        self.frais_inscription = 0.0
        self.frais_inscription_reservataire = 0.0    
        for inscription in self.inscrit.inscriptions:
            if inscription.frais_inscription and inscription.debut and inscription.debut >= self.debut_recap and inscription.debut <= self.fin_recap:
                if inscription.reservataire:
                    self.frais_inscription_reservataire += inscription.frais_inscription
                else:
                    self.frais_inscription += inscription.frais_inscription

        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction
        self.total_facture = self.total + self.report_cotisation_mensuelle
        
        if options & TRACES:
            for var in ["heures_contractualisees", "heures_facturees", "heures_supplementaires", "heures_contractualisees_realisees", "heures_realisees_non_facturees", "cotisation_mensuelle", "supplement", "deduction", "total"]:
                print "", var, ':', eval("self.%s" % var)  
        
    def formule_supplement_activites(self, activites):
        result = 0.0
        for activite in activites:
            result += self.detail_supplement_activites[activite]
        return locale.format("%+.2f", result)

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
        self.jours_conges_non_factures = self.facture_precedente.jours_conges_non_factures
        self.jours_vacances = self.facture_precedente.jours_vacances
        self.raison_deduction = self.facture_precedente.raison_deduction
        self.raison_supplement = self.facture_precedente.raison_supplement
        self.previsionnel |= self.facture_precedente.previsionnel
        
class FactureDebutMoisContrat(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        self.cotisation_mensuelle += self.facture_precedente.report_cotisation_mensuelle
        self.supplement = self.facture_precedente.supplement
        self.deduction = self.facture_precedente.deduction
        self.supplement_activites = self.facture_precedente.supplement_activites
        self.detail_supplement_activites = self.facture_precedente.detail_supplement_activites
        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction

class FactureDebutMoisPrevisionnel(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        
        if today > self.fin_recap:
            if inscrit.GetInscriptions(self.facture_precedente.debut_recap, self.facture_precedente.fin_recap):
                if self.facture_precedente.fin_recap not in inscrit.factures_cloturees:
                    error = u" - La facture du mois " + GetDeMoisStr(self.facture_precedente.fin_recap.month-1) + " " + str(self.facture_precedente.fin_recap.year) + u" n'est pas clôturée"
                    raise CotisationException([error])
                
                facture_cloturee = inscrit.factures_cloturees[self.facture_precedente.fin_recap].Restore()
                self.cotisation_mensuelle += self.facture_precedente.cotisation_mensuelle - facture_cloturee.cotisation_mensuelle
                self.supplement += self.facture_precedente.supplement - facture_cloturee.supplement
                self.deduction += self.facture_precedente.deduction - facture_cloturee.deduction
                self.supplement_activites += self.facture_precedente.supplement_activites - facture_cloturee.supplement_activites            
        
        self.cotisation_mensuelle += self.report_cotisation_mensuelle
        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction

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
                    journee = self.inscrit.GetJourneeReferenceCopy(date)
                    if journee:
                        self.inscrit.journees[date] = journee
                        journee.CloturePrevisionnel()
                        journee.Save()
                date += datetime.timedelta(1)
            FactureFinMois.Cloture(self)       

def CreateFacture(inscrit, annee, mois, options=0):
    if creche.temps_facturation == FACTURATION_FIN_MOIS:
        return FactureFinMois(inscrit, annee, mois, options)
    elif creche.temps_facturation == FACTURATION_DEBUT_MOIS_CONTRAT:
        return FactureDebutMoisContrat(inscrit, annee, mois, options)
    else:
        return FactureDebutMoisPrevisionnel(inscrit, annee, mois, options)

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
            self.facture = CreateFacture(self.inscrit, self.date.year, self.date.month)
            self.facture.cotisation_mensuelle = self.cotisation_mensuelle
            self.facture.total_contractualise = self.total_contractualise
            self.facture.total_realise = self.total_realise
            self.facture.total_facture = self.total_facture
            self.facture.supplement_activites = self.supplement_activites
            self.facture_precedente.supplement_activites
            self.facture.supplement = self.supplement
            self.facture.deduction = self.deduction
            self.facture.total = self.cotisation_mensuelle + self.supplement + self.supplement_activites - self.deduction + self.facture.correction
        return self.facture
    
    def Decloture(self):
        self.cloture = True
        del self.inscrit.factures_cloturees[self.date]
        if sql_connection:
            print u'Suppression clôture', self.inscrit.idx, self.date
            sql_connection.execute('DELETE FROM FACTURES where inscrit=? AND date=?', (self.inscrit.idx, self.date))
            # print "sql_connection.execute('DELETE FROM FACTURES where inscrit=%d AND date=%r)'" % (self.inscrit.idx, self.date)
            history.append(None)

    
def Facture(inscrit, annee, mois, options=0):
    date = datetime.date(annee, mois, 1)
    if date in inscrit.factures_cloturees:
        return inscrit.factures_cloturees[date].Restore()        
    else:
        return CreateFacture(inscrit, annee, mois, options)
    