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

class Cotisation(object):
    def __init__(self, inscrit, periode, options=0):
        self.inscrit = inscrit
        self.debut, self.fin = periode
        self.options = options
        errors = []
        if not inscrit.prenom or (not options & NO_NOM and not inscrit.nom):
            errors.append(u" - L'état civil de l'enfant est incomplet.")
        if not (options & NO_ADDRESS) and (not inscrit.code_postal or not inscrit.ville):
            errors.append(u" - L'adresse de l'enfant est incomplète.")
        if not (options & NO_PARENTS) and (not inscrit.papa.prenom or not inscrit.maman.prenom or not inscrit.papa.nom or not inscrit.maman.nom):
            errors.append(u" - L'état civil des parents est incomplet.")
        if self.debut is None:
            errors.append(u" - La date de début de la période n'est pas renseignée.")
            raise CotisationException(errors)
        if self.debut < datetime.date(self.debut.year, 9, 1) or self.debut >= datetime.date(2008, 9, 1):
            revenus_debut = datetime.date(self.debut.year-2, 1, 1)
        else:
            revenus_debut = datetime.date(self.debut.year-1, 1, 1)
        if creche.mode_facturation != FACTURATION_PAJE:
	    self.revenus_papa = Select(inscrit.papa.revenus, revenus_debut)
	    if not options & NO_REVENUS and (self.revenus_papa is None or self.revenus_papa.revenu == ''):
	        errors.append(u" - Les déclarations de revenus du papa sont incomplètes.")
	    self.revenus_maman = Select(inscrit.maman.revenus, revenus_debut)
	    if not options & NO_REVENUS and (self.revenus_maman is None or self.revenus_maman.revenu == ''):
	        errors.append(u" - Les déclarations de revenus de la maman sont incomplètes.")
        if creche.type == TYPE_MUNICIPAL:
            self.bureau = None
        else:
            self.bureau = Select(creche.bureaux, self.debut)
            if self.bureau is None:
                errors.append(u" - Il n'y a pas de bureau à cette date.")
        if creche.mode_facturation != FACTURATION_PAJE:
            self.bareme_caf = Select(creche.baremes_caf, self.debut)
            if self.bareme_caf is None:
                errors.append(u" - Il n'y a pas de barème CAF à cette date.")
        self.inscription = inscrit.getInscription(self.debut)
        if self.inscription is None:
            errors.append(u" - Il n'y a pas d'inscription à cette date.")
            raise CotisationException(errors)

        if creche.modes_inscription == MODE_5_5:
            self.mode_garde = MODE_5_5
            self.jours_semaine = 5
            self.heures_reelles_semaine = 50.0
        else:
            self.mode_garde = self.inscription.mode
            self.jours_semaine = 0
            self.heures_reelles_semaine = 0.0
            for i in range(self.inscription.duree_reference):
                if i % 7 < 5 or not "Week-end" in creche.feries:
                  if self.inscription.reference[i].get_state() & PRESENT:
                    self.jours_semaine += 1
                    self.heures_reelles_semaine += self.inscription.reference[i].get_heures()
            self.semaines_reference = self.inscription.duree_reference / 7
            self.jours_semaine /= self.semaines_reference
            self.heures_reelles_semaine /= self.semaines_reference
        
        if self.mode_garde == MODE_HALTE_GARDERIE:
            self.mode_inscription = MODE_HALTE_GARDERIE
        else:
            self.mode_inscription = MODE_CRECHE

        self.enfants_a_charge = 1
        self.enfants_en_creche = 1
        for frere_soeur in inscrit.freres_soeurs:
            if frere_soeur.naissance and frere_soeur.naissance <= self.debut:
                self.enfants_a_charge += 1
                if frere_soeur.entree and frere_soeur.entree <= self.debut and (frere_soeur.sortie is None or frere_soeur.sortie > self.debut):
                    self.enfants_en_creche += 1

        if len(errors) > 0:
            raise CotisationException(errors)

        self.mois_sans_facture = []
        for conge in creche.conges:
            if conge.options == MOIS_SANS_FACTURE:
                if conge.debut in months:
                    mois = months.index(conge.debut) + 1
                    if mois not in self.mois_sans_facture:
                        self.mois_sans_facture.append(mois)
                else:
                    try:
                        mois = int(conge.debut)
                        if mois not in self.mois_sans_facture:
                            self.mois_sans_facture.append(mois)
                    except:
                        pass
        self.nombre_factures = 12 - len(self.mois_sans_facture)
        
        if creche.mode_facturation == FACTURATION_FORFAIT_10H:
            self.heures_semaine = self.jours_semaine * 10
            self.heures_mois = self.heures_semaine * 4
            self.heures_annee = 12 * self.heures_mois
        else:
            self.heures_semaine = self.heures_reelles_semaine
            self.heures_annee = 47 * self.heures_semaine
#            print 'heures annee', self.heures_annee
            self.heures_mois = self.heures_annee / 12
            # TODO c'etait 45 au lieu de 46 pour Oleron, 47 pour Bois le roi
            # Il faudrait pouvoir saisir le nombre de samaines de vacances qq part
            
            
        if creche.facturation_jours_feries == JOURS_FERIES_DEDUITS_ANNUELLEMENT:
#            print self.heures_annee
            for date in creche.jours_feries + [j for j in creche.jours_fermeture if creche.jours_fermeture[j].options == ACCUEIL_NON_FACTURE]:
                iso = date.isocalendar()
                if iso[0] == self.debut.year:
                    inscription = inscrit.getInscription(date)
                    if inscription:
                        self.heures_annee -= inscription.getReferenceDay(date).get_heures()
#                        if inscription.getReferenceDay(date).get_heures():
#                            print date, inscription.getReferenceDay(date).get_heures()
#            print self.heures_annee
            self.heures_mois = math.ceil(self.heures_annee / self.nombre_factures)

        if self.jours_semaine == 5:
            self.str_mode_garde = u'plein temps'
        else:
            self.str_mode_garde = u'%d/5èmes' % self.jours_semaine
            
        if creche.mode_facturation == FACTURATION_PAJE:       
            self.assiette_annuelle = None
            self.taux_horaire = creche.forfait_horaire
            self.montant_heure_garde = creche.forfait_horaire
            self.montant_jour_supplementaire = 0
            if self.inscription.fin:
                self.semaines_periode = min(52, ((self.inscription.fin - self.inscription.debut).days + 6) / 7)
                self.mois_periode = min(12, self.inscription.fin.month + (self.inscription.fin.year*12) - self.inscription.debut.month - (self.inscription.debut.year*12) + 1)               
            else:
                self.semaines_periode = 52
                self.mois_periode = 12
            if type(self.inscription.semaines_conges) == int:
                self.semaines_conges = self.inscription.semaines_conges
            else:                
                self.semaines_conges = 0
            self.cotisation_periode = self.taux_horaire * self.heures_semaine * (self.semaines_periode - self.semaines_conges)
            self.cotisation_mensuelle = self.cotisation_periode / self.mois_periode
        else:
            self.assiette_annuelle = float(self.revenus_papa.revenu) 
            if self.revenus_papa.chomage:
                self.abattement_chomage_papa = 0.3 * float(self.revenus_papa.revenu)
                self.assiette_annuelle -= self.abattement_chomage_papa
            self.assiette_annuelle += float(self.revenus_maman.revenu)
            if self.revenus_maman.chomage:
                self.abattement_chomage_maman = 0.3 * float(self.revenus_maman.revenu)
                self.assiette_annuelle -= self.abattement_chomage_maman

            if self.assiette_annuelle > self.bareme_caf.plafond:
                self.assiette_annuelle = self.bareme_caf.plafond
            elif self.assiette_annuelle < self.bareme_caf.plancher:
                self.assiette_annuelle = self.bareme_caf.plancher

            self.assiette_mensuelle = self.assiette_annuelle / 12

            if self.enfants_a_charge > 1:
                self.mode_taux_horaire = u'%d enfants à charge' % self.enfants_a_charge
            else:
                self.mode_taux_horaire = u'1 enfant à charge'

            if creche.type == TYPE_MUNICIPAL:
                if self.enfants_a_charge > 3:
                    self.taux_effort = 6.0
                elif self.enfants_a_charge == 3:
                    self.taux_effort = 7.6
                elif self.enfants_a_charge == 2:
                    self.taux_effort = 10.0
                else:
                    self.taux_effort = 12.0
            else:
                if self.enfants_a_charge > 3:
                    self.taux_effort = 5.55
                elif self.enfants_a_charge == 3:
                    self.taux_effort = 6.25
                elif self.enfants_a_charge == 2:
                    self.taux_effort = 8.33
                else:
                    self.taux_effort = 10.0
            self.taux_horaire = self.taux_effort / 200

            self.montant_heure_garde = self.assiette_mensuelle * self.taux_horaire / 100
            if creche.mode_facturation == FACTURATION_PSU:
                self.montant_heure_garde = round(self.montant_heure_garde, 2)
                self.cotisation_mensuelle = self.heures_mois *  self.montant_heure_garde
                self.montant_jour_supplementaire = 0
            else:
                self.montant_jour_garde = self.montant_heure_garde * 10
                self.cotisation_mensuelle = self.assiette_mensuelle * self.taux_horaire * self.heures_mois * creche.mois_payes / 12 / 100
                if self.heures_mois < 200:
                    self.montant_jour_supplementaire = self.montant_jour_garde
                else: 
                    self.montant_jour_supplementaire = 0

        if creche.majoration_localite and self.inscrit.majoration:
            self.majoration_mensuelle = creche.majoration_localite
        else:
            self.majoration_mensuelle = 0.0
        self.cotisation_mensuelle += self.majoration_mensuelle
             
        if 0:
            print inscrit.prenom
            for var in ["debut", "fin", "revenus_papa.revenu", "revenus_maman.revenu", "assiette_annuelle", "jours_semaine", "heures_reelles_semaine", "heures_semaine", "heures_mois", "taux_effort", "enfants_a_charge", "taux_horaire"]:
                print " ", var, eval("self.%s" % var)
        

    def __cmp__(self, context2):
        return context2 == None or \
            (creche.mode_facturation == FACTURATION_PAJE and self.heures_semaine != context2.heures_semaine) or \
            (creche.mode_facturation != FACTURATION_PAJE and self.cotisation_mensuelle != context2.cotisation_mensuelle) or \
            self.heures_mois != context2.heures_mois or \
            self.bureau != context2.bureau or \
            self.assiette_annuelle != context2.assiette_annuelle
