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

import math
import xml.dom.minidom
from builtins import str
from functions import *


class CotisationException(Exception):
    def __init__(self, errors):
        self.errors = errors
        
    def __str__(self):
        return '\n'.join(self.errors)


def GetNombreFacturesContrat(debut, fin):
    nombre_factures = 0
    date = debut
    while date <= fin:
        if IsContratFacture(date):
            nombre_factures += 1
        date = GetNextMonthStart(date)
    return nombre_factures


def GetNombreMoisSansFactureContrat(annee):
    result = 0
    if annee in database.creche.mois_sans_facture.keys():
        result += len(database.creche.mois_sans_facture[annee])
    if annee in database.creche.mois_facture_uniquement_heures_supp.keys():
        result += len(database.creche.mois_facture_uniquement_heures_supp[annee])
    return result    


def IsFacture(date):
    return date.year not in database.creche.mois_sans_facture.keys() or date.month not in database.creche.mois_sans_facture[date.year]


def IsContratFacture(date):
    return IsFacture(date) and (date.year not in database.creche.mois_facture_uniquement_heures_supp.keys() or date.month not in database.creche.mois_facture_uniquement_heures_supp[date.year])


def GetTranchesPaje(date, naissance, enfants_a_charge):
    if date < datetime.date(2016, 1, 1):
        if enfants_a_charge == 1:
            return [20285.0, 45077.01]
        elif enfants_a_charge == 2:
            return [23164.0, 51475.01]
        else:
            enfants_a_charge -= 3
            return [26043.0 + (enfants_a_charge * 2879.0), 57873.01 + (enfants_a_charge * 6398.0)]
    elif naissance >= datetime.date(2014, 4, 1):
        if enfants_a_charge == 1:
            return [20509.0, 45575.0]
        elif enfants_a_charge == 2:
            return [23420.0, 52044.0]
        else:
            enfants_a_charge -= 3
            return [26331.0 + (enfants_a_charge * 2911.0), 58513.00 + (enfants_a_charge * 6469.0)]
    else:
        if enfants_a_charge == 1:
            return [21332.0, 47405.0]
        elif enfants_a_charge == 2:
            return [24561.0, 54579.0]
        else:
            enfants_a_charge -= 3
            return [28435.0 + (enfants_a_charge * 3874.0), 63188 + (enfants_a_charge * 8609.0)]


class Cotisation(object):
    def CalculeFraisGarde(self, heures):
        return self.CalculeFraisGardeComplete(heures, heures)[0]

    def GetNombreContratsFactures(self):
        return max(1, self.nombre_factures)

    def IsContratFacture(self, date):
        if self.nombre_factures == 0:
            return True
        else:
            return IsFacture(date)
    
    def CalculeFraisGardeComplete(self, heures, heures_mois):
        if self.montant_heure_garde is not None:
            try:
                result = self.montant_heure_garde * heures
            except:
                result = 0.0
            tarifs = [self.montant_heure_garde]
        else:
            result = 0.0
            tarifs = set()
            heure = 0.0
            if heures_mois == 0:
                multiplier = 1
            else:
                multiplier = heures / heures_mois
            while heure < heures_mois:
                montant, unite = database.creche.eval_tarif(self.debut, self.mode_garde, self.inscrit.handicap, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine, self.inscription.reservataire, self.inscrit.nom.lower(), self.parents, self.chomage, self.conge_parental, self.heures_mois, heure, self.tranche_paje, self.inscrit.famille.tarifs | self.inscription.tarifs, self.inscription.site.nom if self.inscription.site else "", self.inscrit.GetPeriodeInscriptions()[0])
                if unite == TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE:
                    result += multiplier * montant * min(1.0, heures_mois - heure)
                    tarifs.add(montant)
                heure += 1.0
        return result, tarifs

    def __init__(self, inscrit, date, options=0):
        self.inscrit = inscrit
        self.date = date
        self.options = options
        errors = []
        if not inscrit.prenom or (not options & NO_NOM and not inscrit.nom):
            errors.append(" - L'état civil de l'enfant est incomplet.")
        if date is None:
            errors.append(" - La date de début de la période n'est pas renseignée.")
            raise CotisationException(errors)

        inscription = inscrit.get_inscription(date, preinscription=True, array=True)
        if len(inscription) == 0:
            errors.append(" - Il n'y a pas d'inscription à cette date (%s)." % str(date))
            raise CotisationException(errors)
        elif len(inscription) > 1:
            errors.append(" - Il y a plusieurs inscriptions à cette date (%s)." % str(date))
            raise CotisationException(errors)
        else:
            self.inscription = inscription[0]

        self.debut_inscription = self.inscription.debut
        self.fin_inscription = self.inscription.fin
        self.debut = self.debut_inscription
        self.fin = self.fin_inscription

        if database.creche.gestion_depart_anticipe and self.inscription.depart:
            self.fin = self.inscription.depart
            if options & DEPART_ANTICIPE:
                self.fin_inscription = self.inscription.depart

        if database.creche.facturation_periode_adaptation not in (PERIODE_ADAPTATION_FACTUREE_NORMALEMENT, PERIODE_ADAPTATION_FACTUREE_NORMALEMENT_SANS_HEURES_SUPPLEMENTAIRES) and self.inscription.fin_periode_adaptation:
            if self.inscription.IsInPeriodeAdaptation(self.date):
                self.fin = self.inscription.fin_periode_adaptation
            else:
                self.debut = self.inscription.fin_periode_adaptation + datetime.timedelta(1)
                self.debut_inscription = self.debut

        if options & TRACES:
            print("\nCotisation de %s au %s ..." % (GetPrenomNom(inscrit), date))

        self.revenus_parents = []
        self.semaines_conges = 0
        self.liste_conges = []
        self.conges_inscription = []
        self.chomage = 0
        self.conge_parental = 0
        self.date_revenus = self.inscrit.creche.GetDateRevenus(self.date)
        self.assiette_annuelle = 0.0
        self.parents = len(inscrit.famille.parents)
        self.frais_inscription = self.inscription.frais_inscription
        self.montant_allocation_caf = self.inscription.allocation_mensuelle_caf
        self.montant_credit_impots = 0.0
        if not (options & NO_PARENTS):
            for parent in inscrit.famille.parents:
                revenus_parent = Select(parent.revenus, self.date_revenus)
                are_revenus_needed = self.inscrit.creche.are_revenus_needed()
                if are_revenus_needed and (revenus_parent is None or revenus_parent.revenu == ''):
                    errors.append(" - Les déclarations de revenus de %s sont incomplètes." % RelationsItems[parent.sexe][0].lower())
                elif revenus_parent:
                    if revenus_parent.revenu:
                        revenu = float(revenus_parent.revenu)
                    else:
                        revenu = 0.0
                    if database.creche.periode_revenus == REVENUS_CAFPRO:
                        revenu_debut, revenu_fin = revenus_parent.debut, revenus_parent.fin
                    elif self.date >= datetime.date(2008, 9, 1):
                        revenu_debut, revenu_fin = revenus_parent.debut, revenus_parent.fin
                        if isinstance(revenu_debut, datetime.date):
                            revenu_debut = IncrDate(revenu_debut, years=+2)
                        if isinstance(revenu_fin, datetime.date):
                            revenu_fin = IncrDate(revenu_fin, years=+2)
                    else:
                        revenu_debut, revenu_fin = (GetYearStart(self.date), GetYearEnd(self.date))
                    if are_revenus_needed:
                        self.AjustePeriode((revenu_debut, revenu_fin))
                    self.assiette_annuelle += revenu
                    if revenus_parent.chomage:
                        abattement = 0.3 * revenu
                        self.assiette_annuelle -= abattement
                        self.chomage += 1
                    else:
                        abattement = None
                    if revenus_parent.conge_parental:
                        self.conge_parental += 1
                    self.revenus_parents.append((parent, revenu, abattement))

        if options & TRACES:
            print(" assiette annuelle :", self.assiette_annuelle)

        self.bareme_caf = Select(database.creche.baremes_caf, self.date)
        if self.bareme_caf:
            if self.bareme_caf.plafond and self.assiette_annuelle > self.bareme_caf.plafond:
                self.AjustePeriode(self.bareme_caf)
                self.assiette_annuelle = self.bareme_caf.plafond
                if options & TRACES:
                    print(" plafond CAF appliqué :", self.assiette_annuelle)
            elif self.bareme_caf.plancher and self.assiette_annuelle < self.bareme_caf.plancher:
                self.AjustePeriode(self.bareme_caf)
                self.assiette_annuelle = self.bareme_caf.plancher
                if options & TRACES:
                    print(" plancher CAF appliqué :", self.assiette_annuelle)
        else:
            if options & TRACES:
                print(" pas de barème CAF")

        if database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H):
            periode_tarifs = Select(database.creche.tarifs_horaires, self.date)
            if periode_tarifs:
                self.AjustePeriode(periode_tarifs)
                    
        self.assiette_mensuelle = self.assiette_annuelle / 12
        
        if database.creche.modes_inscription == MODE_TEMPS_PLEIN:
            self.mode_garde = MODE_TEMPS_PLEIN  # TODO a renommer en mode_inscription
            self.jours_semaine = 5
            self.heures_reelles_semaine = 50.0
        else:
            self.mode_garde = self.inscription.mode
            self.jours_semaine = self.inscription.get_days_per_week()
            self.heures_reelles_semaine = self.inscription.get_duration_per_week(self.inscrit.creche.arrondi_heures)
            self.semaines_reference = self.inscription.duree_reference // 7
        
        if self.mode_garde is None:
            errors.append(" - Le mode de garde n'est pas renseigné.")
            
        if self.mode_garde == MODE_HALTE_GARDERIE:
            self.mode_inscription = MODE_HALTE_GARDERIE
        else:
            self.mode_inscription = MODE_CRECHE

        self.enfants_a_charge, self.enfants_en_creche, debut, fin = inscrit.famille.GetEnfantsCount(self.date)
        self.AjustePeriode((debut, fin))
        
        if self.fin is None:
            self.fin = datetime.date.today() + datetime.timedelta(2 * 365)

        if self.date < self.debut or self.date > self.fin:
            errors.append(" - Problème dans les périodes d'inscription.")

        if len(errors) > 0:
            raise CotisationException(errors)
        
        if options & TRACES:
            print(" période du %s au %s" % (self.debut, self.fin))
            print(" heures hebdomadaires (réelles) :", self.heures_reelles_semaine)

        self.prorata = True
        self.heures_periode = 0.0
        self.heures_fermeture_creche = 0.0
        self.heures_accueil_non_facture = 0.0
        self.semaines_periode = 0
              
        if database.creche.mode_facturation == FACTURATION_FORFAIT_10H:
            self.heures_semaine = 10.0 * self.jours_semaine
            self.heures_mois = self.heures_semaine * 4
            self.heures_periode = self.heures_mois * 12
            self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
        elif database.creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            self.heures_semaine = self.heures_reelles_semaine
            self.heures_mois = self.heures_semaine * 4
            self.heures_periode = self.heures_mois * 12
            self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
        else:
            if self.inscription.mode == MODE_FORFAIT_MENSUEL:
                if self.inscription.forfait_mensuel_heures is None:
                    errors.append(" - Le nombre d'heures du forfait mensuel n'est pas renseigné.")
                    raise CotisationException(errors)
                self.heures_mois = self.inscription.forfait_mensuel_heures
                self.heures_semaine = self.heures_mois / (52.0 / 12) if self.heures_mois else 0.0  # attention Le Nid Des Trésors
            elif self.inscription.mode == MODE_FORFAIT_HEBDOMADAIRE:
                self.heures_semaine = self.inscription.forfait_mensuel_heures  # TODO rename to forfait
            elif self.inscription.mode == MODE_FORFAIT_GLOBAL_CONTRAT:
                self.heures_periode = self.inscription.forfait_mensuel_heures  # TODO rename to forfait
            elif database.creche.mode_facturation == FACTURATION_PAJE_10H:
                self.heures_semaine = 10.0 * self.jours_semaine
            else:
                self.heures_semaine = self.heures_reelles_semaine

            if config.options & COMPATIBILITY_MODE_CONGES_2016:
                fin_decompte_conges_et_factures = self.fin
            else:
                fin_decompte_conges_et_factures = self.fin_inscription

            if database.creche.facturation_jours_feries == ABSENCES_DEDUITES_EN_JOURS and self.inscription.mode not in (MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_MENSUEL, MODE_FORFAIT_GLOBAL_CONTRAT):
                if self.fin_inscription is None:
                    errors.append(" - La période d'inscription n'a pas de fin.")
                    raise CotisationException(errors)

                if database.creche.repartition == REPARTITION_MENSUALISATION_CONTRAT:
                    debut_decompte_conges_et_factures = self.debut_inscription
                    fin_decompte_conges_et_factures = self.fin_inscription
                    if self.debut_inscription.year in database.creche.mois_sans_facture and self.debut_inscription.month not in database.creche.mois_sans_facture[self.debut_inscription.year]:
                        debut_decompte_conges_et_factures = GetMonthStart(self.debut_inscription)
                    if self.fin_inscription.year in database.creche.mois_sans_facture and self.fin_inscription.month not in database.creche.mois_sans_facture[self.fin_inscription.year]:
                        fin_decompte_conges_et_factures = GetMonthEnd(self.fin_inscription)
                    if options & TRACES:
                        print(" début théorique en date du", debut_decompte_conges_et_factures)
                        print(" fin théorique en date du", fin_decompte_conges_et_factures)
                else:
                    debut_decompte_conges_et_factures = self.debut

                if database.creche.prorata == PRORATA_NONE:
                    self.prorata = (self.fin_inscription != self.fin or self.debut_inscription != self.debut)
                    if self.prorata and (options & TRACES):
                        print(" prorata appliqué quand même (changement de facturation en cours de contrat)")
                    else:
                        debut_decompte_conges_et_factures = self.debut

                # debut_conge = None
                date = debut_decompte_conges_et_factures
                while date <= fin_decompte_conges_et_factures:
                    heures = self.inscription.get_day_from_date(date).get_duration(self.inscrit.creche.arrondi_heures)
                    if heures:
                        if date in database.creche.jours_fermeture:
                            # if debut_conge is None:
                            #     debut_conge = date
                            if database.creche.jours_fermeture[date].options == ACCUEIL_NON_FACTURE:
                                if options & TRACES:
                                    print(" accueil non facturé :", date, "(%fh)" % heures)
                                self.heures_accueil_non_facture += heures
                            else:
                                if options & TRACES:
                                    print(" jour de fermeture :", date, "(%fh)" % heures)
                                self.heures_fermeture_creche += heures
                        elif database.creche.conges_inscription in (GESTION_CONGES_INSCRIPTION_MENSUALISES, GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT) and date in inscrit.jours_conges:
                            if options & TRACES:
                                print(" jour de congé inscription :", date, "(%fh)" % heures)
                            self.conges_inscription.append(date)
                            # if debut_conge is None:
                            #     debut_conge = date                            
                        else:
                            self.heures_periode += heures
                            # if debut_conge is not None:
                            #     self.liste_conges.append(date2str(debut_conge) + " - " + date2str(date-datetime.timedelta(1)))
                            #     debut_conge = None
                    date += datetime.timedelta(1)
                # if debut_conge is not None:
                #     self.liste_conges.append(date2str(debut_conge) + " - " + date2str(self.fin_inscription))
                if self.inscription.semaines_conges:
                    if options & TRACES:
                        print(" + %d semaines de congés" % self.inscription.semaines_conges)
                    self.heures_periode -= self.inscription.semaines_conges * self.heures_semaine
                    self.liste_conges.append("%d semaines de congés" % self.inscription.semaines_conges)
                self.heures_periode = float(math.ceil(self.heures_periode))
                if options & TRACES:
                    print(" heures période :", self.heures_periode)
                self.semaines_periode = 1 + (self.fin_inscription - self.debut_inscription).days // 7
                self.nombre_factures = GetNombreFacturesContrat(debut_decompte_conges_et_factures, fin_decompte_conges_et_factures)

                if options & TRACES:
                    print(" nombres de factures :", self.nombre_factures)

                if database.creche.mode_facturation != FACTURATION_FORFAIT_MENSUEL:
                    self.heures_mois = self.heures_periode / self.GetNombreContratsFactures()
                    if options & TRACES:
                        print(" heures mensuelles : %f" % self.heures_mois)
                    if database.creche.arrondi_mensualisation == ARRONDI_HEURE_PLUS_PROCHE:
                        self.heures_mois = math.ceil(self.heures_mois)
                        if options & TRACES:
                            print(" arrondi heures mensuelles : %f" % self.heures_mois)
            else:
                if database.creche.repartition == REPARTITION_MENSUALISATION_CONTRAT:
                    if self.fin_inscription is None:
                        errors.append(" - La période d'inscription n'a pas de fin.")
                        raise CotisationException(errors)
                    if not config.options & COMPATIBILITY_MODE_ADAPTATIONS_2016:
                        if database.creche.facturation_periode_adaptation in (PERIODE_ADAPTATION_GRATUITE, PERIODE_ADAPTATION_HORAIRES_REELS) and self.inscription.fin_periode_adaptation:
                            self.debut_inscription = self.inscription.fin_periode_adaptation + datetime.timedelta(1)
                    self.semaines_periode = GetNombreSemainesPeriode(self.debut_inscription, self.fin_inscription)
                    self.nombre_factures = GetNombreFacturesContrat(self.debut_inscription, self.fin_inscription)
                    if database.creche.prorata == PRORATA_NONE:
                        self.prorata = False  # Fait pour O-pagaio (self.fin_inscription != self.fin or self.debut_inscription != self.debut)
                elif database.creche.repartition == REPARTITION_SANS_MENSUALISATION:
                    if self.fin_inscription is None:
                        self.semaines_periode = 52
                        self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
                    else:
                        self.semaines_periode = GetNombreSemainesPeriode(self.debut_inscription, self.fin_inscription)
                        self.nombre_factures = GetNombreFacturesContrat(self.debut_inscription, self.fin_inscription)
                else:
                    self.semaines_periode = 52
                    self.nombre_factures = 12 - GetNombreMoisSansFactureContrat(self.date.year)
                if self.inscription.semaines_conges:
                    self.semaines_conges = self.inscription.semaines_conges

                if self.inscription.mode == MODE_FORFAIT_GLOBAL_CONTRAT:
                    self.heures_semaine = self.heures_periode / (self.semaines_periode - self.semaines_conges)
                    self.heures_mois = self.heures_periode / self.GetNombreContratsFactures()
                    if options & TRACES:
                        print(" semaines période", self.semaines_periode)
                        print(" heures / semaine", self.heures_semaine)
                        print(" heures / mois", self.heures_mois)
                else:
                    self.heures_periode = (self.semaines_periode - self.semaines_conges) * self.heures_semaine

                    if database.creche.mode_facturation != FACTURATION_FORFAIT_MENSUEL and self.inscription.mode != MODE_FORFAIT_MENSUEL:
                        self.heures_mois = self.heures_periode / self.GetNombreContratsFactures()

                    if options & TRACES:
                        print(' heures / periode : (%f-%f) * %f = %f' % (self.semaines_periode, self.semaines_conges, self.heures_semaine, self.heures_periode))
                        print(' nombre de factures : %d' % self.nombre_factures)
                        print(' heures / mois : %f' % self.heures_mois)
                
        if self.jours_semaine == 5:
            self.str_mode_garde = 'plein temps'
        else:
            self.str_mode_garde = '%d/5èmes' % self.jours_semaine

        self.tranche_paje = 0
        self.taux_effort = None
        self.forfait_mensuel_heures = 0.0
        self.montants_heure_garde = []

        if not inscrit.naissance:
            errors.append(" - La date de naissance n'est pas renseignée.")
            raise CotisationException(errors)

        if database.creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            self.montant_heure_garde = 0.0
            self.cotisation_periode = 0.0
            self.cotisation_mensuelle = self.inscription.forfait_mensuel
        elif database.creche.mode_facturation == FACTURATION_HORAIRES_REELS or self.inscription.mode == MODE_FORFAIT_MENSUEL:
            if self.inscription.mode == MODE_FORFAIT_MENSUEL:
                self.forfait_mensuel_heures = self.inscription.forfait_mensuel_heures
                # print "heures : ", self.heures_semaine, self.heures_mois
            try:
                self.tranche_paje = 1 + GetTranche(self.assiette_annuelle, GetTranchesPaje(date, inscrit.naissance, self.enfants_a_charge))
                self.tarif_montant, self.tarif_unite = database.creche.eval_tarif(self.debut, self.mode_garde, inscrit.handicap, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine, self.inscription.reservataire, inscrit.nom.lower(), self.parents, self.chomage, self.conge_parental, self.heures_mois, 0, self.tranche_paje, inscrit.famille.tarifs | self.inscription.tarifs, self.inscription.site.nom if self.inscription.site else "", inscrit.GetPeriodeInscriptions()[0])
                if self.tarif_unite == TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE:
                    self.montant_heure_garde = self.tarif_montant
                    if options & TRACES:
                        print(" montant heure de garde (Forfait horaire) :", self.montant_heure_garde)
                else:
                    if options & TRACES:
                        print(" montant mensuel (Forfait horaire) :", self.tarif_montant)
            except Exception as e:
                print("Exception formule de calcul", e)
                errors.append(" - La formule de calcul du tarif horaire n'est pas correcte.")
                raise CotisationException(errors)
            self.cotisation_periode = None
            self.cotisation_mensuelle, self.montants_heure_garde = self.CalculeFraisGardeComplete(self.forfait_mensuel_heures, self.heures_mois)
        elif database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H):
            self.tranche_paje = 1 + GetTranche(self.assiette_annuelle, GetTranchesPaje(date, inscrit.naissance, self.enfants_a_charge))
            if date < datetime.date(2016, 1, 1):
                self.AjustePeriode((debut, datetime.date(2015, 12, 31)))
            else:
                self.AjustePeriode((datetime.date(2016, 1, 1), fin))
            try:
                self.tarif_montant, self.tarif_unite = database.creche.eval_tarif(self.debut, self.mode_garde, inscrit.handicap, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine, self.inscription.reservataire, inscrit.nom.lower(), self.parents, self.chomage, self.conge_parental, self.heures_mois, None, self.tranche_paje, inscrit.famille.tarifs | self.inscription.tarifs, self.inscription.site.nom if self.inscription.site else "", inscrit.GetPeriodeInscriptions()[0])
                if self.tarif_unite == TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE:
                    self.montant_heure_garde = self.tarif_montant
                    if options & TRACES:
                        print(" montant heure de garde (PAJE) :", self.montant_heure_garde)
                else:
                    if options & TRACES:
                        print(" montant mensuel (PAJE) :", self.tarif_montant)
                    self.montant_heure_garde = 0.0
            except Exception as e:
                print("Exception formule de calcul", e)
                errors.append(" - La formule de calcul du tarif horaire n'est pas correcte.")
                raise CotisationException(errors)
            if type(self.inscription.semaines_conges) == int:
                self.semaines_conges = self.inscription.semaines_conges
            if self.tarif_unite == TARIF_HORAIRE_UNITE_EUROS_PAR_MOIS:
                self.montants_heure_garde = 0.0
                self.cotisation_mensuelle = self.tarif_montant
                self.cotisation_periode = self.cotisation_mensuelle * self.GetNombreContratsFactures()
            else:
                self.cotisation_periode, self.montants_heure_garde = self.CalculeFraisGardeComplete(self.heures_periode, self.heures_mois)
                self.cotisation_mensuelle = self.cotisation_periode / self.GetNombreContratsFactures()
            self.montant_allocation_caf = self.eval_allocation_caf()
            self.montant_credit_impots = self.eval_credit_impots()
            if options & TRACES:
                print(" cotisation periode :", self.cotisation_periode)
                print(" cotisation mensuelle :", self.cotisation_mensuelle)
                print(" montant heure garde supplementaire :", self.montant_heure_garde)
                print(" montant allocation CAF :", self.montant_allocation_caf)
                print(" montant credit impots :", self.montant_credit_impots)
        elif database.creche.nom == "LA VOLIERE":
            if self.enfants_a_charge == 1:
                tranche = GetTranche(self.assiette_annuelle, [20281.0, 45068.0])
            elif self.enfants_a_charge == 2:
                tranche = GetTranche(self.assiette_annuelle, [23350.0, 51889.0])
            elif self.enfants_a_charge == 3:
                tranche = GetTranche(self.assiette_annuelle, [27033.0, 60074.0])
            else:
                tranche = GetTranche(self.assiette_annuelle, [30716.0, 68259.0])
            b20 = database.creche.cout_journalier / 10
            b2x = b20 * (1.10, 1.15, 1.20)[tranche]
            self.a = (b20 - b2x) / 229
            self.b = (230 * b2x - b20) / 229
            self.montant_heure_garde = (self.a * self.heures_mois + self.b)
            self.cotisation_mensuelle = self.heures_mois * self.montant_heure_garde
        else:
            if self.enfants_a_charge > 1:
                self.mode_taux_effort = '%d enfants à charge' % self.enfants_a_charge
            else:
                self.mode_taux_effort = '1 enfant à charge'
                
            if database.creche.mode_facturation == FACTURATION_PSU_TAUX_PERSONNALISES:
                try:
                    self.taux_effort = database.creche.EvalTauxEffort(self.mode_garde, inscrit.handicap, self.assiette_annuelle, self.enfants_a_charge, self.jours_semaine, self.heures_semaine, self.inscription.reservataire, inscrit.nom.lower(), self.parents, self.chomage, self.conge_parental, self.heures_mois, 0, self.tranche_paje, inscrit.famille.tarifs | self.inscription.tarifs)
                except Exception as e:
                    print("Exception formule de calcul", e)
                    errors.append(" - La formule de calcul du taux d'effort n'est pas correcte.")
                    raise CotisationException(errors)
            else:
                if database.creche.type == TYPE_PARENTAL and date.year < 2013:
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
                elif database.creche.type in (TYPE_FAMILIAL, TYPE_PARENTAL, TYPE_MICRO_CRECHE):
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
                    tranche = self.enfants_a_charge
                    if inscrit.handicap:
                        tranche += 1
                    if tranche > 7:
                        self.taux_effort = 0.02
                    elif tranche > 3:
                        self.taux_effort = 0.03
                    elif tranche == 3:
                        self.taux_effort = 0.04
                    elif tranche == 2:
                        self.taux_effort = 0.05
                    else:
                        self.taux_effort = 0.06
            if options & TRACES:
                print(" taux d'effort=%.02f, mode=%s, type creche=%d" % (self.taux_effort, self.mode_taux_effort, database.creche.type))
                
            self.montant_heure_garde = self.assiette_mensuelle * self.taux_effort / 100
            if database.creche.mode_facturation in (FACTURATION_PSU, FACTURATION_PSU_TAUX_PERSONNALISES):
                self.montant_heure_garde = round(self.montant_heure_garde, 2)
                self.cotisation_mensuelle = self.heures_mois * self.montant_heure_garde
            else:
                self.cotisation_mensuelle = self.assiette_mensuelle * self.taux_effort * self.heures_mois / 100
        
        if database.creche.facturation_periode_adaptation not in (PERIODE_ADAPTATION_FACTUREE_NORMALEMENT, PERIODE_ADAPTATION_FACTUREE_NORMALEMENT_SANS_HEURES_SUPPLEMENTAIRES) and self.inscription.IsInPeriodeAdaptation(self.date):
            self.cotisation_periode = 0.0
            self.cotisation_mensuelle = 0.0
        
        self.majoration_mensuelle = 0.0
        self.majoration_journaliere = 0.0
        self.raison_majoration_journaliere = set()
        if self.montant_heure_garde is not None:
            for tarif in database.creche.tarifs_speciaux:
                if (inscrit.famille.tarifs | self.inscription.tarifs) & (1 << tarif.idx):
                    heure_garde_diff = 0.0
                    jour_garde_diff = 0.0
                    if tarif.unite == TARIF_SPECIAL_UNITE_EUROS:
                        cotisation_diff = tarif.valeur
                    elif tarif.unite == TARIF_SPECIAL_UNITE_POURCENTAGE:
                        cotisation_diff = (self.cotisation_mensuelle * tarif.valeur) / 100
                        heure_garde_diff = (self.montant_heure_garde * tarif.valeur) / 100
                    elif tarif.unite == TARIF_SPECIAL_UNITE_EUROS_PAR_HEURE:
                        cotisation_diff = tarif.valeur * self.heures_mois 
                        heure_garde_diff = tarif.valeur
                    elif tarif.unite == TARIF_SPECIAL_UNITE_EUROS_PAR_JOUR:
                        cotisation_diff = 0
                        jour_garde_diff = tarif.valeur
                        self.raison_majoration_journaliere.add(tarif.label)
                    else:
                        errors.append(" - Le tarif spécial à appliquer n'est pas implémenté.")
                        raise CotisationException(errors)
                    
                    if tarif.type == TARIF_SPECIAL_REDUCTION:
                        self.majoration_mensuelle -= cotisation_diff
                        self.montant_heure_garde -= heure_garde_diff
                        self.majoration_journaliere -= jour_garde_diff
                    elif tarif.type == TARIF_SPECIAL_MAJORATION:
                        self.majoration_mensuelle += cotisation_diff
                        self.montant_heure_garde += heure_garde_diff
                        self.majoration_journaliere += jour_garde_diff
                    else:
                        self.cotisation_mensuelle = cotisation_diff
                        self.montant_heure_garde = heure_garde_diff
                        self.montants_heure_garde = [self.montant_heure_garde]

        if self.majoration_mensuelle:
            self.cotisation_mensuelle += self.majoration_mensuelle
        
        if database.creche.arrondi_mensualisation_euros == ARRONDI_EURO_PLUS_PROCHE:
            self.cotisation_mensuelle = round(self.cotisation_mensuelle)

        self.montant_journalier_activites = 0.0
        for activite in database.creche.activites:
            if activite.mode == MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE:
                self.montant_journalier_activites += activite.EvalTarif(inscrit, self.debut, reservataire=self.inscription.reservataire)
        if options & TRACES:
            print(" montant journalier activites :", self.montant_journalier_activites)
        self.montant_mensuel_activites = self.montant_journalier_activites * self.jours_semaine * (self.semaines_periode - self.semaines_conges) / self.GetNombreContratsFactures()
        self.cotisation_mensuelle_avec_activites = self.cotisation_mensuelle + self.montant_mensuel_activites

        if options & TRACES: 
            print(" cotisation mensuelle :", self.cotisation_mensuelle)
            print(" montant heure garde :", self.montant_heure_garde)
            print()

    def eval_allocation_caf(self):
        """
        - de 3 ans	        846,22 €	729,47 €	612,77 €
        de 3 ans à 6 ans	423,12 €	364,74 €	306,39 €
        """
        if not self.inscrit.naissance or not self.tranche_paje or self.inscription.debut > IncrDate(self.inscrit.naissance, years=6):
            result = 0.0
        elif self.inscription.debut > IncrDate(self.inscrit.naissance, years=3):
            result = [423.12, 364.74, 306.39][self.tranche_paje-1]
        else:
            result = [846.22, 729.47, 612.77][self.tranche_paje-1]
        return min(result, self.cotisation_mensuelle * 85 / 100)

    def eval_credit_impots(self):
        # l'allocation CAF doit avoir été calculée avant
        assiette = min((self.cotisation_mensuelle - self.montant_allocation_caf) * 12, 2300.0)
        if self.inscrit.garde_alternee:
            assiette /= 2
        return math.ceil(assiette / 24)

    def AjustePeriode(self, param):
        if isinstance(param, tuple):
            debut, fin = param
        else:
            debut, fin = param.debut, param.fin
        if debut and debut > self.debut:
            self.debut = debut
        if fin and fin > self.debut and (not self.fin or fin < self.fin):
            self.fin = fin

    def IsFacture(self, date):
        if self.nombre_factures == 0:
            return True
        else:
            return IsFacture(date)

    def GetNombreFactures(self, debut, fin):
        nombre_factures = 0
        date = debut
        while date <= fin:
            if IsFacture(date):
                nombre_factures += 1
            date = GetNextMonthStart(date)
        return nombre_factures
            
    def Include(self, date):
        return self.debut <= date <= self.fin

    def get_echeances(self):
        echeances = []
        if self.debut:
            fin = self.fin
            if not fin:
                fin = self.debut.replace(year=self.debut.year+1)
            debut = GetMonthEnd(self.debut)
            fin = GetMonthEnd(fin)
            date = debut
            while date <= fin:
                valeur = self.cotisation_mensuelle
                if database.creche.repartition == REPARTITION_MENSUALISATION_CONTRAT:
                    if date == debut or (self.fin and date == fin):
                        num, den = 0, 0
                        d = GetMonthStart(date)
                        while d.month == date.month:
                            if d not in database.creche.jours_fermeture and (database.creche.conges_inscription != GESTION_CONGES_INSCRIPTION_MENSUALISES or d not in self.inscrit.jours_conges):
                                den += 1
                                if self.debut <= d and (not self.fin or d <= self.fin):
                                    num += 1
                            d += datetime.timedelta(1)
                        if den:
                            valeur = valeur * num / den
                echeances.append((date, valeur))
                date = GetMonthEnd(date + datetime.timedelta(1))
            return echeances


def GetCotisations(inscrit, options=TRACES):
    result = []
    date = config.first_date
    for inscription in inscrit.get_inscriptions(preinscriptions=True):
        if inscription.debut:
            date = max(date, inscription.debut)
            while date.year < datetime.date.today().year + 2:
                try:
                    cotisation = Cotisation(inscrit, date, options)
                    result.append((cotisation.debut, cotisation.fin, cotisation))
                    date = cotisation.fin + datetime.timedelta(1)
                    if inscription.fin and date > inscription.fin:
                        break
                    if database.creche.gestion_depart_anticipe and inscription.depart and date > inscription.depart:
                        break
                except CotisationException as e:
                    if inscription.fin:
                        fin = inscription.fin
                    else:
                        fin = datetime.date(date.year, 12, 31)
                    if fin >= date:
                        result.append((date, fin, e))
                        date = fin + datetime.timedelta(1)
                    break
    return result


def ParseHtml(filename, context):
    locals().update(context.__dict__)
    data = open(filename, "r").read()

    # remplacement des <if>
    while 1:
        start = data.find('<if ')
        if start == -1:
            break
        end = data.find('</if>', start) + 5
        text = data[start:end]
        dom = xml.dom.minidom.parseString(text[:text.index('>') + 1] + '</if>')
        test = dom.getElementsByTagName('if')[0].getAttribute('value')
        try:
            if eval(test):
                replacement = text[text.index('>') + 1:-5]
            else:
                replacement = ''
        except Exception as e:
            print("Exception dans un <if> du template HTML", text)
            replacement = ""
        data = data.replace(text, replacement)

    # remplacement des <var>
    while 1:
        start = data.find('<var ')
        if start == -1:
            break
        end = data.find('/>', start) + 2
        text = data[start:end]
        dom = xml.dom.minidom.parseString(text)
        try:
            replacement = eval(dom.getElementsByTagName('var')[0].getAttribute('value'))
        except:
            replacement = "<erreur (%s)>" % dom.getElementsByTagName('var')[0].getAttribute('value')
        if isinstance(replacement, datetime.date):
            replacement = date2str(replacement)
        elif not isinstance(replacement, str):
            replacement = str(replacement)
        data = data.replace(text, replacement)

    return data


def generateFraisGardeHtml(cotisation):
    if cotisation.inscription.mode == MODE_FORFAIT_HEBDOMADAIRE and IsTemplateFile("Frais garde forfait hebdomadaire.html"):
        filename = "Frais garde forfait hebdomadaire.html"
    elif cotisation.inscription.mode == MODE_FORFAIT_MENSUEL and IsTemplateFile("Frais garde forfait mensuel.html"):
        filename = "Frais garde forfait mensuel.html"
    elif database.creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
        filename = "Frais garde forfait.html"
    elif database.creche.mode_facturation == FACTURATION_HORAIRES_REELS:
        filename = "Frais garde reel.html"
    elif database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H):
        filename = "Frais garde paje.html"
    else:
        filename = "Frais garde defaut.html"
    print(filename)
    return ParseHtml(GetTemplateFile(filename), cotisation)
