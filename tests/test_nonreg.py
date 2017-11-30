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


class GertrudeTestCase(unittest.TestCase):
    def setUp(self):
        database.init(":memory:")
        database.create(False)
        database.load()
        database.creche.activites[0] = Activite(creche=database.creche, value=0, mode=MODE_NORMAL)

    def add_ferie(self, label):
        database.creche.add_ferie(CongeStructure(creche=database.creche, debut=label))

    def add_conge(self, debut, fin="", options=0):
        database.creche.add_conge(CongeStructure(creche=database.creche, debut=debut, fin=fin, options=options))

    def AddParents(self, inscrit, salaire=30000.0):
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

    def AddInscrit(self):
        inscrit = Inscrit(creche=database.creche)
        inscrit.prenom, inscrit.nom = 'Gertrude', 'GPL'
        inscrit.naissance = datetime.date(2010, 1, 1)
        self.AddParents(inscrit)
        database.creche.inscrits.append(inscrit)
        return inscrit
    
    def AddSalarie(self):
        salarie = Salarie(creche=database.creche)
        salarie.prenom, salarie.nom = 'Gertrude', 'GPL'
        database.creche.salaries.append(salarie)
        return salarie    
    
    def AddActivite(self, inscrit, date, debut, fin, activite):
        inscrit.days.add(TimeslotInscrit(date=date, debut=debut, fin=fin, value=activite))
        
    def AddJourneePresence(self, inscrit, date, debut, fin):
        self.AddActivite(inscrit, date, debut, fin, 0)
        
    def AddFrere(self, inscrit, naissance=datetime.date(2000, 1, 1)):
        result = Fratrie(famille=inscrit.famille, prenom="Frere ou Soeur", naissance=naissance)
        inscrit.famille.freres_soeurs.append(result)
        return result

    def assertPrec2Equals(self, montant1, montant2):
        self.assertEquals("%.2f" % montant1, "%.2f" % montant2)


@pytest.mark.skipif("sys.version_info >= (3, 0)")
class PlanningTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.activites[1] = Activite(database.creche, value=1, mode=MODE_LIBERE_PLACE)
        database.creche.activites[2] = Activite(database.creche, value=2, mode=MODE_NORMAL)

    def test_ski(self):
        from planning import BasePlanningLine
        day = BasePlanningLine()
        day.set_activity(0, 10, 0)
        day.set_activity(2, 8, 1)
        self.assertEquals(len(day.timeslots), 3)
    
    def test_repas(self):
        from planning import BasePlanningLine
        day = BasePlanningLine()
        day.set_activity(0, 10, 0)
        day.set_activity(2, 8, 2)
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
            inscrit = self.AddInscrit()
            inscription = Inscription(inscrit=inscrit)
            inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
            inscription.mode = MODE_TEMPS_PLEIN
            inscription.days.add(TimeslotInscription(day=0, debut=96, fin=180, value=0))
            inscription.days.add(TimeslotInscription(day=1, debut=96, fin=180, value=0))
            inscription.days.add(TimeslotInscription(day=2, debut=96, fin=180, value=0))
            inscription.days.add(TimeslotInscription(day=3, debut=96, fin=180, value=0))
            inscription.days.add(TimeslotInscription(day=4, debut=96, fin=180, value=0))
            inscrit.inscriptions.append(inscription)
            
            salarie = self.AddSalarie()
            contrat = ContratSalarie(salarie=salarie, debut=datetime.date(2010, 9, 6), fin=datetime.date(2011, 7, 27))
            planning = PlanningSalarie(contrat=contrat, debut=contrat.debut)
            contrat.plannings.append(planning)
            planning.days.add(TimeslotPlanningSalarie(day=0, debut=96, fin=180, value=0))
            planning.days.add(TimeslotPlanningSalarie(day=1, debut=96, fin=180, value=0))
            planning.days.add(TimeslotPlanningSalarie(day=2, debut=96, fin=180, value=0))
            planning.days.add(TimeslotPlanningSalarie(day=3, debut=96, fin=180, value=0))
            planning.days.add(TimeslotPlanningSalarie(day=4, debut=96, fin=180, value=0))
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
        inscrit = self.AddInscrit()
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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscrit.inscriptions.append(inscription)
        self.assertRaises(CotisationException, Cotisation, inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 0.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)

    def test_august_without_invoice(self):
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 10.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=96, fin=180, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1654.55)
        facture = Facture(inscrit, 2010, 1, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 1654.55)
        facture = Facture(inscrit, 2010, 8, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 0.0)


class PAJETests(GertrudeTestCase):
    def test_pas_de_taux_horaire(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.AddInscrit()
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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
        inscription.days.add(TimeslotInscription(day=0, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=96, fin=180, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 6), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1001.95)
        facture = Facture(inscrit, 2010, 9, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 1001.95)

    def test_microcosmos(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 10, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut, inscription.fin = datetime.date(2014, 10, 15), datetime.date(2015, 12, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=96, fin=180, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=96, fin=180, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 15), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1516.67)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 831.72)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 1516.67)

    def test_123_apetitspas(self):
        database.creche.mode_facturation = FACTURATION_PAJE
        database.creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["", 6.25, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        database.creche.bureaux.append(Bureau(debut=datetime.date(2010, 1, 1)))
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2014, 9, 22)
        inscription.days.add(TimeslotInscription(day=0, debut=96, fin=204, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=96, fin=204, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=204, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=96, fin=204, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=96, fin=204, value=0))
        inscription.semaines_conges = 7
        inscription.fin_periode_adaptation = datetime.date(2014, 10, 6)
        inscrit.inscriptions.append(inscription)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 22), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 23), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 24), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 25), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 26), 144, 204)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 1), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 0)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 7), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1054.69)
        facture = Facture(inscrit, 2014, 9, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 268.75)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 1075.55)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 1054.69)


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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL, debut=datetime.date(2010, 1, 4), fin=datetime.date(2010, 7, 30))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=222, value=0))
        inscrit.inscriptions.append(inscription)
        conge = CongeInscrit(inscrit=inscrit, debut="01/02/2010", fin="20/02/2010")
        inscrit.add_conge(conge)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 4), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.heures_semaine, 37.0)
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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 8, 24)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=210, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 196.0)
        self.assertEquals(cotisation.nombre_factures, 4)

    def test_9sept_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 9, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=210, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 183.0)
        self.assertEquals(cotisation.nombre_factures, 4)

    def test_1janv_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=222, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=210, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=222, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=222, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 48.0)
        self.assertEquals(cotisation.heures_mois, 199.0)
        self.assertEquals(cotisation.nombre_factures, 11)
        facture = Facture(inscrit, 2010, 9)
        self.assertPrec2Equals(facture.total_contractualise, 248.75)
        self.assertPrec2Equals(facture.total_facture, 248.75)

    def test_heures_supp_sur_arrondi(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=150, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 5.0)
        self.AddJourneePresence(inscrit, datetime.date(2010, 9, 8), 96, 204)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 4.0)

    def test_heures_supp_2_plages_horaires_sur_1_jour(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=222, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 10.0)
        self.AddJourneePresence(inscrit, datetime.date(2010, 9, 8), 88, 94)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 1.0)

    def test_prorata_suite_a_naissance_enfant(self):
        database.creche.type = TYPE_ASSOCIATIF
        inscrit = self.AddInscrit()
        inscrit.naissance = datetime.date(2014, 12, 5)
        self.AddFrere(inscrit, datetime.date(2016, 10, 21))
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2016, 1, 1)
        inscription.fin = datetime.date(2016, 12, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=90, fin=198, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=90, fin=198, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=96, fin=198, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=90, fin=198, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=90, fin=198, value=0))
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
        inscrit = self.AddInscrit()
        self.AddParents(inscrit, 57312.0)
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL,
                                  debut=datetime.date(2013, 1, 1), fin=datetime.date(2013, 2, 15),
                                  semaines_conges=5)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=222, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=222, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=222, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2013, 1, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 30.0)
        self.assertPrec2Equals(cotisation.heures_mois, 128.18)
        self.assertEquals(cotisation.nombre_factures, 11)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 302.51)
        facture = Facture(inscrit, 2013, 1, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 302.51)
        facture = Facture(inscrit, 2013, 2, NO_ADDRESS)
        self.assertPrec2Equals(facture.total, 166.38+43.64)


class LoupandisesTests(GertrudeTestCase):
    def test_facture_periode_adaptation(self):
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.add_ferie(label)
        self.add_conge("23/10/2010", "02/11/2010")
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.debut = datetime.date(2010, 9, 6)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.fin_periode_adaptation = datetime.date(2010, 11, 30)
        inscription.days.add(TimeslotInscription(day=1, debut=141, fin=201, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=165, fin=201, value=0))
        inscrit.inscriptions.append(inscription)
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 4), 120, 120)
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 8), 120, 156)
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 9), 105, 201)
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 18), 120, 120)
        facture = Facture(inscrit, 2010, 11)
        self.assertEquals(round(facture.heures_facturees, 2), 29.0)
        self.assertEquals(round(facture.heures_contractualisees, 2), 29.0)
        self.assertEquals(round(facture.heures_supplementaires, 2), 6.0)
        self.assertEquals(round(facture.heures_realisees, 2), 29.0)
        self.assertPrec2Equals(facture.total, 36.25)


class FacturationDebutMoisContratTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_HORAIRES_REELS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.type = TYPE_MICRO_CRECHE
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["mode=hg", 9.5, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE], ["", 7.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))

    def test_forfait_mensuel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, 90.0*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4.0+12*10.0-1.75-1.75) * 7.0)

    def test_temps_partiel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - (1.75 * 2) * 7.0)

    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*9.5)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, 1292.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15
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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
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
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189)  # 8h15 => 1.75h en moins
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189)  # 8h15 => 1.75h en moins
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-2*1.75) * 7.0)  # 1095.5
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189)  # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-4*1.75) * 7.0)

    def test_temps_partiel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
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
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189) # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189) # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - 2*1.75*7.0)

    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=141, value=0))  # 4h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
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
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189)  # 8h15
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189)  # 8h15
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0 - 2*1.75*9.5)

    def test_periode_adaptation(self):
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 60.0
        inscription.debut = datetime.date(2011, 4, 7)
        inscription.fin_periode_adaptation = datetime.date(2011, 9, 1)
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2011, 4)
        self.assertEquals(facture.total, 0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 4, 14), 90, 102) # 1h
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
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2002, 9, 13))
        self.AddFrere(inscrit, datetime.date(2003, 9, 19))
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
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 5), 102, 126)  # 8h30 periode d'adaptation
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 10), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 12), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 17), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 19), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 24), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 26), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 31), 102, 204)  # 8h30
        facture = Facture(inscrit, 2011, 1)
        self.assertPrec2Equals(facture.cotisation_mensuelle, 0.34)
        self.assertPrec2Equals(facture.supplement, 10.12)
        self.assertPrec2Equals(facture.heures_facturees, 61.5)
        # on dirait que les heures d'adaptation partent dans les heures supp, alors que le total part dans la cotisation
        self.assertPrec2Equals(facture.heures_supplementaires, 61.5)
        self.assertPrec2Equals(facture.total, 10.46)


class BebebulTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.temps_facturation = FACTURATION_FIN_MOIS
        database.creche.type = TYPE_PARENTAL
        database.creche.activites[1] = Activite(database.creche, value=1, mode=MODE_PRESENCE_NON_FACTUREE)

    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2009, 8, 11))
        self.AddFrere(inscrit, datetime.date(2012, 8, 18))
        inscrit.famille.parents[0].revenus[0].revenu = 42966.0
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=144, value=0))  # 3h30
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=144, value=0))  # 3h30
        inscrit.inscriptions.append(inscription)
        Cotisation(inscrit, datetime.date(2012, 10, 1), NO_ADDRESS)
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 2), 105, 138)  # 2h45
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 4), 105, 141)  # 3h00
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 9), 105, 138)  # 2h45
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 11), 105, 132)  # 2h15
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 16), 105, 144)  # 3h15
        self.AddActivite(inscrit, datetime.date(2012, 10, 18), 102, 144, -1)  # conge
        self.AddActivite(inscrit, datetime.date(2012, 10, 23), 105, 147, ABSENCE_NON_PREVENUE)  # 3h30 absence non prevenue
        self.AddActivite(inscrit, datetime.date(2012, 10, 25), 105, 147, 1)  # 3h30 permanence
        facture = Facture(inscrit, 2012, 10)
        self.assertPrec2Equals(facture.total, 18.73)

    def test_adaptation_sur_presence_supplementaire(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2009, 8, 11))
        self.AddFrere(inscrit, datetime.date(2012, 8, 18))
        inscrit.famille.parents[0].revenus[0].revenu = 42966.0
        inscription = inscrit.inscriptions[0]  # Inscription(inscrit=inscrit)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 25), 105, 147)  # 3h00
        self.AddActivite(inscrit, datetime.date(2012, 10, 25), 105, 147, 1)      # 3h00 adaptation
        facture = Facture(inscrit, 2012, 10)
        self.assertPrec2Equals(facture.heures_contractualisees, 0.0)
        self.assertPrec2Equals(facture.heures_realisees, 3.5)
        self.assertPrec2Equals(facture.heures_supplementaires, 3.5)
        self.assertPrec2Equals(facture.heures_realisees_non_facturees, 3.5)
        self.assertPrec2Equals(facture.heures_facturees, 0.0)
        self.assertPrec2Equals(facture.cotisation_mensuelle, 0.00)
        self.assertPrec2Equals(facture.supplement, 0.00)
        self.assertPrec2Equals(facture.deduction, 0.00)
        self.assertPrec2Equals(facture.total, 0.00)


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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=4, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 10, 1), NO_ADDRESS)
        self.assertEquals(cotisation.montant_heure_garde, 1.25)
        facture = Facture(inscrit, 2015, 10)
        self.assertEquals(facture.total, 275)

    def test_adaptation(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        inscription.fin_periode_adaptation = datetime.date(2015, 10, 3)
        self.AddJourneePresence(inscrit, datetime.date(2015, 10, 1), 105, 117) # 1h00
        self.AddJourneePresence(inscrit, datetime.date(2015, 10, 2), 93, 201) # 9h00
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=4, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2015, 10)
        self.assertPrec2Equals(facture.total, 275 - 10*1.25)

    def test_statistiques_conges_avec_supplement(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2016, 1, 1)
        conge = CongeInscrit(inscrit=inscrit, debut="01/02/2016", fin="05/02/2016")
        inscrit.add_conge(conge)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=4, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        statistiques = GetStatistiques(datetime.date(2016, 1, 1), datetime.date(2016, 12, 31))
        self.assertPrec2Equals(statistiques.heures_contrat, 2560.0)
        self.assertPrec2Equals(statistiques.heures_reel, 2560.0)
        self.assertPrec2Equals(statistiques.heures_facture, 2560.0)


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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit, mode=MODE_TEMPS_PARTIEL)
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2015, 1, 15)
        inscription.fin_periode_adaptation = datetime.date(2015, 1, 19)
        inscription.fin = datetime.date(2016, 1, 14)
        inscription.days.add(TimeslotInscription(day=0, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=1, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=2, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=3, debut=93, fin=213, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=4, debut=93, fin=213, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 15), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 20), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1468.75)
        facture = Facture(inscrit, 2015, 1)
        self.assertPrec2Equals(facture.total, 568.55)
        facture = Facture(inscrit, 2016, 1)
        self.assertPrec2Equals(facture.total, 663.31)

    def test_regularisation_conges_non_pris(self):
        database.creche.tarifs_horaires.append(TarifHoraire(database.creche, [["revenus>0", 10.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE]]))
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 11, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        inscription.depart = datetime.date(2017, 3, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=111, fin=216, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2017, 4, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        inscription.days.add(TimeslotInscription(day=0, debut=111, fin=216, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=111, fin=216, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 1, 1), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 342.71)
        cotisation = Cotisation(inscrit, datetime.date(2017, 4, 1), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 685.42)
        facture = Facture(inscrit, 2017, 4)
        self.assertPrec2Equals(facture.total, 685.42 + 179.79)


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
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 0
        inscription.debut = datetime.date(2017, 7, 12)
        inscription.fin_periode_adaptation = datetime.date(2017, 8, 25)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=225, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=225, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=225, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=168, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=219, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 7, 12), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2017, 8, 26), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 92.00)
        self.AddJourneePresence(inscrit, datetime.date(2017, 8, 22), 120, 168)  # 4h00
        self.AddJourneePresence(inscrit, datetime.date(2017, 8, 23), 120, 174)  # 4h30
        self.AddJourneePresence(inscrit, datetime.date(2017, 8, 24), 114, 177)  # 5h15
        self.AddJourneePresence(inscrit, datetime.date(2017, 8, 25), 105, 216)  # 9h15
        facture = Facture(inscrit, 2017, 8)
        self.assertPrec2Equals(facture.total, 138.00)


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
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 26)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.duree_reference = 14
        for i in range(10):
            inscription.days.add(TimeslotInscription(day=i, debut=96, fin=216, value=0))  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 9, 26), NO_ADDRESS | NO_PARENTS)
        self.assertEquals(cotisation.heures_semaine, 50)

    def test_adaptation_a_cheval_sur_2_mois(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 26)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 2)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=96, fin=216, value=0))  # 10h
        inscription.days.add(TimeslotInscription(day=4, debut=96, fin=150, value=0))  # 4h30
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 9, 26), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 3), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 538.48)
        facture = Facture(inscrit, 2016, 9)
        self.assertEquals(facture.total, 0.0)
        facture = Facture(inscrit, 2016, 10)
        self.assertPrec2Equals(facture.total, 538.48)

    def test_changement_de_contrat(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 10
        inscription.debut = datetime.date(2016, 10, 3)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 3)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 2, 5)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=216, value=0))  # 9.5h
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 9.0
        inscription.debut = datetime.date(2017, 2, 6)
        inscription.fin = datetime.date(2017, 3, 10)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 4), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 311.77)
        cotisation = Cotisation(inscrit, datetime.date(2017, 2, 6), NO_ADDRESS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 213.75)
        facture = Facture(inscrit, 2017, 2)
        self.assertPrec2Equals(facture.cotisation_mensuelle, 525.52)

    def test_regularisation_conges_non_pris_mode_forfait_hebdomadaire(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 32.0
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 12)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 4, 30)
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2017, 4)
        self.assertPrec2Equals(facture.regularisation, 188.19)

    def test_regularisation_conges_non_pris_mode_temps_partiel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 7
        inscription.debut = datetime.date(2017, 3, 1)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 5, 31)
        inscription.days.add(TimeslotInscription(day=0, debut=114, fin=210, value=0))  # 9.5h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2017, 5)
        self.assertPrec2Equals(facture.regularisation, 228.00)


class PitchounsTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        database.creche.type = TYPE_ASSOCIATIF
        database.creche.mode_facturation = FACTURATION_PSU
        database.creche.gestion_depart_anticipe = True
        database.creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        database.creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        database.creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        database.creche.arrondi_semaines = ARRONDI_SEMAINE_SUPERIEURE
        self.add_conge("Août", options=MOIS_SANS_FACTURE)
        self.add_conge("25/05/2017", "28/05/2017")
        self.add_conge("07/08/2017", "28/08/2017")
        self.add_conge("23/12/2017", "31/12/2017")

    def test_2_inscriptions_sur_mois_sans_facture(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit)
        self.AddFrere(inscrit)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2017, 4, 1)
        inscription.fin = datetime.date(2017, 8, 5)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=156, value=0))
        inscription.days.add(TimeslotInscription(day=2, debut=102, fin=132, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=132, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=156, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 4, 1), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 133.0)
        inscription = Inscription(inscrit=inscrit)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 1
        inscription.debut = datetime.date(2017, 8, 29)
        inscription.fin = datetime.date(2017, 12, 23)
        inscription.days.add(TimeslotInscription(day=0, debut=102, fin=195, value=0))
        inscription.days.add(TimeslotInscription(day=1, debut=102, fin=195, value=0))
        inscription.days.add(TimeslotInscription(day=3, debut=102, fin=195, value=0))
        inscription.days.add(TimeslotInscription(day=4, debut=102, fin=195, value=0))
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 8, 29), NO_ADDRESS)
        self.assertEquals(cotisation.cotisation_mensuelle, 248.0)
        facture = Facture(inscrit, 2017, 8)
        self.assertPrec2Equals(facture.total, 0.0)
        facture = Facture(inscrit, 2017, 9)
        self.assertPrec2Equals(facture.total, 248.00)


if __name__ == '__main__':
    unittest.main()
