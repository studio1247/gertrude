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

import locale
from cotisation import *
from globals import *
from database import Inscrit, Reservataire, EncaissementFamille, EncaissementReservataire, ClotureFacture


class FactureBase(object):
    def __init__(self, inscrit, annee, mois, options=0):
        self.inscrit = inscrit
        self.site = None
        self.annee = annee
        self.mois = mois
        self.debut_recap = datetime.date(annee, mois, 1)
        self.fin_recap = GetMonthEnd(self.debut_recap)
        self.date = self.fin_recap
        self.options = options
        self.cloture = None

    def GetFactureId(self):
        if config.numfact:
            fields = {"inscritid": self.inscrit.idx, "numero": self.numero, "annee": self.annee, "mois": self.mois}
            if "numero-global" in config.numfact:
                fields["numero-global"] = config.numerotation_factures.get("inscrit-%d" % self.inscrit.idx, datetime.date(self.annee, self.mois, 1))
            return config.numfact % fields
        else:
            return '%03d%04d%02d' % (self.inscrit.idx, self.annee, self.mois)

    def GetDatePrelevementAutomatique(self):
        date = self.date
        if database.creche.temps_facturation == FACTURATION_FIN_MOIS:
            date += datetime.timedelta(1)
        day = self.inscrit.famille.jour_prelevement_automatique
        return date.replace(day=(day if type(day) == int else 1))

    def Cloture(self):
        print("Clôture de facture", GetPrenomNom(self.inscrit), self.date)
        cloture = ClotureFacture(inscrit=self.inscrit,
                                 date=self.date,
                                 cotisation_mensuelle=self.cotisation_mensuelle,
                                 total_contractualise=self.total_contractualise,
                                 total_realise=self.total_realise,
                                 total_facture=self.total_facture,
                                 supplement_activites=self.supplement_activites,
                                 supplement=self.supplement,
                                 deduction=self.deduction)
        if cloture.date in self.inscrit.clotures:
            print("Facture déjà clôturée !")
        else:
            self.inscrit.clotures[cloture.date] = cloture
            history.append(None)  # TODO

    def Decloture(self):
        print("Déclôture de facture", GetPrenomNom(self.inscrit), self.date)
        if self.date in self.inscrit.clotures:
            database.delete(self.inscrit.clotures[self.date])
            del self.inscrit.clotures[self.date]
        else:
            print("Facture non clôturée !")
        history.append(None)


class FactureFinMois(FactureBase):
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
            self.heures_supplementaires_facture += heures
            if cotisation.montant_heure_garde is not None:
                self.formule_supplement.append("%s * %.2f" % (GetHeureString(heures), cotisation.montant_heure_garde))
            else:
                self.formule_supplement.append("%s = %.2f" % (GetHeureString(heures), supplement))
        return supplement

    def GetNumeroFacture(self):
        try:
            numero = int(database.creche.numeros_facture[self.debut_recap].valeur)
        except:
            numero = 0
        
        if (config.options & GROUPES_SITES) and self.site:
            inscrits = []
            for site in database.creche.sites:
                if site.groupe == self.site.groupe:
                    inscrits.extend(list(database.creche.select_inscrits(self.debut_recap, self.fin_recap, site)))
        else:
            inscrits = database.creche.inscrits[:]
        
        inscrits = GetEnfantsTriesSelonParametreTriFacture(inscrits)
            
        if config.options & FACTURES_FAMILLES:
            done = []
            for inscrit in inscrits:
                if inscrit.famille is self.inscrit.famille:
                    return numero
                elif inscrit.has_facture(self.debut_recap) and inscrit.famille not in done:
                    numero += 1
                    done.append(inscrit.famille)
        else:
            for inscrit in inscrits:
                if inscrit is self.inscrit:
                    return numero
                elif inscrit.has_facture(self.debut_recap):
                    numero += 1

    @staticmethod
    def join_raison(raison):
        if raison:
            return "(" + ", ".join(raison) + ")"
        else:
            return ""

    def __init__(self, inscrit, annee, mois, options=0):
        FactureBase.__init__(self, inscrit, annee, mois, options)
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
        self.supplement_heures_supplementaires = 0.0
        self.heures_supplementaires_facture = 0.0
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
        self.jours_maladie_non_deduits = {}
        self.heures_absence_maladie = 0.0
        self.jours_vacances = []
        self.jours_conges_non_factures = []
        self.raison_deduction = set()
        self.raison_supplement = set()
        self.supplement_activites = 0.0
        self.heures_supplement_activites = {}
        self.detail_supplement_activites = {"Activites mensualisees": 0.0}
        self.tarif_supplement_activites = {"Activites mensualisees": 0.0}
        for activite in database.creche.activites:
            self.heures_supplement_activites[activite.label] = 0.0
            self.detail_supplement_activites[activite.label] = 0.0
            self.tarif_supplement_activites[activite.label] = 0.0
        self.previsionnel = False
        self.montant_heure_garde = 0.0
        self.montant_jour_garde = 0.0
        self.heures_periode_adaptation = 0.0
        self.cotisation_periode_adaptation = 0.0
        self.correction = 0.0
        self.libelle_correction = ""
        self.regularisation = 0.0
        self.raison_regularisation = set()
        if self.debut_recap in inscrit.corrections:
            try:
                if inscrit.corrections[self.debut_recap].valeur:
                    self.correction = float(inscrit.corrections[self.debut_recap].valeur)
                    self.libelle_correction = inscrit.corrections[self.debut_recap].libelle
            except:
                print("Warning", GetPrenomNom(inscrit), ": correction invalide", inscrit.corrections[self.debut_recap].valeur)

        self.jours_ouvres = 0
        cotisations_mensuelles = []
        heures_hebdomadaires = {}
        self.last_cotisation = None

        if options & TRACES:
            print('\nFacture de', inscrit.prenom, inscrit.nom, 'pour', months[mois - 1], annee)
               
        if inscrit.has_facture(self.debut_recap) and database.creche.cloture_facturation == CLOTURE_FACTURES_AVEC_CONTROLE and datetime.date.today() > self.fin_recap:
            fin = self.debut_recap - datetime.timedelta(1)
            debut = GetMonthStart(fin)
            if inscrit.get_inscriptions(debut, fin) and not inscrit.get_facture_cloturee(debut) and IsFacture(debut) and self.debut_recap >= config.first_date:
                error = " - La facture du mois " + GetDeMoisStr(debut.month-1) + " " + str(debut.year) + " n'est pas clôturée"
                raise CotisationException([error])

        if database.creche.mode_saisie_planning == SAISIE_HORAIRE:
            date = self.debut_recap
            while date.month == mois:
                jour_ouvre = (date not in database.creche.jours_fermeture and (database.creche.conges_inscription != GESTION_CONGES_INSCRIPTION_MENSUALISES or date not in inscrit.jours_conges))
                if jour_ouvre:
                    self.jours_ouvres += 1

                inscription = inscrit.get_inscription(date)
                if inscription:
                    self.site = inscription.site
                    if self.last_cotisation and self.last_cotisation.Include(date):
                        cotisation = self.last_cotisation
                        cotisation.jours_inscription += 1
                    else:
                        cotisation = Cotisation(inscrit, date, options=NO_ADDRESS | self.options)
                        self.last_cotisation = cotisation
                        cotisation.jours_inscription = 1
                        cotisation.jours_ouvres = 0
                        cotisation.heures_mois_ajustees = cotisation.heures_mois
                        cotisation.heures_reference = 0.0
                        cotisation.heures_realisees = 0.0
                        cotisation.heures_realisees_non_facturees = 0.0
                        cotisation.heures_facturees_non_realisees = 0.0
                        cotisation.nombre_jours_maladie_deduits = 0
                        cotisation.heures_maladie = 0.0
                        cotisation.heures_contractualisees = 0.0
                        cotisation.heures_supplementaires = 0.0
                        cotisation.total_realise_non_facture = 0.0
                        cotisations_mensuelles.append(cotisation)
                        self.taux_effort = cotisation.taux_effort
                        self.montant_heure_garde = cotisation.montant_heure_garde
                        if options & TRACES:
                            print(" => cotisation mensuelle à partir de %s :" % date, cotisation.cotisation_mensuelle)

                        if inscription.mode == MODE_FORFAIT_GLOBAL_CONTRAT:
                            reste_heures = inscription.forfait_mensuel_heures
                            index = cotisation.debut
                            while index < date and reste_heures > 0:
                                day = inscrit.days.get(index, inscription.get_day_from_date(index))
                                reste_heures -= day.get_duration(mode_arrondi=database.creche.arrondi_facturation)
                                index += datetime.timedelta(1)
                            cotisation.reste_heures = max(0, reste_heures)
                            # if cotisation.heures_realisees > reste_heures:
                            #    cotisation.heures_supplementaires = cotisation.heures_realisees - reste_heures
                            #    self.CalculeSupplement(cotisation, cotisation.heures_supplementaires)
                            #    if self.options & TRACES:
                            #        print(" heures supplémentaires :", cotisation.heures_realisees, "-", reste_heures, "=", cotisation.heures_supplementaires, "heures")

                    if jour_ouvre:
                        cotisation.jours_ouvres += 1
                        inscritState = inscrit.GetState(date, inscrit.creche.arrondi_facturation)
                        # print date, str(inscritState)
                        state, heures_reference, heures_realisees, heures_facturees = inscritState.state, inscritState.heures_contractualisees, inscritState.heures_realisees, inscritState.heures_facturees
                        if date in database.creche.jours_fermeture_non_prevus:
                            if heures_reference > 0:
                                self.jours_contractualises += 1
                                self.CalculeDeduction(cotisation, heures_reference)
                        else:
                            if heures_reference > 0:
                                self.jours_contractualises += 1
                            if heures_realisees > 0:
                                self.jours_realises += 1
                            if heures_facturees > 0:
                                self.jours_factures += 1
                            heures_facturees_non_realisees = 0.0
                            heures_realisees_non_facturees = inscrit.GetTotalActivitesPresenceNonFacturee(date)
                            heures_facturees += inscrit.GetTotalActivitesPresenceFactureesEnSupplement(date)
                            if database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(date):
                                heures_reference = 0
                                heures_supplementaires_facturees = 0
                                heures_facturees = 0
                            else:
                                heures_supplementaires_facturees = (heures_facturees - heures_reference)
                                if (options & TRACES) and heures_supplementaires_facturees:
                                    print("%f heures supplémentaires le" % heures_supplementaires_facturees, date)

                            #  retiré le 19 juillet 2017 pb d'heures supp marquées non facturées (retirées en double)
                            #  if heures_realisees_non_facturees > heures_reference:
                            #    heures_supplementaires_facturees -= heures_realisees_non_facturees - heures_reference
                            #    print "RETRANCHE" , heures_supplementaires_facturees
                            cotisation.heures_reference += heures_reference
                            if (cotisation.mode_inscription, cotisation.heures_semaine) in heures_hebdomadaires:
                                heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] += 1
                            else:
                                heures_hebdomadaires[(cotisation.mode_inscription, cotisation.heures_semaine)] = 1

                            if state == HOPITAL:
                                if options & TRACES:
                                    print("jour maladie hospitalisation", date)
                                if heures_reference > 0:
                                    self.jours_maladie.append(date)
                                self.jours_maladie_deduits.append(date)
                                cotisation.nombre_jours_maladie_deduits += 1
                                cotisation.heures_maladie += heures_reference
                                if database.creche.nom == "LA VOLIERE":
                                    pass
                                elif database.creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                    self.CalculeDeduction(cotisation, 10)
                                elif inscription.mode not in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE):
                                    self.CalculeDeduction(cotisation, heures_reference)
                                self.raison_deduction.add('hospitalisation')
                            elif database.creche.repartition != REPARTITION_SANS_MENSUALISATION and database.creche.conges_inscription == GESTION_CONGES_INSCRIPTION_NON_MENSUALISES and date in inscrit.jours_conges:
                                duration = inscription.get_day_from_date(date).get_duration(mode_arrondi=database.creche.arrondi_facturation)
                                if duration:
                                    if options & TRACES:
                                        print("jour de congé déduit", date, inscrit.jours_conges[date].label)
                                    self.jours_vacances.append(date)
                                    # self.heures_facturees_par_mode[cotisation.mode_garde] -= duration
                                    self.jours_conges_non_factures.append(date)
                                    self.CalculeDeduction(cotisation, duration)
                                    self.raison_deduction.add(inscrit.jours_conges[date].label if inscrit.jours_conges[date].label else "Congés")
                            elif state == MALADE or state == MALADE_SANS_JUSTIFICATIF:
                                if options & TRACES:
                                    print("jour maladie", date)
                                if heures_reference > 0:
                                    self.jours_maladie.append(date)
                                if state == MALADE and (database.creche.mode_facturation != FACTURATION_HORAIRES_REELS or inscription.mode in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE)):
                                    nombre_jours_maladie = inscrit.get_nombre_jours_maladie(date)
                                    if options & TRACES:
                                        print("nombre de jours : %d (minimum=%d)" % (nombre_jours_maladie, database.creche.minimum_maladie))
                                    self.heures_absence_maladie += heures_reference
                                    if nombre_jours_maladie > database.creche.minimum_maladie:
                                        self.jours_maladie_deduits.append(date)
                                        cotisation.nombre_jours_maladie_deduits += 1
                                        cotisation.heures_maladie += heures_reference
                                        if options & TRACES:
                                            print("heures déduites : %02f (total %02f)" % (heures_reference, cotisation.heures_maladie))
                                        if database.creche.nom == "LA VOLIERE":
                                            pass
                                        elif database.creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                            self.CalculeDeduction(cotisation, 10)
                                        elif inscription.mode not in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE):
                                            self.CalculeDeduction(cotisation, heures_reference)
                                        self.raison_deduction.add("maladie > %dj consécutifs" % database.creche.minimum_maladie)
                                    else:
                                        self.jours_maladie_non_deduits[date] = heures_reference
                                elif state == MALADE_SANS_JUSTIFICATIF:
                                    self.jours_maladie_non_deduits[date] = heures_reference
                            elif state == VACANCES:
                                if heures_reference > 0:
                                    self.jours_vacances.append(date)
                                if not inscription.IsNombreSemainesCongesDepasse(date):
                                    self.heures_facturees_par_mode[cotisation.mode_garde] -= heures_reference
                                    self.jours_conges_non_factures.append(date)
                                    if database.creche.repartition == REPARTITION_SANS_MENSUALISATION or database.creche.facturation_jours_feries == ABSENCES_DEDUITES_SANS_LIMITE:
                                        self.CalculeDeduction(cotisation, heures_reference)
                                        self.raison_deduction.add("absence prévenue")
                                else:
                                    self.jours_presence_selon_contrat[date] = (0.0, heures_facturees)
                            elif state == ABSENCE_NON_PREVENUE or state == ABSENCE_CONGE_SANS_PREAVIS:
                                heures_facturees_non_realisees = heures_facturees
                                self.jours_absence_non_prevenue[date] = heures_facturees
                                if heures_reference == 0:
                                    self.CalculeSupplement(cotisation, heures_facturees)
                            elif state > 0:
                                affectation_jours_supplementaires = False
                                if heures_supplementaires_facturees > 0:
                                    if database.creche.nom == "LA VOLIERE":
                                        affectation_jours_supplementaires = True
                                        self.heures_supplementaires += heures_supplementaires_facturees
                                        cotisation.heures_supplementaires += heures_supplementaires_facturees
                                    elif database.creche.mode_facturation == FACTURATION_FORFAIT_10H:
                                        affectation_jours_supplementaires = True
                                        self.CalculeSupplement(cotisation, 10)
                                    elif (database.creche.presences_supplementaires or heures_reference == 0) and (cotisation.inscription.mode not in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_GLOBAL_CONTRAT)):
                                        cotisation.heures_supplementaires += heures_supplementaires_facturees
                                        self.heures_supplementaires += heures_supplementaires_facturees
                                        self.heures_facture_par_mode[cotisation.mode_garde] += heures_supplementaires_facturees
                                        if database.creche.mode_facturation != FACTURATION_HORAIRES_REELS and (database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_FACTUREE_NORMALEMENT or not cotisation.inscription.IsInPeriodeAdaptation(date)):
                                            affectation_jours_supplementaires = True
                                            self.CalculeSupplement(cotisation, heures_supplementaires_facturees)

                                if cotisation.inscription.mode == MODE_FORFAIT_GLOBAL_CONTRAT:
                                    if heures_realisees > cotisation.reste_heures:
                                        affectation_jours_supplementaires = True
                                        heures_supplementaires_facturees = heures_realisees - cotisation.reste_heures
                                        cotisation.heures_supplementaires += heures_supplementaires_facturees
                                        self.heures_supplementaires += heures_supplementaires_facturees
                                        self.CalculeSupplement(cotisation, heures_supplementaires_facturees)
                                        if self.options & TRACES:
                                            print(" heures supplémentaires :", heures_supplementaires_facturees)
                                    cotisation.reste_heures = max(0, cotisation.reste_heures - heures_realisees)

                                if affectation_jours_supplementaires:
                                    self.jours_supplementaires[date] = (heures_realisees, heures_facturees)
                                else:
                                    self.jours_presence_selon_contrat[date] = (heures_realisees, heures_facturees)

                                if cotisation.majoration_journaliere:
                                    print(" majoration journalière :", cotisation.majoration_journaliere)
                                    self.supplement += cotisation.majoration_journaliere
                                    self.raison_supplement = self.raison_supplement.union(cotisation.raison_majoration_journaliere)

                                heures_activite_conges_deduites = inscrit.GetTotalActivitesConges(date)
                                if heures_activite_conges_deduites:
                                    print(" heures de congés déduites le", date)
                                self.heures_realisees -= heures_activite_conges_deduites
                                self.CalculeDeduction(cotisation, heures_activite_conges_deduites)

                            if database.creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE or (database.creche.tarification_activites == ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION and inscription.IsInPeriodeAdaptation(date)):
                                for timeslot in inscrit.GetExtraActivites(date):
                                    if timeslot.activity.mode != MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE:
                                        tarif = timeslot.activity.EvalTarif(self.inscrit, date, reservataire=cotisation.inscription.reservataire)
                                        if not isinstance(tarif, (int, float)):
                                            continue
                                        if tarif and (self.options & TRACES):
                                            print(" %s : activité %s = %f" % (date, timeslot.activity.label, tarif))
                                        self.supplement_activites += tarif
                                        self.heures_supplement_activites[timeslot.activity.label] += 1
                                        self.detail_supplement_activites[timeslot.activity.label] += tarif
                                        self.tarif_supplement_activites[timeslot.activity.label] = tarif
                            if 0 < heures_realisees_non_facturees == heures_realisees:
                                self.jours_presence_non_facturee[date] = heures_realisees_non_facturees

                            if inscription.mode == MODE_FORFAIT_HEBDOMADAIRE and date.weekday() == 4:
                                debut_semaine = date - datetime.timedelta(date.weekday())
                                fin_semaine = debut_semaine + datetime.timedelta(6)
                                heures_semaine = 0
                                it = debut_semaine
                                while it <= fin_semaine:
                                    if it in inscrit.days:
                                        heures = inscrit.days[it].get_duration()
                                    else:
                                        heures = inscription.get_day_from_index(it).get_duration()
                                    if heures > 0:
                                        heures_semaine += heures
                                        if heures_semaine > inscription.forfait_mensuel_heures:
                                            self.jours_supplementaires[it] = (heures_realisees, heures_facturees)
                                            if it in self.jours_presence_selon_contrat:
                                                del self.jours_presence_selon_contrat[it]
                                    it += datetime.timedelta(1)
                                forfait_mensuel_heures = inscription.forfait_mensuel_heures if inscription.forfait_mensuel_heures else 0
                                if heures_semaine > forfait_mensuel_heures:
                                    cotisation.heures_supplementaires += heures_semaine - forfait_mensuel_heures

                            realise_non_facture = cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees) - cotisation.CalculeFraisGarde(cotisation.heures_mois_ajustees - heures_realisees_non_facturees)
                            cotisation.total_realise_non_facture += realise_non_facture
                            self.total_realise_non_facture += realise_non_facture
                            self.heures_realisees += heures_realisees
                            self.heures_realisees_non_facturees += heures_realisees_non_facturees
                            self.heures_facturees_non_realisees += heures_facturees_non_realisees
                            cotisation.heures_realisees += heures_realisees
                            cotisation.heures_realisees_non_facturees += heures_realisees_non_facturees
                            cotisation.heures_facturees_non_realisees += heures_facturees_non_realisees

                            if cotisation.inscription.mode not in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE):
                                cotisation.heures_contractualisees += heures_reference
                                self.heures_contractualisees += heures_reference
                                self.heures_contractualisees_realisees += min(heures_realisees, heures_reference)
                                if database.creche.mode_facturation == FACTURATION_HORAIRES_REELS or (database.creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE):
                                    self.heures_facturees_par_mode[cotisation.mode_garde] += heures_realisees - heures_realisees_non_facturees + heures_facturees_non_realisees
                                    self.total_contractualise += cotisation.CalculeFraisGarde(heures_reference)
                                elif database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(date):
                                    if database.creche.nom == "LA VOLIERE":
                                        heures_adaptation = heures_realisees  # - heures_realisees_non_facturees + heures_facturees_non_realisees
                                        self.heures_supplementaires += heures_adaptation
                                        self.jours_presence_selon_contrat[date] = (heures_adaptation, heures_adaptation)
                                        self.heures_periode_adaptation += heures_adaptation
                                        self.heures_facturees_par_mode[cotisation.mode_garde] += heures_adaptation
                                        # montant_adaptation = cotisation.CalculeFraisGarde(heures_adaptation)
                                        # self.cotisation_periode_adaptation += montant_adaptation
                                        # self.supplement += montant_adaptation
                                        # self.raison_supplement.add("%s heures adaptation" % GetHeureString(heures_adaptation))
                                        # self.total_realise += montant_adaptation
                                    else:
                                        heures_adaptation = heures_realisees #  - heures_realisees_non_facturees + heures_facturees_non_realisees
                                        self.heures_supplementaires += heures_adaptation
                                        self.jours_presence_selon_contrat[date] = (heures_adaptation, heures_adaptation)
                                        self.heures_periode_adaptation += heures_adaptation
                                        self.heures_facturees_par_mode[cotisation.mode_garde] += heures_adaptation
                                        montant_adaptation = cotisation.CalculeFraisGarde(heures_adaptation)
                                        self.cotisation_periode_adaptation += montant_adaptation
                                        self.supplement += montant_adaptation
                                        # self.raison_supplement.add("%s heures adaptation" % GetHeureString(heures_adaptation))
                                        self.total_realise += montant_adaptation
                                else:
                                    self.heures_facturees_par_mode[cotisation.mode_garde] += heures_facturees
                            self.total_realise += cotisation.CalculeFraisGarde(heures_realisees - heures_realisees_non_facturees)

                date += datetime.timedelta(1)
        else:
            monday = GetNextMonday(self.debut_recap)
            if monday.day >= 6:
                monday -= datetime.timedelta(7)
            while (monday + datetime.timedelta(2)).month == mois:
                week_slots = inscrit.get_week_slots(monday)
                if week_slots:
                    cotisation = Cotisation(inscrit, monday, options=NO_ADDRESS | self.options)
                    self.taux_effort = cotisation.taux_effort
                    if database.creche.mode_saisie_planning == SAISIE_JOURS_SEMAINE:
                        self.montant_jour_garde = cotisation.montant_heure_garde
                    else:
                        self.montant_heure_garde = cotisation.montant_heure_garde
                    for slot in week_slots:
                        activite = slot.activity
                        if activite in database.creche.activites or activite in database.creche.states.values():
                            compteur = slot.value if slot.value else 0
                            if activite.mode == MODE_PRESENCE:
                                if database.creche.mode_saisie_planning == SAISIE_JOURS_SEMAINE:
                                    self.jours_realises += compteur
                                else:
                                    self.heures_realisees += compteur
                                    self.heures_facturees_par_mode[cotisation.mode_garde] += compteur
                                self.cotisation_mensuelle += compteur * cotisation.montant_heure_garde
                            else:
                                tarif = activite.EvalTarif(inscrit, monday, cotisation.montant_heure_garde, reservataire=cotisation.inscription.reservataire)
                                total = compteur * tarif
                                self.supplement_activites += total
                                self.heures_supplement_activites[activite.label] += compteur
                                self.detail_supplement_activites[activite.label] += total
                                self.tarif_supplement_activites[activite.label] = tarif

                monday += datetime.timedelta(7)
            
        if options & NO_NUMERO:
            self.numero = 0
        else:
            self.numero = self.GetNumeroFacture()

        if inscrit.has_facture(self.debut_recap):
            for cotisation in cotisations_mensuelles:
                inscription = cotisation.inscription
                self.heures_maladie += cotisation.heures_maladie
                self.heures_facture_par_mode[cotisation.mode_garde] -= cotisation.heures_maladie
                if database.creche.nom == "LA VOLIERE":
                    heures = cotisation.heures_contractualisees + cotisation.heures_supplementaires - cotisation.heures_maladie
                    tarif_horaire = (cotisation.a * heures + cotisation.b)
                    self.cotisation_mensuelle += heures * tarif_horaire
                    if self.heures_periode_adaptation:
                        tarif_horaire = (cotisation.a * (heures + self.heures_periode_adaptation) + cotisation.b)
                        self.cotisation_periode_adaptation = self.heures_periode_adaptation * tarif_horaire
                        # print(self.cotisation_periode_adaptation, tarif_horaire, self.heures_periode_adaptation)
                        self.supplement += self.cotisation_periode_adaptation
                elif database.creche.repartition == REPARTITION_SANS_MENSUALISATION:
                    if database.creche.mode_facturation == FACTURATION_HORAIRES_REELS or (database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(cotisation.debut)):
                        montant = (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees) * cotisation.montant_heure_garde
                    else:
                        montant = (cotisation.heures_contractualisees - cotisation.heures_realisees_non_facturees) * cotisation.montant_heure_garde
                    self.cotisation_mensuelle += montant
                    self.total_contractualise += montant
                elif database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_GRATUITE and inscription.IsInPeriodeAdaptation(cotisation.debut):
                    pass
                elif database.creche.facturation_periode_adaptation == PERIODE_ADAPTATION_HORAIRES_REELS and inscription.IsInPeriodeAdaptation(cotisation.debut):
                    if inscription.mode in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE):
                        self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees
                    report = cotisation.CalculeFraisGarde(cotisation.heures_realisees)
                    self.report_cotisation_mensuelle += report
                    # cotisation.prorata = False  # TODO ? si oui => unittest
                    if options & TRACES:
                        print(" cotisation periode adaptation :", report)
                elif inscription.mode == MODE_FORFAIT_HEBDOMADAIRE:
                    if cotisation.prorata:
                        prorata = cotisation.cotisation_mensuelle * cotisation.jours_ouvres / self.jours_ouvres
                    else:
                        prorata = cotisation.cotisation_mensuelle
                    self.cotisation_mensuelle += prorata
                    cotisation.heures_contractualisees = cotisation.heures_mois * cotisation.jours_ouvres / self.jours_ouvres
                    self.total_contractualise += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                    self.heures_supplementaires += cotisation.heures_supplementaires
                    self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees - cotisation.heures_realisees_non_facturees
                    self.heures_facture_par_mode[cotisation.mode_garde] += cotisation.heures_mois + cotisation.heures_supplementaires
                    self.CalculeSupplement(cotisation, cotisation.heures_supplementaires)
                elif inscription.mode == MODE_FORFAIT_MENSUEL:
                    if not cotisation.cotisation_mensuelle:
                        prorata = 0.0
                    elif cotisation.prorata:
                        prorata = cotisation.cotisation_mensuelle * cotisation.jours_ouvres / self.jours_ouvres
                    else:
                        prorata = cotisation.cotisation_mensuelle
                    self.cotisation_mensuelle += prorata
                    forfait = inscription.forfait_mensuel_heures or 0
                    cotisation.heures_contractualisees = forfait * cotisation.jours_ouvres / self.jours_ouvres
                    self.heures_contractualisees += cotisation.heures_contractualisees
                    self.total_contractualise += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                    if cotisation.nombre_jours_maladie_deduits > 0:
                        # retire parce que "montant" non defini ... self.deduction += montant * cotisation.nombre_jours_maladie_deduits / cotisation.jours_ouvres
                        heures_contractualisees = cotisation.heures_contractualisees * (cotisation.jours_ouvres - cotisation.nombre_jours_maladie_deduits) / cotisation.jours_ouvres
                    else:
                        heures_contractualisees = cotisation.heures_contractualisees
                    if database.creche.presences_supplementaires and cotisation.heures_realisees - cotisation.heures_realisees_non_facturees > heures_contractualisees:
                        cotisation.heures_supplementaires = cotisation.heures_realisees - cotisation.heures_realisees_non_facturees - heures_contractualisees
                        self.heures_facturees_par_mode[cotisation.mode_garde] += cotisation.heures_realisees - cotisation.heures_realisees_non_facturees
                        self.heures_supplementaires += cotisation.heures_supplementaires
                        self.heures_facture_par_mode[cotisation.mode_garde] += cotisation.heures_supplementaires
                        self.CalculeSupplement(cotisation, cotisation.heures_supplementaires)
                    else:
                        self.heures_facturees_par_mode[cotisation.mode_garde] += heures_contractualisees
                elif database.creche.mode_facturation == FACTURATION_HORAIRES_REELS:
                    self.cotisation_mensuelle += cotisation.heures_contractualisees * cotisation.montant_heure_garde
                    self.report_cotisation_mensuelle += (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees - cotisation.heures_contractualisees) * cotisation.montant_heure_garde
                elif database.creche.mode_facturation == FACTURATION_PSU and cotisation.mode_garde == MODE_HALTE_GARDERIE:
                    # On ne met dans la cotisation mensuelle que les heures realisees des heures du contrat
                    self.supplement += (cotisation.heures_realisees - cotisation.heures_realisees_non_facturees + cotisation.heures_facturees_non_realisees - cotisation.heures_supplementaires) * cotisation.montant_heure_garde
                    # print '(', cotisation.heures_realisees, '-', cotisation.heures_realisees_non_facturees, '+', cotisation.heures_facturees_non_realisees, '-', cotisation.heures_supplementaires, ') *', cotisation.montant_heure_garde, '=', self.cotisation_mensuelle
                elif database.creche.mode_facturation == FACTURATION_PSU and self.heures_contractualisees:
                    prorata_heures = cotisation.heures_mois * cotisation.jours_ouvres / self.jours_ouvres
                    if cotisation.prorata and cotisation.nombre_factures > 0:
                        prorata = cotisation.cotisation_mensuelle * cotisation.jours_ouvres / self.jours_ouvres
                    else:
                        prorata = cotisation.cotisation_mensuelle
                    if cotisation.total_realise_non_facture:
                        self.deduction += cotisation.total_realise_non_facture
                        self.raison_deduction.add("heures non facturées")
                    if cotisation.IsContratFacture(self.debut_recap):
                        self.cotisation_mensuelle += prorata
                    self.total_contractualise += prorata
                    self.heures_contrat += prorata_heures
                    self.heures_facture_par_mode[cotisation.mode_garde] += prorata_heures
                else:
                    # Bug sur la Cabane aux familles le 20/09/2016
                    # Un enfant en adaptation du 15 janvier au 19 janvier
                    # Le prorata etait fait ici, et la mensualisation etait beaucoup trop haute
                    prorata_effectue = False
                    if 0:  # self.heures_contractualisees:
                        if cotisation.heures_reference != self.heures_contractualisees:
                            prorata = cotisation.cotisation_mensuelle * cotisation.heures_reference / self.heures_contractualisees
                            prorata_heures = cotisation.heures_mois * cotisation.heures_reference / self.heures_contractualisees
                            prorata_effectue = True
                            if options & TRACES: 
                                print(" prorata : %f * %f / %f = %f" % (cotisation.cotisation_mensuelle, cotisation.heures_reference, self.heures_contractualisees, prorata))
                        else:
                            prorata = cotisation.cotisation_mensuelle
                            prorata_heures = cotisation.heures_mois
                    else:
                        prorata = cotisation.cotisation_mensuelle
                        prorata_heures = cotisation.heures_mois
                    # ajoute FACTURATION_PSU bloc plus haut pour eviter 2 * la regle de 3
                    # avant il y avait ce commentaire: ne marche pas pour saint julien, mais c'est redemande (2 octobre 2012), normal pour le premier mois pour un enfant qui arrive mi-septembre
                    # avec le test suivant on devrait etre bon, parce que sinon on effectue la regle de 3 dans la cotisation + ici
                    if cotisation.prorata and not prorata_effectue:
                        if database.creche.prorata == PRORATA_MOIS_COMPLET:
                            days_count = GetMonthDaysCount(self.debut_recap)
                            new_prorata = (prorata * cotisation.jours_inscription) / days_count
                            new_prorata_heures = (prorata_heures * cotisation.jours_inscription) / days_count
                            if options & TRACES:
                                print(" prorata (mois complet) : %f * %f / %f = %f" % (prorata, cotisation.jours_inscription, days_count, new_prorata))
                        elif self.jours_ouvres:
                            new_prorata = (prorata * cotisation.jours_ouvres) / self.jours_ouvres
                            new_prorata_heures = (prorata_heures * cotisation.jours_ouvres) / self.jours_ouvres
                            if options & TRACES:
                                print(" prorata (jours ouvrés) : %f * %f / %f = %f" % (prorata, cotisation.jours_ouvres, self.jours_ouvres, new_prorata))
                        else:
                            new_prorata = prorata
                            new_prorata_heures = prorata_heures
                        prorata = new_prorata
                        prorata_heures = new_prorata_heures

                    if cotisation.IsContratFacture(self.debut_recap):
                        self.cotisation_mensuelle += prorata

                    self.total_contractualise += prorata
                    self.heures_contrat += prorata_heures
                    self.heures_facture_par_mode[cotisation.mode_garde] += prorata_heures

                if cotisation.montant_mensuel_activites:
                    if database.creche.prorata == PRORATA_MOIS_COMPLET:
                        days_count = GetMonthDaysCount(self.debut_recap)
                        montant_activites_mensualisees = cotisation.montant_mensuel_activites * cotisation.jours_inscription / days_count
                        if options & TRACES:
                            print(" activites mensualisees : %0.2f * %d / %d = %0.2f" % (cotisation.montant_mensuel_activites, cotisation.jours_inscription, days_count, montant_activites_mensualisees))
                    else:
                        montant_activites_mensualisees = cotisation.montant_mensuel_activites * cotisation.jours_ouvres / self.jours_ouvres
                        if options & TRACES:
                            print(" activites mensualisees : %0.2f * %d / %d = %0.2f" % (cotisation.montant_mensuel_activites, cotisation.jours_ouvres, self.jours_ouvres, montant_activites_mensualisees))
                    self.supplement_activites += montant_activites_mensualisees
                    self.detail_supplement_activites["Activites mensualisees"] += montant_activites_mensualisees
                    self.tarif_supplement_activites["Activites mensualisees"] = montant_activites_mensualisees

                if database.creche.regularisation_fin_contrat or database.creche.regularisation_conges_non_pris:
                    depart_anticipe = database.creche.gestion_depart_anticipe and inscription.depart and self.debut_recap <= inscription.depart <= self.fin_recap
                    dernier_mois = (depart_anticipe or inscription.fin and self.debut_recap <= inscription.fin <= self.fin_recap)

                    if depart_anticipe and cotisation.Include(inscription.depart):
                        date_fin_cotisation = inscription.depart
                        if database.creche.regularisation_fin_contrat and database.creche.repartition != REPARTITION_SANS_MENSUALISATION:
                            date = cotisation.debut
                            while date <= inscription.depart:
                                cotisation_regularisee = Cotisation(inscrit, date, options=NO_ADDRESS | DEPART_ANTICIPE | self.options)
                                regularisation_cotisation = cotisation_regularisee.cotisation_mensuelle - cotisation.cotisation_mensuelle
                                regularisation_periode = regularisation_cotisation * cotisation_regularisee.nombre_factures
                                if abs(regularisation_periode) > 0.01:
                                    if options & TRACES:
                                        print(" régularisation cotisation : %f - %f = %f par mois => %f" % (cotisation_regularisee.cotisation_mensuelle, cotisation.cotisation_mensuelle, regularisation_cotisation, regularisation_periode))
                                    self.regularisation += regularisation_periode
                                    self.raison_regularisation.add("régularisation cotisation")
                                date = cotisation.fin + datetime.timedelta(1)
                    else:
                        date_fin_cotisation = inscription.fin

                    if database.creche.regularisation_conges_non_pris:
                        if inscription.mode in (MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_MENSUEL):
                            jours_presence = database.creche.get_nombre_jours_semaine_travailles()
                        else:
                            jours_presence = inscription.get_days_per_week()
                        if jours_presence and inscription.semaines_conges:
                            if dernier_mois:
                                if config.options & REGULARISATION_UNIQUEMENT_SEMAINES_FERMETURE:
                                    # pour Nos petits pouces
                                    semaines_conges_a_prendre = inscription.semaines_conges
                                elif database.creche.repartition == REPARTITION_MENSUALISATION_12MOIS:
                                    semaines_conges_a_prendre = float(inscription.semaines_conges) * (date_fin_cotisation - inscription.debut).days / 365
                                else:
                                    semaines_conges_a_prendre = inscription.semaines_conges
                                jours_conges_pris = inscription.GetNombreJoursCongesPoses()
                                semaines_conges_pris = float(jours_conges_pris) / jours_presence
                                semaines_conges_non_pris = semaines_conges_a_prendre - semaines_conges_pris
                                if semaines_conges_non_pris > 0:
                                    heures = cotisation.heures_semaine * semaines_conges_non_pris
                                    regularisation_conges_non_pris = heures * cotisation.montant_heure_garde
                                    if options & TRACES:
                                        print(" régularisation congés non pris (%0.1f semaines à prendre, %d jours pris = %0.1f semaines) : %0.1fh * %0.2f = %0.2f" % (semaines_conges_a_prendre, jours_conges_pris, semaines_conges_pris, heures, cotisation.montant_heure_garde, regularisation_conges_non_pris))
                                    self.regularisation += regularisation_conges_non_pris
                                    self.raison_regularisation.add("congés non pris")

        if self.supplement > 0 and self.heures_supplementaires_facture > 0:
            self.supplement_heures_supplementaires = self.supplement
            self.raison_supplement.add("%s heures supplémentaires" % GetHeureString(self.heures_supplementaires_facture))

        self.supplement_avant_regularisation = self.supplement
        self.raison_supplement_avant_regularisation = self.raison_supplement
        self.deduction_avant_regularisation = self.deduction
        self.raison_deduction_avant_regularisation = self.raison_deduction

        if self.regularisation > 0:
            self.supplement += self.regularisation
            self.raison_supplement.update(self.raison_regularisation)
        elif self.regularisation < 0:
            self.deduction -= self.regularisation
            self.raison_deduction.update(self.raison_regularisation)

        self.heures_facturees = sum(self.heures_facturees_par_mode)
        if database.creche.mode_saisie_planning == SAISIE_HORAIRE:
            self.heures_facture = self.heures_contrat + self.heures_supplementaires - self.heures_maladie
        else:
            self.heures_facture = self.heures_facturees
        if database.creche.temps_facturation == FACTURATION_FIN_MOIS:
            self.cotisation_mensuelle += self.report_cotisation_mensuelle
            self.report_cotisation_mensuelle = 0.0

        # arrondi de tous les champs en euros
        self.cotisation_mensuelle = round(self.cotisation_mensuelle, 2)

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
        self.raison_regularisation = self.join_raison(self.raison_regularisation)
        self.raison_deduction = self.join_raison(self.raison_deduction)
        self.raison_deduction_avant_regularisation = self.join_raison(self.raison_deduction_avant_regularisation)
        self.raison_supplement = self.join_raison(self.raison_supplement)
        self.raison_supplement_avant_regularisation = self.join_raison(self.raison_supplement_avant_regularisation)
        self.total_contractualise = round(self.total_contractualise, 2)
        self.total_realise = round(self.total_realise, 2)
        
        self.majoration_mensuelle = 0.0
        for tarif in database.creche.tarifs_speciaux:
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
            if not inscription.preinscription and inscription.frais_inscription and inscription.debut and self.debut_recap <= inscription.debut <= self.fin_recap:
                if inscription.reservataire and (config.options & FRAIS_INSCRIPTION_RESERVATAIRES):
                    self.frais_inscription_reservataire += inscription.frais_inscription
                else:
                    self.frais_inscription += inscription.frais_inscription

        if database.creche.arrondi_mensualisation_euros == ARRONDI_EURO_PLUS_PROCHE:
            self.cotisation_mensuelle = round(self.cotisation_mensuelle)

        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction
        self.total_facture = self.total + self.report_cotisation_mensuelle

        if options & TRACES:
            print("Récapitulatif :")
            for var in ["heures_contractualisees", "heures_facturees", "heures_facture", "heures_realisees", "heures_supplementaires", "heures_contractualisees_realisees", "heures_realisees_non_facturees", "heures_facturees_non_realisees", "cotisation_mensuelle", "supplement", "deduction", "supplement_activites", "total"]:
                print("", var, ':', eval("self.%s" % var))
            print()
        
    def formule_supplement_activites(self, activites):
        result = 0.0
        for activite in activites:
            result += self.detail_supplement_activites[activite]
        return locale.format("%+.2f", result)

    def formule_heures_supplement_activites(self, activites):
        result = 0.0
        for activite in activites:
            result += self.heures_supplement_activites[activite]
        if database.creche.mode_saisie_planning == SAISIE_JOURS_SEMAINE:
            return str(result)
        else:
            return GetHeureString(result)

    def formule_compte_supplement_activites(self, activites):
        result = 0.0
        for activite in activites:
            result += self.heures_supplement_activites[activite]
        return "%d" % result

    def formule_tarif_activite(self, activite):
        tarif = self.tarif_supplement_activites[activite]
        return str(tarif)


class FactureDebutMois(FactureFinMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureFinMois.__init__(self, inscrit, annee, mois, options)
        self.heures_previsionnelles = self.heures_realisees
        if options & TRACES:
            print("Calcul de la facture du mois précédent pour le report...")
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
        self.heures_periode_adaptation = self.facture_precedente.heures_periode_adaptation
        self.cotisation_periode_adaptation = self.facture_precedente.cotisation_periode_adaptation


class FactureDebutMoisContrat(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        self.cotisation_mensuelle += self.facture_precedente.report_cotisation_mensuelle
        self.supplement = self.facture_precedente.supplement
        self.deduction = self.facture_precedente.deduction
        self.supplement_activites = self.facture_precedente.supplement_activites
        self.heures_supplement_activites = self.facture_precedente.heures_supplement_activites
        self.detail_supplement_activites = self.facture_precedente.detail_supplement_activites
        self.tarif_supplement_activites = self.facture_precedente.tarif_supplement_activites
        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction
        self.total_facture = self.total


class FactureDebutMoisPrevisionnel(FactureDebutMois):
    def __init__(self, inscrit, annee, mois, options=0):
        FactureDebutMois.__init__(self, inscrit, annee, mois, options)
        
        if datetime.date.today() > self.fin_recap:
            if inscrit.get_inscriptions(self.facture_precedente.debut_recap, self.facture_precedente.fin_recap):
                if self.facture_precedente.date not in inscrit.clotures:
                    error = " - La facture du mois " + GetDeMoisStr(self.facture_precedente.date.month-1) + " " + str(self.facture_precedente.date.year) + " n'est pas clôturée"
                    raise CotisationException([error])
                facture_cloturee = FactureCloturee(inscrit.clotures[self.facture_precedente.date], options)
                self.cotisation_mensuelle += self.facture_precedente.cotisation_mensuelle - facture_cloturee.cotisation_mensuelle
                self.supplement += self.facture_precedente.supplement - facture_cloturee.supplement
                self.deduction += self.facture_precedente.deduction - facture_cloturee.deduction
                self.supplement_activites += self.facture_precedente.supplement_activites - facture_cloturee.supplement_activites            
        
        self.cotisation_mensuelle += self.report_cotisation_mensuelle
        self.total = self.cotisation_mensuelle + self.frais_inscription + self.supplement + self.supplement_activites - self.deduction + self.correction
        self.total_facture = self.total

    def Cloture(self):
        facture_previsionnelle = FactureFinMois(self.inscrit, self.annee, self.mois)
        facture_previsionnelle.Cloture()
        FactureFinMois.Cloture(self)


def CreateFacture(inscrit, annee, mois, options=0):
    if database.creche.temps_facturation == FACTURATION_FIN_MOIS:
        return FactureFinMois(inscrit, annee, mois, options)
    elif database.creche.temps_facturation == FACTURATION_DEBUT_MOIS_CONTRAT:
        return FactureDebutMoisContrat(inscrit, annee, mois, options)
    else:
        return FactureDebutMoisPrevisionnel(inscrit, annee, mois, options)


class FactureCloturee(FactureBase):
    def __init__(self, cloture, options=0):
        self.cloture = cloture
        self.options = options
        self.facture = None

    def restore(self, options=0):
        if not self.facture:
            self.facture = CreateFacture(self.cloture.inscrit, self.cloture.date.year, self.cloture.date.month, options=self.options)
        return self.facture

    def __getattr__(self, item):
        if hasattr(self.cloture, item):
            return getattr(self.cloture, item)
        else:
            if not self.facture:
                # print("Restauration facture (%s) ..." % item)
                self.restore()
            return getattr(self.facture, item)


def Facture(inscrit, annee, mois, options=0):
    result = inscrit.get_facture_cloturee(datetime.date(annee, mois, 1))
    if result:
        return FactureCloturee(result, options)
    return CreateFacture(inscrit, annee, mois, options)


class FactureReservataire(object):
    def __init__(self, reservataire, date):
        self.reservataire = reservataire
        self.debut = date
        self.date = date
        self.nombre_mois = reservataire.periode_facturation
        if self.nombre_mois:
            for i in range(reservataire.periode_facturation):
                self.fin = GetMonthEnd(date)
                if reservataire.debut > self.fin or (reservataire.fin and self.reservataire.fin < date):
                    self.nombre_mois -= 1
                date = GetNextMonthStart(date)
        if reservataire.has_facture(self.debut) and reservataire.tarif:
            self.total = reservataire.tarif * self.nombre_mois
        else:
            self.total = .0
        self.total_facture = self.total


def GetHistoriqueSolde(who, jalon=datetime.date.today()):
    lignes = [encaissement for encaissement in who.encaissements]
    if isinstance(who, Reservataire):
        for date in who.get_factures_list():
            if config.is_date_after_reglements_start(date) and date <= jalon:
                lignes.append(FactureReservataire(who, date))
    else:
        inscrits = GetInscritsFamille(who)
        debut, fin = None, None
        for inscrit in inscrits:
            debut_inscrit, fin_inscrit = inscrit.GetPeriodeInscriptions()
            if debut_inscrit is None:
                print("Erreur sur la période d'accueil de %s" % GetPrenomNom(inscrit))
            elif debut is None or debut_inscrit < debut:
                debut = debut_inscrit
            if fin is None or fin_inscrit is None or fin_inscrit > fin:
                fin = fin_inscrit
        if debut is None:
            return lignes
        if fin is None or fin > jalon:
            fin = jalon
        date = GetMonthStart(debut)
        if config.date_debut_reglements and config.date_debut_reglements > date:
            date = config.date_debut_reglements
        fin = min(datetime.date.today(), GetMonthEnd(fin))
        while date <= fin:
            for inscrit in inscrits:
                try:
                    facture = Facture(inscrit, date.year, date.month, NO_NUMERO | NO_RESTORE_CLOTURE)
                    if config.is_date_after_reglements_start(facture.fin_recap) and facture.total_facture != 0:
                        if (database.creche.cloture_facturation and facture.cloture) or facture.fin_recap < GetMonthStart(jalon):
                            lignes.append(facture)
                except Exception as e:
                    print("Exception", repr(e))
            date = GetNextMonthStart(date)
    lignes.sort(key=lambda ligne: ligne.date if ligne.date else today)
    return lignes


def GetValeurLigneHistorique(ligne):
    if isinstance(ligne, EncaissementFamille) or isinstance(ligne, EncaissementReservataire):
        return ligne.valeur
    else:
        return -ligne.total_facture


def CalculeSoldeFromHistorique(historique):
    solde = 0.0
    for ligne in historique:
        solde -= GetValeurLigneHistorique(ligne)
    return solde


def CalculeSolde(who, date):
    historique = GetHistoriqueSolde(who, date)
    return CalculeSoldeFromHistorique(historique)


def GetRetardDePaiement(who):
    delai = who.get_delai_paiement()
    if delai is None:
        return None
    historique = GetHistoriqueSolde(who)
    solde = CalculeSoldeFromHistorique(historique)
    last_date = None
    for ligne in reversed(historique):
        if solde <= 0.01:
            break
        if isinstance(ligne, EncaissementFamille) or isinstance(ligne, EncaissementReservataire):
            solde += ligne.valeur
        else:
            solde -= ligne.total_facture
        last_date = ligne.date
    if not last_date:
        return None
    if (today - last_date).days > delai:
        return last_date


def ClotureFactures(inscrits, date, cloture=True):
    errors = {}
    for inscrit in inscrits:
        try:
            facture = Facture(inscrit, date.year, date.month, NO_NUMERO)
            if cloture:
                facture.Cloture()
            elif facture.cloture:
                facture.Decloture()
        except CotisationException as e:
            errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
            continue
    return errors

