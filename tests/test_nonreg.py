#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


from __future__ import unicode_literals
from __future__ import division

import unittest
import pytest
from cotisation import *
from facture import Facture
from generation.planning_detaille import PlanningDetailleModifications
from generation.coordonnees_parents import CoordonneesModifications
from generation.releve_detaille import ReleveDetailleModifications
from generation.etats_trimestriels import EtatsTrimestrielsModifications
from ooffice import GenerateOODocument
from database import *
from globals import *
from statistiques import GetStatistiques


config.first_date = datetime.date(2010, 1, 1)


class DatesTestCase(unittest.TestCase):
    def test_incr_date(self):
        self.assertEquals(IncrDate(datetime.date(2010, 12, 31), years=1, months=1), datetime.date(2012, 1, 31))
        self.assertEquals(IncrDate(datetime.date(2010, 3, 31), years=0, months=1), datetime.date(2010, 5, 1))
        self.assertEquals(IncrDate(datetime.date(2016, 2, 29), years=1, months=0), datetime.date(2017, 3, 1))


class GertrudeTestCase(unittest.TestCase):
    def setUp(self):
        database.init(":memory:")
        database.create(False)
        database.load()

    @staticmethod
    def add_ferie(label):
        database.creche.add_ferie(CongeStructure(creche=database.creche, debut=label))

    @staticmethod
    def add_conge(debut, fin="", options=0):
        database.creche.add_conge(CongeStructure(creche=database.creche, debut=debut, fin=fin, options=options))

    @staticmethod
    def add_parents(inscrit, salaire=30000.0):
        del inscrit.famille.parents[0].revenus[0]
        del inscrit.famille.parents[1].revenus[0]
        revenu = Revenu(parent=inscrit.famille.parents[0], debut=datetime.date(2008, 1, 1), fin=datetime.date(2014, 12, 31))
        revenu.revenu = salaire
        inscrit.famille.parents[0].revenus.append(revenu)
        revenu = Revenu(parent=inscrit.famille.parents[1], debut=datetime.date(2008, 1, 1), fin=datetime.date(2014, 12, 31))
        revenu.revenu = 0.0
        inscrit.famille.parents[1].revenus.append(revenu)
        for year in range(2015, 2020):
            revenu = Revenu(parent=inscrit.famille.parents[0], debut=datetime.date(year, 1, 1), fin=datetime.date(year, 12, 31))
            revenu.revenu = salaire
            inscrit.famille.parents[0].revenus.append(revenu)
            revenu = Revenu(parent=inscrit.famille.parents[1], debut=datetime.date(year, 1, 1), fin=datetime.date(year, 12, 31))
            revenu.revenu = salaire
            inscrit.famille.parents[1].revenus.append(revenu)

    def add_inscrit(self):
        inscrit = Inscrit(creche=database.creche)
        inscrit.prenom, inscrit.nom = 'Gertrude', 'GPL'
        inscrit.naissance = datetime.date(2010, 1, 1)
        self.add_parents(inscrit)
        database.creche.inscrits.append(inscrit)
        return inscrit
    
    @staticmethod
    def add_salarie():
        salarie = Salarie(creche=database.creche)
        salarie.prenom, salarie.nom = 'Gertrude', 'GPL'
        database.creche.salaries.append(salarie)
        return salarie    
    
    @staticmethod
    def add_activite(inscrit, date, debut, fin, activity):
        inscrit.days.add(TimeslotInscrit(date=date, debut=debut, fin=fin, activity=activity))

    @staticmethod
    def add_inscription_timeslot(inscription, day, debut, fin, activity=None):
        if activity is None:
            activity = database.creche.states[0]
        inscription.days.add(TimeslotInscription(day=day, debut=debut, fin=fin, activity=activity))

    @staticmethod
    def add_planning_salarie_timeslot(planning, day, debut, fin, activity=None):
        if activity is None:
            activity = database.creche.states[0]
        planning.days.add(TimeslotPlanningSalarie(day=day, debut=debut, fin=fin, activity=activity))

    def add_journee_presence(self, inscrit, date, debut, fin):
        self.add_activite(inscrit, date, debut, fin, database.creche.states[0])
        
    @staticmethod
    def add_frere(inscrit, naissance=datetime.date(2000, 1, 1)):
        result = Fratrie(famille=inscrit.famille, prenom="Frere ou Soeur", naissance=naissance)
        inscrit.famille.freres_soeurs.append(result)
        return result

    @staticmethod
    def set_revenus(inscrit, revenus):
        for i in range(len(inscrit.famille.parents[0].revenus)):
            inscrit.famille.parents[0].revenus[i].revenu = revenus / len(inscrit.famille.parents)
            inscrit.famille.parents[1].revenus[i].revenu = revenus / len(inscrit.famille.parents)

    def assert_prec2_equals(self, montant1, montant2):
        self.assertEqual("%.2f" % montant1, "%.2f" % montant2)


@pytest.mark.skipif("sys.version_info >= (3, 0)")
class PlanningTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        self.activity_presence = database.creche.states[MODE_PRESENCE]
        self.activity_ski = Activite(database.creche, mode=MODE_LIBERE_PLACE)
        database.creche.add_activite(self.activity_ski)
        self.activity_repas = Activite(database.creche, mode=MODE_NORMAL)
        database.creche.add_activite(self.activity_repas)

    def test_ski(self):
        from planning import BasePlanningLine
        day = BasePlanningLine()
        day.set_activity(0, 10, self.activity_presence)
        day.set_activity(2, 8, self.activity_ski)
        self.assertEquals(len(day.timeslots), 3)
    
    def test_repas(self):
        from planning import BasePlanningLine
        day = BasePlanningLine()
        day.set_activity(0, 10, self.activity_presence)
        day.set_activity(2, 8, self.activity_repas)
        self.assertEquals(len(day.timeslots), 2)


class DocumentsTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        self.pwd = os.getcwd()
        os.chdir("..")
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 6.70, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        for i in range(10):
            inscrit = self.add_inscrit()
            inscription = Inscription(inscrit=inscrit)
            inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
            inscription.mode = MODE_TEMPS_PLEIN
            self.add_inscription_timeslot(inscription, 0, 96, 180)
            self.add_inscription_timeslot(inscription, 1, 96, 180)
            self.add_inscription_timeslot(inscription, 2, 96, 180)
            self.add_inscription_timeslot(inscription, 3, 96, 180)
            self.add_inscription_timeslot(inscription, 4, 96, 180)
            inscrit.inscriptions.append(inscription)
            
            salarie = self.add_salarie()
            contrat = ContratSalarie(salarie=salarie, debut=datetime.date(2010, 9, 6), fin=datetime.date(2011, 7, 27))
            planning = PlanningSalarie(contrat=contrat, debut=contrat.debut)
            contrat.plannings.append(planning)
            self.add_planning_salarie_timeslot(planning, 0, 96, 180)
            self.add_planning_salarie_timeslot(planning, 1, 96, 180)
            self.add_planning_salarie_timeslot(planning, 2, 96, 180)
            self.add_planning_salarie_timeslot(planning, 3, 96, 180)
            self.add_planning_salarie_timeslot(planning, 4, 96, 180)
            salarie.contrats.append(contrat)
    
    def tearDown(self):
        os.chdir(self.pwd)
                    
    def test_planning_detaille(self):
        modifications = PlanningDetailleModifications((datetime.date(2010, 9, 7), datetime.date(2010, 9, 30)))
        errors = GenerateOODocument(modifications, filename="./test.odg", gauge=None)
        self.assertEquals(len(errors), 0)
        os.unlink("./test.odg")
        
    def test_coordonnees_parents(self):
        modifications = CoordonneesModifications(None, datetime.date(2010, 9, 7))
        errors = GenerateOODocument(modifications, filename="./test.odt", gauge=None)
        self.assertEquals(len(errors), 0)
        os.unlink("./test.odt")

    def test_releves_trimestriels(self):
        modifications = EtatsTrimestrielsModifications(None, 2011)
        errors = GenerateOODocument(modifications, filename="./test.ods", gauge=None)
        self.assertEquals(len(errors), 0)
        os.unlink("./test.ods")    

    def test_releves_detailles(self):
        modifications = ReleveDetailleModifications(None, 2011)
        errors = GenerateOODocument(modifications, filename="./test.ods", gauge=None)
        self.assertEquals(len(errors), 0)
        os.unlink("./test.ods")    


class PSUTests(GertrudeTestCase):
    def test_nombre_mois_facturation(self):
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2009, 9, 1)
        inscription.fin = datetime.date(2010, 8, 31)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        self.assertEquals(cotisation.nombre_factures, 8)


class NosPetitsPoucesTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PAJE
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))

    def test_exception_missing_formula(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscrit.inscriptions.append(inscription)
        self.assertRaises(CotisationException, Cotisation, inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 0.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)

    def test_august_without_invoice(self):
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 10.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        self.add_inscription_timeslot(inscription, 0, 96, 180)
        self.add_inscription_timeslot(inscription, 1, 96, 180)
        self.add_inscription_timeslot(inscription, 2, 96, 180)
        self.add_inscription_timeslot(inscription, 3, 96, 180)
        self.add_inscription_timeslot(inscription, 4, 96, 180)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 1654.55)
        facture = Facture(inscrit, 2010, 1, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 1654.55)
        facture = Facture(inscrit, 2010, 8, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 0.0)


class PAJETests(GertrudeTestCase):
    def test_pas_de_taux_horaire(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscrit.inscriptions.append(inscription)
        self.assertRaises(CotisationException, Cotisation, inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche,[["", 0.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        
    def test_nospetitspouces(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 6.70, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
        self.add_inscription_timeslot(inscription, 0, 96, 180)
        self.add_inscription_timeslot(inscription, 1, 96, 180)
        self.add_inscription_timeslot(inscription, 2, 96, 180)
        self.add_inscription_timeslot(inscription, 3, 96, 180)
        self.add_inscription_timeslot(inscription, 4, 96, 180)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 6), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 1001.95)
        facture = Facture(inscrit, 2010, 9, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 1001.95)

    def test_microcosmos(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 10, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut, inscription.fin = datetime.date(2014, 10, 15), datetime.date(2015, 12, 31)
        self.add_inscription_timeslot(inscription, 0, 96, 180)
        self.add_inscription_timeslot(inscription, 1, 96, 180)
        self.add_inscription_timeslot(inscription, 2, 96, 180)
        self.add_inscription_timeslot(inscription, 3, 96, 180)
        self.add_inscription_timeslot(inscription, 4, 96, 180)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 15), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 1516.67)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 831.72)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 1516.67)


class UnDeuxTroisAPetitsPas(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.conges_inscription = GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT
        database.creche.arrondi_mensualisation_euros = ARRONDI_EURO_PLUS_PROCHE
        database.creche.tarification_activites = 1
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 6.25, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        self.activity_repas = Activite(database.creche, mode=MODE_SANS_HORAIRES, formule_tarif="4.50")
        database.creche.add_activite(self.activity_repas)

    def test_123_apetitspas(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2014, 9, 22)
        self.add_inscription_timeslot(inscription, 0, 96, 204)
        self.add_inscription_timeslot(inscription, 1, 96, 204)
        self.add_inscription_timeslot(inscription, 2, 96, 204)
        self.add_inscription_timeslot(inscription, 3, 96, 204)
        self.add_inscription_timeslot(inscription, 4, 96, 204)
        inscription.semaines_conges = 7
        inscription.fin_periode_adaptation = datetime.date(2014, 10, 6)
        inscrit.inscriptions.append(inscription)
        self.add_journee_presence(inscrit, datetime.date(2014, 9, 22), 144, 204)
        self.add_journee_presence(inscrit, datetime.date(2014, 9, 23), 144, 204)
        self.add_journee_presence(inscrit, datetime.date(2014, 9, 24), 144, 204)
        self.add_journee_presence(inscrit, datetime.date(2014, 9, 25), 144, 204)
        self.add_journee_presence(inscrit, datetime.date(2014, 9, 26), 144, 204)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 0)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 7), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 1055.00)
        facture = Facture(inscrit, 2014, 9, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 269.00)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 1076.00)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 1055.00)

    def test_activites_pendant_conges(self):
        inscrit = self.add_inscrit()
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="01/01/2018", fin="05/01/2018"))
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.debut = datetime.date(2016, 8, 31)
        inscription.fin = datetime.date(2018, 12, 31)
        inscription.forfait_mensuel_heures = 150
        inscription.semaines_conges = 10
        self.add_inscription_timeslot(inscription, 0, 105, 216)
        self.add_inscription_timeslot(inscription, 1, 105, 216)
        self.add_inscription_timeslot(inscription, 2, 105, 216)
        self.add_inscription_timeslot(inscription, 3, 105, 216)
        self.add_inscription_timeslot(inscription, 4, 105, 216)
        self.add_inscription_timeslot(inscription, 0, None, None, self.activity_repas)
        self.add_inscription_timeslot(inscription, 1, None, None, self.activity_repas)
        self.add_inscription_timeslot(inscription, 2, None, None, self.activity_repas)
        self.add_inscription_timeslot(inscription, 3, None, None, self.activity_repas)
        self.add_inscription_timeslot(inscription, 4, None, None, self.activity_repas)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2018, 1, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.montant_heure_garde, 6.25)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 938.00)
        facture = Facture(inscrit, 2018, 1, NO_ADDRESS)
        self.assert_prec2_equals(facture.supplement_activites, 81.00)
        # TODO 1 centime d'écart sous Python 3 => self.assert_prec2_equals(facture.total, 1122.13)


class MarmousetsTests(GertrudeTestCase):
    def test_1(self):
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        database.creche.conges_inscription = 1
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
            self.add_ferie(label)
        conge = CongeStructure(creche=database.creche, debut="14/05/2010", fin="14/05/2010")
        database.creche.add_conge(conge)
        database.creche.baremes_caf.append(BaremeCAF(database.creche, debut=datetime.date(2010, 1, 1), plancher=6876.00, plafond=53400.00))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL, debut=datetime.date(2010, 1, 4), fin=datetime.date(2010, 7, 30))
        self.add_inscription_timeslot(inscription, 1, 102, 210)
        self.add_inscription_timeslot(inscription, 2, 102, 210)
        self.add_inscription_timeslot(inscription, 3, 102, 210)
        self.add_inscription_timeslot(inscription, 4, 102, 222)
        inscrit.inscriptions.append(inscription)
        conge = CongeInscrit(inscrit=inscrit, debut="01/02/2010", fin="20/02/2010")
        inscrit.add_conge(conge)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 4), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.heures_semaine, 37.0)
        self.assertEquals(cotisation.heures_periode, 971.0)
        self.assertEquals(cotisation.nombre_factures, 7)


class DessineMoiUnMoutonTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        database.creche.arrondi_heures = ARRONDI_HEURE
        database.creche.arrondi_facturation = ARRONDI_HEURE
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.add_ferie(label)
        self.add_conge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.add_conge("23/08/2010")
        self.add_conge("02/08/2010", "20/08/2010")
        self.add_conge("19/04/2010", "23/04/2010")
        self.add_conge("20/12/2010", "24/12/2010")
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        self.add_conge("06/04/2016")
        self.add_conge("26/12/2016", "02/01/2017")
        self.add_conge("29/07/2016", "22/08/2016")
        self.add_conge("18/04/2016", "23/04/2016")

    def test_24aout_31dec(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 8, 24)
        inscription.fin = datetime.date(2010, 12, 31)
        self.add_inscription_timeslot(inscription, 0, 102, 210)
        self.add_inscription_timeslot(inscription, 1, 102, 210)
        self.add_inscription_timeslot(inscription, 2, 102, 210)
        self.add_inscription_timeslot(inscription, 3, 102, 210)
        self.add_inscription_timeslot(inscription, 4, 102, 210)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 196.0)
        self.assertEquals(cotisation.nombre_factures, 4)

    def test_9sept_31dec(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 9, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        self.add_inscription_timeslot(inscription, 0, 102, 210)
        self.add_inscription_timeslot(inscription, 1, 102, 210)
        self.add_inscription_timeslot(inscription, 2, 102, 210)
        self.add_inscription_timeslot(inscription, 3, 102, 210)
        self.add_inscription_timeslot(inscription, 4, 102, 210)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 183.0)
        self.assertEquals(cotisation.nombre_factures, 4)

    def test_1janv_31dec(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        self.add_inscription_timeslot(inscription, 0, 102, 210)
        self.add_inscription_timeslot(inscription, 1, 102, 222)
        self.add_inscription_timeslot(inscription, 2, 102, 210)
        self.add_inscription_timeslot(inscription, 3, 102, 222)
        self.add_inscription_timeslot(inscription, 4, 102, 222)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 48.0)
        self.assertEquals(cotisation.heures_mois, 199.0)
        self.assertEquals(cotisation.nombre_factures, 11)
        facture = Facture(inscrit, 2010, 9)
        self.assert_prec2_equals(facture.total_contractualise, 248.75)
        self.assert_prec2_equals(facture.total_facture, 248.75)

    def test_heures_supp_sur_arrondi(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        self.add_inscription_timeslot(inscription, 2, 96, 150)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 5.0)
        self.add_journee_presence(inscrit, datetime.date(2010, 9, 8), 96, 204)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 4.0)

    def test_heures_supp_2_plages_horaires_sur_1_jour(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        self.add_inscription_timeslot(inscription, 2, 102, 222)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 10.0)
        self.add_journee_presence(inscrit, datetime.date(2010, 9, 8), 88, 94)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 1.0)

    def test_prorata_suite_a_naissance_enfant(self):
        database.creche.type = TYPE_ASSOCIATIF
        inscrit = self.add_inscrit()
        inscrit.naissance = datetime.date(2014, 12, 5)
        self.add_frere(inscrit, datetime.date(2016, 10, 21))
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2016, 1, 1)
        inscription.fin = datetime.date(2016, 12, 31)
        self.add_inscription_timeslot(inscription, 0, 90, 198)
        self.add_inscription_timeslot(inscription, 1, 90, 198)
        self.add_inscription_timeslot(inscription, 2, 96, 198)
        self.add_inscription_timeslot(inscription, 3, 90, 198)
        self.add_inscription_timeslot(inscription, 4, 90, 198)
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2016, 9)
        self.assertEquals(facture.total_contractualise, 277.5)
        self.assertEquals(facture.total_facture, 277.5)
        facture = Facture(inscrit, 2016, 11)
        self.assertEquals(facture.total_contractualise, 165.0)
        self.assertEquals(facture.total_facture, 165.0)
        facture = Facture(inscrit, 2016, 10)
        self.assertEquals(facture.total_contractualise, 245.36)
        self.assertEquals(facture.total_facture, 245.36)


class PetitsMoussesTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.add_ferie(label)
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        database.creche.baremes_caf.append(BaremeCAF(database.creche, debut=datetime.date(2013, 1, 1), plancher=6876.00, plafond=56665.32))

    def test_1janv_15fev(self):
        inscrit = self.add_inscrit()
        self.add_parents(inscrit, 57312.0)
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL,
                                  debut=datetime.date(2013, 1, 1), fin=datetime.date(2013, 2, 15),
                                  semaines_conges=5)
        self.add_inscription_timeslot(inscription, 0, 102, 222)
        self.add_inscription_timeslot(inscription, 3, 102, 222)
        self.add_inscription_timeslot(inscription, 4, 102, 222)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2013, 1, 1))
        self.assert_prec2_equals(cotisation.heures_semaine, 30.0)
        self.assert_prec2_equals(cotisation.heures_mois, 128.18)
        self.assertEquals(cotisation.nombre_factures, 11)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 302.51)
        facture = Facture(inscrit, 2013, 1, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 302.51)
        facture = Facture(inscrit, 2013, 2, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 166.38+43.64)


class LoupandisesTests(GertrudeTestCase):
    def test_facture_periode_adaptation(self):
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.add_ferie(label)
        self.add_conge("23/10/2010", "02/11/2010")
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 9, 6)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.fin_periode_adaptation = datetime.date(2010, 11, 30)
        self.add_inscription_timeslot(inscription, 1, 141, 201)
        self.add_inscription_timeslot(inscription, 3, 165, 201)
        inscrit.inscriptions.append(inscription)
        self.add_journee_presence(inscrit, datetime.date(2010, 11, 4), 120, 120)
        self.add_journee_presence(inscrit, datetime.date(2010, 11, 8), 120, 156)
        self.add_journee_presence(inscrit, datetime.date(2010, 11, 9), 105, 201)
        self.add_journee_presence(inscrit, datetime.date(2010, 11, 18), 120, 120)
        facture = Facture(inscrit, 2010, 11)
        self.assertEquals(round(facture.heures_facturees, 2), 29.0)
        self.assertEquals(round(facture.heures_contractualisees, 2), 29.0)
        self.assertEquals(round(facture.heures_supplementaires, 2), 6.0)
        self.assertEquals(round(facture.heures_realisees, 2), 29.0)
        self.assert_prec2_equals(facture.total, 36.25)


class FacturationDebutMoisContratTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_HORAIRES_REELS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.type = TYPE_MICRO_CRECHE
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["mode=hg", 9.5, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE], ["", 7.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))

    def test_forfait_mensuel(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, 90.0*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4.0+12*10.0-1.75-1.75) * 7.0)

    def test_temps_partiel(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0)
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - (1.75 * 2) * 7.0)

    def test_halte_garderie(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*9.5)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, 1292.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0)
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0 - (1.75 * 2) * 9.5)


class MonPetitBijouTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_HORAIRES_REELS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_PREVISIONNEL
        database.creche.type = TYPE_MICRO_CRECHE
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["mode=hg", 9.5, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE], ["", 7.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))

    def test_forfait_mensuel(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture()
        Facture(inscrit, 2011, 1).Cloture()
        Facture(inscrit, 2011, 2).Cloture()
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0)*7.0)
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15 => 1.75h en moins
        self.add_journee_presence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15 => 1.75h en moins
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-2*1.75) * 7.0)  # 1095.5
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 7), 90, 189)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 8), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-4*1.75) * 7.0)

    def test_temps_partiel(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture()
        Facture(inscrit, 2011, 1).Cloture()
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        facture.Cloture()
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, (5*4.0+14*10.0) * 7.0) # 1120.0
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 7), 90, 189) # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 8), 90, 189) # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - 2*1.75*7.0)

    def test_halte_garderie(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 141)  # 4h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*9.5)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture()
        Facture(inscrit, 2011, 1).Cloture()
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, 1292.0)
        facture.Cloture()
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0)
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 7), 90, 189)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2011, 3, 8), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0 - 2*1.75*9.5)

    def test_periode_adaptation(self):
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 60.0
        inscription.debut = datetime.date(2011, 4, 7)
        inscription.fin_periode_adaptation = datetime.date(2011, 9, 1)
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2011, 4)
        self.assertEquals(facture.total, 0)
        self.add_journee_presence(inscrit, datetime.date(2011, 4, 14), 90, 102) # 1h
        facture = Facture(inscrit, 2011, 4)
        self.assertEquals(facture.total, 7.00)
        self.assertEquals(facture.heures_facturees, 1.0)
        self.assertEquals(facture.heures_realisees, 1.0)


class VivreADomicileTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.type = TYPE_PARENTAL
        self.add_conge("01/08/2011", "26/08/2011")
        self.add_conge("03/06/2011", "03/06/2011")
        self.add_conge("Août", options=MOIS_SANS_FACTURE)

    def test_heures_supplementaires(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit, datetime.date(2002, 9, 13))
        self.add_frere(inscrit, datetime.date(2003, 9, 19))
        inscrit.famille.parents[0].revenus[0].revenu = 6960.0
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2011, 1, 3)
        inscription.fin = datetime.date(2011, 2, 28)
        inscription.fin_periode_adaptation = datetime.date(2011, 1, 5)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2011, 1, 3), NO_ADDRESS)
        self.assertEquals(cotisation.assiette_mensuelle, 580.00)
        self.assertEquals(cotisation.taux_effort, 0.03)
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 5), 102, 126)  # 8h30 periode d'adaptation
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 10), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 12), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 17), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 19), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 24), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 26), 102, 204)  # 8h30
        self.add_journee_presence(inscrit, datetime.date(2011, 1, 31), 102, 204)  # 8h30
        facture = Facture(inscrit, 2011, 1)
        self.assert_prec2_equals(facture.cotisation_mensuelle, 0.34)
        self.assert_prec2_equals(facture.supplement, 10.12)
        self.assert_prec2_equals(facture.heures_facturees, 61.5)
        # on dirait que les heures d'adaptation partent dans les heures supp, alors que le total part dans la cotisation
        self.assert_prec2_equals(facture.heures_supplementaires, 61.5)
        self.assert_prec2_equals(facture.total, 10.46)


class BebebulTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.type = TYPE_PARENTAL
        database.creche.add_activite(Activite(database.creche, mode=MODE_PRESENCE_NON_FACTUREE))

    def test_halte_garderie(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit, datetime.date(2009, 8, 11))
        self.add_frere(inscrit, datetime.date(2012, 8, 18))
        inscrit.famille.parents[0].revenus[0].revenu = 42966.0
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)  # lundi
        self.add_inscription_timeslot(inscription, 1, 102, 144)  # mardi = 3h30
        self.add_inscription_timeslot(inscription, 3, 102, 144)  # jeudi = 3h30
        inscrit.inscriptions.append(inscription)
        Cotisation(inscrit, datetime.date(2012, 10, 1), NO_ADDRESS)
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 2), 105, 138)  # mardi 2h45
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 4), 105, 141)  # jeudi 3h00 => 5h45
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 9), 105, 138)  # mardi 2h45 => 8h30
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 11), 105, 132)  # jeudi 2h15 => 10h45
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 16), 105, 144)  # mardi 3h15 => 14h
        self.add_activite(inscrit, datetime.date(2012, 10, 18), 102, 144, database.creche.states[VACANCES])  # jeudi conge
        self.add_activite(inscrit, datetime.date(2012, 10, 23), 105, 147, database.creche.states[ABSENCE_NON_PREVENUE])  # mardi 3h30 absence non prevenue
        self.add_activite(inscrit, datetime.date(2012, 10, 25), 105, 147, database.creche.activites[0])  # jeudi 3h30 permanence
        # mardi 30 => 3h30 (periode de reference)
        facture = Facture(inscrit, 2012, 10)
        self.assert_prec2_equals(facture.heures_contractualisees, 31.5)
        self.assert_prec2_equals(facture.heures_facturees, 21.0)
        self.assert_prec2_equals(facture.heures_realisees, 21.0)
        self.assert_prec2_equals(facture.heures_supplementaires, 0.0)
        self.assert_prec2_equals(facture.heures_contractualisees_realisees, 21.0)
        self.assert_prec2_equals(facture.heures_realisees_non_facturees, 3.5)
        self.assert_prec2_equals(facture.heures_facturees_non_realisees, 3.5)
        self.assert_prec2_equals(facture.total, 22.47)

    def test_adaptation_sur_presence_supplementaire(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit, datetime.date(2009, 8, 11))
        self.add_frere(inscrit, datetime.date(2012, 8, 18))
        inscrit.famille.parents[0].revenus[0].revenu = 42966.0
        inscription = inscrit.inscriptions[0]  # Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        self.add_journee_presence(inscrit, datetime.date(2012, 10, 25), 105, 147)  # 3h30
        self.add_activite(inscrit, datetime.date(2012, 10, 25), 105, 147, database.creche.activites[0])      # 3h30 adaptation
        facture = Facture(inscrit, 2012, 10)
        self.assert_prec2_equals(facture.heures_contractualisees, 0.0)
        self.assert_prec2_equals(facture.heures_realisees, 3.5)
        self.assert_prec2_equals(facture.heures_supplementaires, 3.5)
        self.assert_prec2_equals(facture.heures_realisees_non_facturees, 3.5)
        self.assert_prec2_equals(facture.heures_facturees, 0.0)
        self.assert_prec2_equals(facture.cotisation_mensuelle, 0.00)
        self.assert_prec2_equals(facture.supplement, 0.00)
        self.assert_prec2_equals(facture.deduction, 0.00)
        self.assert_prec2_equals(facture.total, 0.00)


class RibambelleTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.type = TYPE_PARENTAL
        database.creche.repartition = REPARTITION_SANS_MENSUALISATION
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.conges_inscription = GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT

    def test_normal(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 4, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 10, 1), NO_ADDRESS)
        self.assertEquals(cotisation.montant_heure_garde, 1.25)
        facture = Facture(inscrit, 2015, 10)
        self.assertEquals(facture.total, 275)

    def test_adaptation(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        inscription.fin_periode_adaptation = datetime.date(2015, 10, 3)
        self.add_journee_presence(inscrit, datetime.date(2015, 10, 1), 105, 117) # 1h00
        self.add_journee_presence(inscrit, datetime.date(2015, 10, 2), 93, 201) # 9h00
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 4, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2015, 10)
        self.assert_prec2_equals(facture.total, 275 - 10*1.25)

    def test_statistiques_conges_avec_supplement(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2016, 1, 1)
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="01/02/2016", fin="05/02/2016"))
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 4, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        statistiques = GetStatistiques(datetime.date(2016, 1, 1), datetime.date(2016, 12, 31))
        self.assert_prec2_equals(statistiques.heures_contrat, 2560.0)
        self.assert_prec2_equals(statistiques.heures_reel, 2560.0)
        self.assert_prec2_equals(statistiques.heures_facture, 2560.0)


class LaCabaneAuxFamillesTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.type = TYPE_MICRO_CRECHE
        database.creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.gestion_depart_anticipe = True
        database.creche.regularisation_fin_contrat = True

    def test_arrivee_et_depart_en_cours_de_mois(self):
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 7.5, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL)
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2015, 1, 15)
        inscription.fin_periode_adaptation = datetime.date(2015, 1, 19)
        inscription.fin = datetime.date(2016, 1, 14)
        self.add_inscription_timeslot(inscription, 0, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 1, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 2, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 3, 93, 213)  # 10h
        self.add_inscription_timeslot(inscription, 4, 93, 213)  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 15), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 20), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 1468.75)
        facture = Facture(inscrit, 2015, 1)
        self.assert_prec2_equals(facture.total, 568.55)
        facture = Facture(inscrit, 2016, 1)
        self.assert_prec2_equals(facture.total, 663.31)

    def test_regularisation_conges_non_pris(self):
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["revenus>0", 10.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 11, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        inscription.depart = datetime.date(2017, 3, 31)
        self.add_inscription_timeslot(inscription, 0, 111, 216)  # 10h
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2017, 4, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        self.add_inscription_timeslot(inscription, 0, 111, 216)
        self.add_inscription_timeslot(inscription, 3, 111, 216)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 1, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 342.71)
        cotisation = Cotisation(inscrit, datetime.date(2017, 4, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 685.42)
        facture = Facture(inscrit, 2017, 4)
        self.assert_prec2_equals(facture.total, 685.42 + 179.79)


class EleaTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_FAMILIAL
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.gestion_depart_anticipe = False
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.repartition = REPARTITION_SANS_MENSUALISATION
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        database.creche.conges_inscription = GESTION_CONGES_INSCRIPTION_NON_MENSUALISES
        self.add_conge("07/05/2018", "11/05/2018")
        self.add_conge("06/08/2018", "26/08/2018")
        self.add_conge("17/10/2018", "17/10/2018")
        self.add_conge("24/12/2018", "28/12/2018")
        self.add_conge("31/12/2018", "31/12/2018")

    def test_absences_prevenues(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit, )
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 0
        inscription.debut = datetime.date(2018, 1, 1)
        inscription.fin = datetime.date(2018, 12, 31)
        self.add_inscription_timeslot(inscription, 2, 110, 110+9*12)  # 9h
        inscrit.inscriptions.append(inscription)
        self.set_revenus(inscrit, 42783)
        cotisation = Cotisation(inscrit, datetime.date(2018, 1, 1), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 50.05)
        facture = Facture(inscrit, 2018, 1, NO_ADDRESS)
        self.assert_prec2_equals(facture.total, 45*1.43)
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="03/01/2018", fin="03/01/2018"))
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="03/01/2018", fin="03/01/2018"))
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="10/01/2018", fin="10/01/2018"))
        inscrit.add_conge(CongeInscrit(inscrit=inscrit, debut="31/01/2018", fin="31/01/2018"))
        facture = Facture(inscrit, 2018, 1, NO_ADDRESS | TRACES)
        self.assert_prec2_equals(facture.total, 18*1.43)


class PiousPiousTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_PARENTAL
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.gestion_depart_anticipe = True
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        self.add_conge("31/07/2017", "21/08/2017")

    def test_adaptation_a_cheval_sur_2_mois_dont_mois_sans_facture(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 0
        inscription.debut = datetime.date(2017, 7, 12)
        inscription.fin_periode_adaptation = datetime.date(2017, 8, 25)
        inscription.fin = datetime.date(2017, 8, 31)
        self.add_inscription_timeslot(inscription, 0, 102, 225)
        self.add_inscription_timeslot(inscription, 1, 102, 225)
        self.add_inscription_timeslot(inscription, 2, 102, 225)
        self.add_inscription_timeslot(inscription, 3, 102, 168)
        self.add_inscription_timeslot(inscription, 4, 102, 219)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 7, 12), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2017, 8, 26), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 92.00)
        self.add_journee_presence(inscrit, datetime.date(2017, 8, 22), 120, 168)  # 4h00
        self.add_journee_presence(inscrit, datetime.date(2017, 8, 23), 120, 174)  # 4h30
        self.add_journee_presence(inscrit, datetime.date(2017, 8, 24), 114, 177)  # 5h15
        self.add_journee_presence(inscrit, datetime.date(2017, 8, 25), 105, 216)  # 9h15
        facture = Facture(inscrit, 2017, 8)
        self.assert_prec2_equals(facture.total, 138.00)


class OPagaioTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_MICRO_CRECHE
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.gestion_depart_anticipe = True
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 9.5, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_GRATUITE
        self.add_conge("26/12/2016", "31/12/2016")
        self.add_conge("24/04/2017", "29/04/2017")

    def test_2_semaines_reference(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 26)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.duree_reference = 14
        for i in range(10):
            self.add_inscription_timeslot(inscription, i, 96, 216)  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 9, 26), NO_ADDRESS | NO_PARENTS)
        self.assertEquals(cotisation.heures_semaine, 50)

    def test_adaptation_a_cheval_sur_2_mois(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 26)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 2)
        inscription.fin = datetime.date(2017, 8, 31)
        self.add_inscription_timeslot(inscription, 0, 96, 216)  # 10h
        self.add_inscription_timeslot(inscription, 4, 96, 150)  # 4h30
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 9, 26), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 3), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 538.48)
        facture = Facture(inscrit, 2016, 9)
        self.assertEquals(facture.total, 0.0)
        facture = Facture(inscrit, 2016, 10)
        self.assert_prec2_equals(facture.total, 538.48)

    def test_changement_de_contrat(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 10
        inscription.debut = datetime.date(2016, 10, 3)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 3)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 2, 5)
        self.add_inscription_timeslot(inscription, 0, 102, 216)  # 9.5h
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 9.0
        inscription.debut = datetime.date(2017, 2, 6)
        inscription.fin = datetime.date(2017, 3, 10)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 4), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 311.77)
        cotisation = Cotisation(inscrit, datetime.date(2017, 2, 6), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 213.75)
        facture = Facture(inscrit, 2017, 2)
        self.assert_prec2_equals(facture.cotisation_mensuelle, 525.52)

    def test_regularisation_conges_non_pris_mode_forfait_hebdomadaire(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 32.0
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 12)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 4, 30)
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2017, 4)
        self.assert_prec2_equals(facture.regularisation, 188.19)

    def test_regularisation_conges_non_pris_mode_temps_partiel(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 7
        inscription.debut = datetime.date(2017, 3, 1)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 5, 31)
        self.add_inscription_timeslot(inscription, 0, 114, 210)  # 9.5h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2017, 5)
        self.assert_prec2_equals(facture.regularisation, 228.00)

    def test_exception_forfait_hebdomadaire(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 32.0
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 12)
        inscription.fin = datetime.date(2017, 8, 31)
        self.add_inscription_timeslot(inscription, 0, 96, 216)  # 10h
        self.add_inscription_timeslot(inscription, 4, 96, 150)  # 4h30
        inscrit.inscriptions.append(inscription)
        self.add_journee_presence(inscrit, datetime.date(2017, 4, 17), 120, 168)  # 4h00
        self.add_journee_presence(inscrit, datetime.date(2017, 4, 18), 120, 174)  # 4h30
        self.add_journee_presence(inscrit, datetime.date(2017, 4, 19), 120, 168)  # 4h00
        self.add_journee_presence(inscrit, datetime.date(2017, 4, 20), 120, 174)  # 4h30
        self.add_journee_presence(inscrit, datetime.date(2017, 4, 21), 120, 174)  # 4h30
        Facture(inscrit, 2017, 4)


class PitchounsTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_ASSOCIATIF
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.gestion_depart_anticipe = True
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.arrondi_heures = SANS_ARRONDI
        database.creche.arrondi_facturation = ARRONDI_DEMI_HEURE
        database.creche.arrondi_facturation_periode_adaptation = ARRONDI_DEMI_HEURE
        database.creche.arrondi_semaines = ARRONDI_SEMAINE_SUPERIEURE
        database.creche.arrondi_mensualisation = ARRONDI_HEURE_PLUS_PROCHE
        database.creche.conges_inscription = GESTION_CONGES_INSCRIPTION_MENSUALISES
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        self.add_conge("25/05/2017", "28/05/2017")
        self.add_conge("07/08/2017", "28/08/2017")
        self.add_conge("23/12/2017", "31/12/2017")

    def test_2_inscriptions_sur_mois_sans_facture(self):
        inscrit = self.add_inscrit()
        self.add_frere(inscrit)
        self.add_frere(inscrit)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2017, 4, 1)
        inscription.fin = datetime.date(2017, 8, 5)
        self.add_inscription_timeslot(inscription, 0, 102, 156)
        self.add_inscription_timeslot(inscription, 2, 102, 132)
        self.add_inscription_timeslot(inscription, 3, 102, 132)
        self.add_inscription_timeslot(inscription, 4, 102, 156)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 4, 1), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 133.0)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 1
        inscription.debut = datetime.date(2017, 8, 29)
        inscription.fin = datetime.date(2017, 12, 23)
        self.add_inscription_timeslot(inscription, 0, 102, 195)
        self.add_inscription_timeslot(inscription, 1, 102, 195)
        self.add_inscription_timeslot(inscription, 3, 102, 195)
        self.add_inscription_timeslot(inscription, 4, 102, 195)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 8, 29), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 248.0)
        facture = Facture(inscrit, 2017, 8)
        self.assert_prec2_equals(facture.total, 0.0)
        facture = Facture(inscrit, 2017, 9)
        self.assert_prec2_equals(facture.total, 248.00)

    def test_arrondi_halte_garderie(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2017, 9, 4)
        inscription.fin = datetime.date(2017, 12, 22)
        inscrit.inscriptions.append(inscription)
        for i in range(len(inscrit.famille.parents[0].revenus)):
            inscrit.famille.parents[0].revenus[i].revenu = 53516.0
            inscrit.famille.parents[1].revenus[i].revenu = 0.0
        cotisation = Cotisation(inscrit, datetime.date(2017, 9, 4), NO_ADDRESS)
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 0.0)
        self.assert_prec2_equals(cotisation.montant_heure_garde, 2.68)
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 4), 120, 228)  # 9h00
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 5), 120, 228)  # 9h00
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 6), 120, 225)  # 8h45
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 7), 120, 225)  # 8h45
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 11), 120, 228)  # 9h00
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 12), 120, 228)  # 9h00
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 13), 120, 225)  # 8h45
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 14), 120, 228)  # 9h00
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 18), 120, 219)  # 8h15
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 19), 120, 207)  # 7h15
        self.add_journee_presence(inscrit, datetime.date(2017, 12, 21), 120, 222)  # 8h30
        facture = Facture(inscrit, 2018, 1)
        self.assert_prec2_equals(facture.heures_supplementaires, 96.5)  # si pas d'arrondi, sans doute pas juste mais pas demandé
        self.assert_prec2_equals(facture.total, 255.27)  # si pas d'arrondi
        database.creche.nom = "Multi- accueils collectif LES PITCHOUN'S"
        facture = Facture(inscrit, 2018, 1)
        self.assert_prec2_equals(facture.heures_supplementaires, 96.5)  # avec arrondi, juste
        self.assert_prec2_equals(facture.total, 258.62)  # avec arrondi comme demandé (config en dur)


class MairieDeMoulonTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU_TAUX_PERSONNALISES
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.repartition = REPARTITION_SANS_MENSUALISATION
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_SEMAINES
        database.creche.arrondi_heures = SANS_ARRONDI
        database.creche.arrondi_facturation = SANS_ARRONDI
        database.creche.formule_taux_effort = [["", 100.0]]
        database.creche.UpdateFormuleTauxEffort(changed=False)
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
            self.add_ferie(label)

    def test_facture(self):
        inscrit = self.add_inscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2017, 1, 1)
        inscription.fin = datetime.date(2017, 12, 31)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 1, 1))
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 0.00)


class RenardeauxTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_PARENTAL
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        database.creche.conges_inscription = GESTION_CONGES_INSCRIPTION_NON_MENSUALISES
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.arrondi_heures = SANS_ARRONDI
        database.creche.arrondi_facturation = SANS_ARRONDI
        database.creche.arrondi_semaines = ARRONDI_SEMAINE_PLUS_PROCHE
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.add_ferie(label)
        self.add_conge("01/08/2018", "31/08/2018", options=MOIS_SANS_FACTURE)
        self.add_conge("23/07/2018", "20/08/2018")
        self.add_conge("11/05/2018", "11/05/2018")

    def test_adaptation(self):
        inscrit = self.add_inscrit()
        self.set_revenus(inscrit, 23924.00)
        inscription = inscrit.inscriptions[0]
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2018, 2, 21)
        inscription.fin_periode_adaptation = datetime.date(2018, 3, 1)
        inscription.fin = datetime.date(2018, 8, 31)
        inscription.frais_inscription = 25.00
        for day in (0, 1, 3, 4):
            self.add_inscription_timeslot(inscription, day, 8.5*12, 18*12)
        cotisation = Cotisation(inscrit, datetime.date(2018, 2, 21))
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 0.00)
        self.assert_prec2_equals(cotisation.montant_heure_garde, 1.00)
        cotisation = Cotisation(inscrit, datetime.date(2018, 3, 2))
        self.assert_prec2_equals(cotisation.cotisation_mensuelle, 156.00)
        self.assert_prec2_equals(cotisation.montant_heure_garde, 1.00)
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 21), 0, 0)  # 0h00
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 22), 100, 112)  # 1h00
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 23), 100, 124)  # 2h00
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 26), 100, 136)  # 3h00
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 27), 100, 160)  # 5h00
        self.add_journee_presence(inscrit, datetime.date(2018, 2, 28), 100, 184)  # 7h00
        facture = Facture(inscrit, 2018, 2)
        self.assert_prec2_equals(facture.total, 25.0)  # uniquement les frais d'inscription
        facture = Facture(inscrit, 2018, 3)
        self.assert_prec2_equals(facture.total, 156 + 18.0)  # la mensualisation + les heures d'adaptation de février


if __name__ == '__main__':
    unittest.main()
