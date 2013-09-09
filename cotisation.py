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
import math
from functions import *

class CotisationException(Exception):
    def __init__(self, errors):
        self.errors = errors
        
    def __str__(self):
        return '\n'.join(self.errors)

NO_ADDRESS = 1
NO_NOM = 2
NO_REVENUS = 4
NO_PARENTS = 8
TRACES = 16

def GetDateRevenus(date):
    if date < datetime.date(date.year, 9, 1) or date >= datetime.date(2008, 9, 1):
        return datetime.date(date.year-2, 1, 1)
    else:
        return datetime.date(date.year-1, 1, 1)
    
def GetNombreFacturesContrat(debut, fin):
    nombre_factures = 0
    date = debut
    while date <= fin:
        if IsContratFacture(date):
            nombre_factures += 1
        date = getNextMonthStart(date)
    return nombre_factures

def GetNombreMoisSansFactureContrat(annee):
    result = 0
    if annee in creche.mois_sans_facture.keys():
        result += len(creche.mois_sans_facture[annee])
    if annee in creche.mois_facture_uniquement_heures_supp.keys():
        result += len(creche.mois_facture_uniquement_heures_supp[annee])
    return result    

def IsFacture(date):
    return date.year not in creche.mois_sans_facture.keys() or date.month not in creche.mois_sans_facture[date.year]

def IsContratFacture(date):
    return IsFacture(date) and (date.year not in creche.mois_facture_uniquement_heures_supp.keys() or date.month not in creche.mois_facture_uniquement_heures_supp[date.year])
                
class Cotisation(object):
    def __init__(self, inscrit, date, options=0):
        self.inscrit = inscrit
        self.date = date
        self.options = options
        errors = []
        if not inscrit.prenom or (not options & NO_NOM and not inscrit.nom):
            errors.append(u" - L'état civil de l'enfant est incomplet.")
        if self.date is None:
            errors.append(u" - La date de début de la période n'est pas renseignée.")
            raise CotisationException(errors)
        self.inscription = inscrit.GetInscription(self.date, preinscription=True)
        if self.inscription is None:
            errors.append(u" - Il n'y a pas d'inscription à cette date.")
            raise CotisationException(errors)
        
        if creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and self.inscription.fin_periode_adaptation:
            if self.inscription.IsInPeriodeAdaptation(self.date):
                self.debut, self.fin = self.inscription.debut, self.inscription.fin_periode_adaptation
            else:
                self.debut, self.fin = self.inscription.fin_periode_adaptation + datetime.timedelta(1), self.inscription.fin
        else:
            self.debut, self.fin = self.inscription.debut, self.inscription.fin
        
        if options & TRACES:
            print u"\nCotisation de %s au %s (%s - %s) :" % (GetPrenomNom(inscrit), date, self.debut, self.fin)

        self.revenus_parents = []
        if creche.formule_taux_horaire_needs_revenus():
            self.date_revenus = GetDateRevenus(self.date)
            self.assiette_annuelle = 0.0
            for parent in inscrit.parents.values():
                if parent:
                    revenus_parent = Select(parent.revenus, self.date_revenus)
                    if revenus_parent is None or revenus_parent.revenu == '':
                        errors.append(u" - Les déclarations de revenus de %s sont incomplètes." % parent.relation)
                    else:
                        self.AjustePeriode((GetYearStart(self.date), GetYearEnd(self.date)))
                        self.assiette_annuelle += float(revenus_parent.revenu)
                        if revenus_parent.chomage:
                            abattement = 0.3 * float(revenus_parent.revenu)
                            self.assiette_annuelle -= abattement
                        else:
                            abattement = None
                        self.revenus_parents.append((parent, revenus_parent.revenu, abattement))
            

            if options & TRACES:
                print u" assiette annuelle :", self.assiette_annuelle
            
            self.bareme_caf = Select(creche.baremes_caf, self.date)
            if self.bareme_caf:
                if self.bareme_caf.plafond and self.assiette_annuelle > self.bareme_caf.plafond:
                    self.AjustePeriode(self.bareme_caf)
                    self.assiette_annuelle = self.bareme_caf.plafond
                    if options & TRACES: print u" plafond CAF appliqué :", self.assiette_annuelle
                elif self.bareme_caf.plancher and self.assiette_annuelle < self.bareme_caf.plancher:
                    self.AjustePeriode(self.bareme_caf)
                    self.assiette_annuelle = self.bareme_caf.plancher
                    if options & TRACES: print u" plancher CAF appliqué :", self.assiette_annuelle
            else:
                if options & TRACES: print " pas de barème CAF"
                    
            self.assiette_mensuelle = self.assiette_annuelle / 12
        else:
            self.date_revenus = None
            self.assiette_annuelle = None
            self.assiette_mensuelle = None
        
        if creche.modes_inscription == MODE_5_5:
            self.mode_garde = MODE_5_5 # TODO a renommer en mode_inscription
            self.jours_semaine = 5
            self.heures_reelles_semaine = 50.0
        else:
            self.mode_garde = self.inscription.mode
            self.jours_semaine, self.heures_reelles_semaine = self.inscription.GetJoursHeuresReference()
            self.semaines_reference = self.inscription.duree_reference / 7
            self.jours_semaine /= self.semaines_reference
            self.heures_reelles_semaine /= self.semaines_reference
        
        if self.mode_garde == MODE_HALTE_GARDERIE:
            self.mode_inscription = MODE_HALTE_GARDERIE
        else:
            self.mode_inscription = MODE_CRECHE

        self.enfants_a_charge, self.enfants_en_creche, debut, fin = GetEnfantsCount(inscrit, self.date)
        self.AjustePeriode((debut, fin))
        
        if self.fin is None:
            self.fin = datetime.date(self.date.year, 12, 31)

        if len(errors) > 0:
            raise CotisationException(errors)
        
        if options & TRACES:
            print u" heures hebdomadaires (réelles) :", self.heures_reelles_semaine
                
        if creche.mode_facturation == FACTURATION_FORFAIT_10H:
            self.heures_semaine = 10.0 * self.jours_semaine
            self.heures_mois = self.heures_semaine * 4
            self.heures_periode = self.heures_mois * 12
            self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
        elif creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            self.heures_semaine = self.heures_reelles_semaine
            self.heures_mois = self.heures_semaine * 4
            self.heures_periode = self.heures_mois * 12
            self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
        else:                
            self.heures_semaine = self.heures_reelles_semaine
                        
            if creche.conges_inscription or creche.facturation_jours_feries == JOURS_FERIES_DEDUITS_ANNUELLEMENT:
                self.heures_periode = 0.0
                self.heures_fermeture_creche = 0.0
                self.heures_accueil_non_facture = 0.0
                self.conges_inscription = []
                date = self.inscription.debut
                if self.inscription.fin is None:
                    errors.append(u" - La période d'inscription n'a pas de fin.")
                    raise CotisationException(errors)
                while date <= self.inscription.fin:
                    heures = self.inscription.getJourneeReference(date).GetNombreHeures()
                    if heures:
                        if date in creche.jours_fermeture:
                            if creche.jours_fermeture[date].options == ACCUEIL_NON_FACTURE:
                                if (options & TRACES): print u' accueil non facturé :', date, "(%fh)" % heures
                                self.heures_accueil_non_facture += heures
                            else:
                                if (options & TRACES): print u' jour de fermeture :', date, "(%fh)" % heures
                                self.heures_fermeture_creche += heures
                        elif date in self.inscrit.jours_conges:
                            if (options & TRACES): print u' jour de congé inscription :', date, "(%fh)" % heures
                            self.conges_inscription.append(date)                            
                        else:
                            self.heures_periode += heures
                    date += datetime.timedelta(1)
                
                self.heures_periode = math.ceil(self.heures_periode)
                if options & TRACES: print u' heures période :', self.heures_periode

                self.nombre_factures = GetNombreFacturesContrat(self.inscription.debut, self.inscription.fin)
                if options & TRACES: print ' nombres de factures :', self.nombre_factures
                self.heures_mois = math.ceil(self.heures_periode / self.nombre_factures)
                if options & TRACES: print ' heures mensuelles : %f (%f)' % (self.heures_mois, self.heures_periode / self.nombre_factures)
            else:
                # 47 pour Bois le roi
                if self.inscription.semaines_conges:
                    self.heures_periode = (52 - self.inscription.semaines_conges) * self.heures_semaine
                    if options & TRACES:
                        print ' heures / periode : (52-%f) * %f = %f' % (self.inscription.semaines_conges, self.heures_semaine, self.heures_periode)
                else:
                    self.heures_periode = 52 * self.heures_semaine
                    if options & TRACES:
                        print ' 52 semaines'
                self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
                if options & TRACES:
                    print ' nombre de factures : %d' % self.nombre_factures
                self.heures_mois = self.heures_periode / self.nombre_factures
                if options & TRACES:
                    print ' heures / mois : %f' % self.heures_mois
                
        if self.jours_semaine == 5:
            self.str_mode_garde = u'plein temps'
        else:
            self.str_mode_garde = u'%d/5èmes' % self.jours_semaine
        
        self.taux_effort = None
        self.forfait_heures_presence = 0.0
        self.prorata_effectue = False
        
        if creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            self.montant_heure_garde = 0.0
            self.cotisation_periode = 0.0
            self.cotisation_mensuelle = self.inscription.forfait_mensuel
        elif creche.mode_facturation == FACTURATION_HORAIRES_REELS:
            if self.inscription.mode == MODE_FORFAIT_HORAIRE:
                self.forfait_heures_presence = self.inscription.forfait_heures_presence
            self.montant_heure_garde = creche.eval_taux_horaire(self.mode_garde, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine)
            if self.montant_heure_garde is None:
                errors.append(u" - La formule de calcul du tarif horaire n'est pas correcte.")
                raise CotisationException(errors)
            self.cotisation_periode = None
            self.cotisation_mensuelle = self.montant_heure_garde * self.forfait_heures_presence
        elif creche.mode_facturation == FACTURATION_PAJE:
            self.montant_heure_garde = creche.eval_taux_horaire(self.mode_garde, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine)
            if options & TRACES: print " montant heure de garde (PAJE) :", self.montant_heure_garde 
            if self.montant_heure_garde is None:
                errors.append(u" - La formule de calcul du tarif horaire n'est pas correcte.")
                raise CotisationException(errors)
            if self.inscription.fin:
                self.semaines_periode = min(52, ((self.inscription.fin - self.inscription.debut).days + 6) / 7)
                self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
                self.nombre_factures = min(self.nombre_factures, GetNombreFacturesContrat(self.inscription.debut, self.inscription.fin))
                self.prorata_effectue = True
            else:
                self.semaines_periode = 52
                self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
            if type(self.inscription.semaines_conges) == int:
                self.semaines_conges = self.inscription.semaines_conges
            else:                
                self.semaines_conges = 0
            self.cotisation_periode = self.montant_heure_garde * self.heures_semaine * (self.semaines_periode - self.semaines_conges)
            if options & TRACES: print " cotisation periode :", self.montant_heure_garde, '*', self.heures_semaine, '* (', self.semaines_periode, '-', self.semaines_conges, ') =', self.cotisation_periode
            self.cotisation_mensuelle = self.cotisation_periode / self.nombre_factures
        else:
            if self.enfants_a_charge > 1:
                self.mode_taux_effort = u'%d enfants à charge' % self.enfants_a_charge
            else:
                self.mode_taux_effort = u'1 enfant à charge'
                
            if creche.mode_facturation == FACTURATION_PSU_TAUX_PERSONNALISES:
                self.taux_effort = creche.eval_taux_effort(self.mode_garde, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine)
                if self.taux_effort is None:
                    errors.append(u" - La formule de calcul du taux d'effort n'est pas correcte.")
                    raise CotisationException(errors)
            else:
                if creche.type == TYPE_PARENTAL and date.year < 2013:
                    tranche = self.enfants_a_charge
                    if inscrit.handicap:
                        tranche += 1
                    if tranche >= 4:
                        self.taux_effort = 0.02
                    elif tranche == 3:
                        self.taux_effort = 0.03
                    elif tranche == 2:
                        self.taux_effort = 0.04
                    else:
                        self.taux_effort = 0.05
                elif creche.type == TYPE_FAMILIAL or creche.type == TYPE_PARENTAL:
                    tranche = self.enfants_a_charge
                    if inscrit.handicap:
                        tranche += 1
                    if tranche > 5:
                        self.taux_effort = 0.02
                    elif tranche > 2:
                        self.taux_effort = 0.03
                    elif tranche == 2:
                        self.taux_effort = 0.04
                    else:
                        self.taux_effort = 0.05
                else:
                    if self.enfants_a_charge > 7:
                        self.taux_effort = 0.02
                    elif self.enfants_a_charge > 3:
                        self.taux_effort = 0.03
                    elif self.enfants_a_charge == 3:
                        self.taux_effort = 0.04
                    elif self.enfants_a_charge == 2:
                        self.taux_effort = 0.05
                    else:
                        self.taux_effort = 0.06
            if options & TRACES: print " taux d'effort :", self.taux_effort
                
            self.montant_heure_garde = self.assiette_mensuelle * self.taux_effort / 100
            if creche.mode_facturation in (FACTURATION_PSU, FACTURATION_PSU_TAUX_PERSONNALISES):
                self.montant_heure_garde = round(self.montant_heure_garde, 2)
                self.cotisation_mensuelle = self.heures_mois * self.montant_heure_garde
            else:
                self.cotisation_mensuelle = self.assiette_mensuelle * self.taux_effort * self.heures_mois / 100
        
        if creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS and self.inscription.IsInPeriodeAdaptation(self.date):
            self.cotisation_periode = 0.0
            self.cotisation_mensuelle = 0.0
        
        self.majoration_mensuelle = 0.0
        for tarif in creche.tarifs_speciaux:
            if self.inscrit.tarifs & (1<<tarif.idx):
                if tarif.pourcentage:
                    cotisation_diff = (self.cotisation_mensuelle * tarif.valeur) / 100
                    heure_garde_diff = (self.montant_heure_garde * tarif.valeur) / 100
                else:
                    cotisation_diff = tarif.valeur
                    heure_garde_diff = 0.0
                if tarif.reduction:
                    self.majoration_mensuelle -= cotisation_diff
                    self.montant_heure_garde -= heure_garde_diff
                else:
                    self.majoration_mensuelle += cotisation_diff
                    self.montant_heure_garde += heure_garde_diff
        self.cotisation_mensuelle += self.majoration_mensuelle
        if options & TRACES: print " cotisation mensuelle :", self.cotisation_mensuelle
    
    def AjustePeriode(self, param):
        if isinstance(param, tuple):
            debut, fin = param
        else:
            debut, fin = param.debut, param.fin
        if debut and debut > self.debut:
            self.debut = debut
        if fin and fin > self.debut and (not self.fin or fin < self.fin):
            self.fin = fin
            
    def Include(self, date):
        return date >= self.debut and date <= self.fin 

