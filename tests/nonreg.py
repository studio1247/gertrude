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

import unittest
import sys
import os
import __builtin__
sys.path.append("..")
import sqlinterface
from sqlobjects import *
from cotisation import *
from facture import Facture
from doc_planning_detaille import PlanningDetailleModifications
from doc_coordonnees_parents import CoordonneesModifications
from doc_releve_detaille import ReleveDetailleModifications
from doc_etats_trimestriels import EtatsTrimestrielsModifications
from ooffice import GenerateOODocument
from config import Config

__builtin__.config = Config()
config.first_date = datetime.date(2010, 1, 1)


class GertrudeTestCase(unittest.TestCase):
    def setUp(self):
        __builtin__.creche = Creche()
        creche.activites[0] = activite = Activite(creation=False)
        activite.value, activite.mode = 0, MODE_NORMAL
        
    def AddJourFerie(self, label):
        conge = Conge(creche, creation=False)
        conge.debut = label
        creche.AddConge(conge)
            
    def AddConge(self, debut, fin="", options=0):
        conge = Conge(creche, creation=False)
        conge.debut, conge.fin = debut, fin
        conge.options = options
        creche.AddConge(conge)
    
    def AddParents(self, inscrit, salaire=30000.0):
        inscrit.famille.parents[0] = papa = Parent(inscrit.famille, "papa", creation=False)
        revenu = Revenu(papa, creation=False)
        revenu.debut, revenu.fin, revenu.revenu = datetime.date(2008, 1, 1), datetime.date(2014, 12, 31), salaire
        papa.revenus.append(revenu)
        inscrit.famille.parents[1] = maman = Parent(inscrit.famille, "maman", creation=False)
        revenu = Revenu(maman, creation=False)
        revenu.debut, revenu.fin, revenu.revenu = datetime.date(2008, 1, 1), datetime.date(2014, 12, 31), 0.0
        maman.revenus.append(revenu)
        for year in range(2015, 2020):
            revenu = Revenu(papa, creation=False)
            revenu.debut, revenu.fin, revenu.revenu = datetime.date(year, 1, 1), datetime.date(year, 12, 31), salaire
            papa.revenus.append(revenu)
            revenu = Revenu(maman, creation=False)
            revenu.debut, revenu.fin, revenu.revenu = datetime.date(year, 1, 1), datetime.date(year, 12, 31), salaire
            maman.revenus.append(revenu)

    def AddInscrit(self):
        inscrit = Inscrit(creation=False)
        inscrit.famille = Famille(creation=False)
        inscrit.prenom, inscrit.nom = 'Gertrude', 'GPL'
        inscrit.naissance = datetime.date(2010, 1, 1)
        inscrit.idx = 0
        self.AddParents(inscrit)
        creche.inscrits.append(inscrit)
        return inscrit
    
    def AddSalarie(self):
        salarie = Salarie(creation=False)
        salarie.prenom, salarie.nom = 'Gertrude', 'GPL'
        salarie.idx = 0
        creche.salaries.append(salarie)
        return salarie    
    
    def AddActivite(self, inscrit, date, debut, fin, activite):
        inscrit.journees[date] = Journee(inscrit, date)
        inscrit.journees[date].AddActivity(debut, fin, activite, None)
        
    def AddJourneePresence(self, inscrit, date, debut, fin):
        self.AddActivite(inscrit, date, debut, fin, 0)
        
    def AddFrere(self, inscrit, naissance):
        result = Frere_Soeur(inscrit, creation=False)
        result.prenom = "Frere ou Soeur"
        result.nom = "GPL"
        result.naissance = naissance
        inscrit.famille.freres_soeurs.append(result)
        return result

    def assertPrec2Equals(self, montant1, montant2):
        self.assertEquals("%.2f" % montant1, "%.2f" % montant2)


class DatabaseTests(unittest.TestCase):
    def test_creation(self):
        filename = "gertrude.db"
        if os.path.isfile(filename):
            os.remove(filename)
        con = sqlinterface.SQLConnection(filename)
        con.Create()


class PlanningTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.activites[1] = activite = Activite(creation=False)
        activite.value, activite.mode = 1, MODE_LIBERE_PLACE
        creche.activites[2] = activite = Activite(creation=False)
        activite.value, activite.mode = 2, MODE_NORMAL
    
    def test_ski(self):
        day = Day()
        day.SetActivity(0, 10, 0)
        day.SetActivity(2, 8, 1)
        self.assertEquals(len(day.activites), 3)
    
    def test_repas(self):
        day = Day()
        day.SetActivity(0, 10, 0)
        day.SetActivity(2, 8, 2)
        self.assertEquals(len(day.activites), 2)
        
    def test_previsionnel_cloture(self):
        day = Day()
        day.InsertActivity(0, 10, PREVISIONNEL|CLOTURE)
        day.SetActivity(2, 8, 0)
        self.assertEquals(len(day.activites), 2)


class DocumentsTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        self.pwd = os.getcwd()
        os.chdir("..")
        creche.mode_facturation = FACTURATION_PAJE
        creche.formule_taux_horaire = [["", 6.70]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        for i in range(10):
            inscrit = self.AddInscrit()
            inscription = Inscription(inscrit, creation=False)
            inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
            inscription.mode = MODE_5_5
            inscription.reference[0].AddActivity(96, 180, 0, -1)
            inscription.reference[1].AddActivity(96, 180, 0, -1)
            inscription.reference[2].AddActivity(96, 180, 0, -1)
            inscription.reference[3].AddActivity(96, 180, 0, -1)
            inscription.reference[4].AddActivity(96, 180, 0, -1)
            inscrit.inscriptions.append(inscription)
            
            salarie = self.AddSalarie()
            contrat = Contrat(salarie, creation=False)
            contrat.debut, contrat.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
            contrat.reference[0].AddActivity(96, 180, 0, -1)
            contrat.reference[1].AddActivity(96, 180, 0, -1)
            contrat.reference[2].AddActivity(96, 180, 0, -1)
            contrat.reference[3].AddActivity(96, 180, 0, -1)
            contrat.reference[4].AddActivity(96, 180, 0, -1)
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
        creche.mode_facturation = FACTURATION_PSU
        creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2009, 9, 1)
        inscription.fin = datetime.date(2010, 8, 31)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        self.assertEquals(cotisation.nombre_factures, 8)


class PAJETests(GertrudeTestCase):
    def test_pas_de_taux_horaire(self):
        creche.mode_facturation = FACTURATION_PAJE
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscrit.inscriptions.append(inscription)
        self.assertRaises(CotisationException, Cotisation, inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        creche.formule_taux_horaire = [["", 0.0]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        
    def test_nospetitspouces(self):
        creche.mode_facturation = FACTURATION_PAJE
        creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        creche.formule_taux_horaire = [["", 6.70]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
        inscription.reference[0].AddActivity(96, 180, 0, -1)
        inscription.reference[1].AddActivity(96, 180, 0, -1)
        inscription.reference[2].AddActivity(96, 180, 0, -1)
        inscription.reference[3].AddActivity(96, 180, 0, -1)
        inscription.reference[4].AddActivity(96, 180, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 6), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1001.95)
        facture = Facture(inscrit, 2010, 9, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 1001.95)
        
    def test_microcosmos(self):
        creche.mode_facturation = FACTURATION_PAJE
        creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        creche.formule_taux_horaire = [["", 10]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut, inscription.fin = datetime.date(2014, 10, 15), datetime.date(2015, 12, 31)
        inscription.reference[0].AddActivity(96, 180, 0, -1)
        inscription.reference[1].AddActivity(96, 180, 0, -1)
        inscription.reference[2].AddActivity(96, 180, 0, -1)
        inscription.reference[3].AddActivity(96, 180, 0, -1)
        inscription.reference[4].AddActivity(96, 180, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 15), NO_ADDRESS|NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1516.67)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 831.72)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 1516.67)
        
    def test_123_apetitspas(self):
        creche.mode_facturation = FACTURATION_PAJE
        creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.formule_taux_horaire = [["", 6.25]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2014, 9, 22)
        inscription.reference[0].AddActivity(96, 204, 0, -1)
        inscription.reference[1].AddActivity(96, 204, 0, -1)
        inscription.reference[2].AddActivity(96, 204, 0, -1)
        inscription.reference[3].AddActivity(96, 204, 0, -1)
        inscription.reference[4].AddActivity(96, 204, 0, -1)
        inscription.semaines_conges = 7
        inscription.fin_periode_adaptation = datetime.date(2014, 10, 6)
        inscrit.inscriptions.append(inscription)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 22), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 23), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 24), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 25), 144, 204)
        self.AddJourneePresence(inscrit, datetime.date(2014, 9, 26), 144, 204)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 1), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 0)
        cotisation = Cotisation(inscrit, datetime.date(2014, 10, 7), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1054.69)
        facture = Facture(inscrit, 2014, 9, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 268.75)
        facture = Facture(inscrit, 2014, 10, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 1075.55)
        facture = Facture(inscrit, 2014, 11, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 1054.69)


class MarmousetsTests(GertrudeTestCase):
    def test_1(self):
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        creche.conges_inscription = 1
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
            self.AddJourFerie(label)
        conge = Conge(creche, creation=False)
        conge.debut = conge.fin = "14/05/2010"
        creche.AddConge(conge)
        bareme = BaremeCAF(creation=False)
        bareme.debut, bareme.plancher, bareme.plafond = datetime.date(2010, 1, 1), 6876.00, 53400.00
        creche.baremes_caf.append(bareme)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 4)
        inscription.fin = datetime.date(2010, 7, 30)
        inscription.reference[1].AddActivity(102, 210, 0, -1)
        inscription.reference[2].AddActivity(102, 210, 0, -1)
        inscription.reference[3].AddActivity(102, 210, 0, -1)
        inscription.reference[4].AddActivity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        conge = CongeInscrit(inscrit, creation=False)
        conge.debut, conge.fin = "01/02/2010", "20/02/2010"
        inscrit.AddConge(conge)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 4), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.heures_semaine, 37.0)
        self.assertEquals(cotisation.heures_periode, 971.0)
        self.assertEquals(cotisation.nombre_factures, 7)


class DessineMoiUnMoutonTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        creche.arrondi_heures = ARRONDI_HEURE
        creche.arrondi_facturation = ARRONDI_HEURE
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.AddConge("23/08/2010")
        self.AddConge("02/08/2010", "20/08/2010")
        self.AddConge("19/04/2010", "23/04/2010")
        self.AddConge("20/12/2010", "24/12/2010")
        self.AddConge("Août", options=MOIS_SANS_FACTURE)
        self.AddConge("06/04/2016")
        self.AddConge("26/12/2016", "02/01/2017")
        self.AddConge("29/07/2016", "22/08/2016")
        self.AddConge("18/04/2016", "23/04/2016")

    def test_24aout_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 8, 24)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].AddActivity(102, 210, 0, -1)
        inscription.reference[1].AddActivity(102, 210, 0, -1)
        inscription.reference[2].AddActivity(102, 210, 0, -1)
        inscription.reference[3].AddActivity(102, 210, 0, -1)
        inscription.reference[4].AddActivity(102, 210, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 196.0)
        self.assertEquals(cotisation.nombre_factures, 4)
        
    def test_9sept_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 9, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].AddActivity(102, 210, 0, -1)
        inscription.reference[1].AddActivity(102, 210, 0, -1)
        inscription.reference[2].AddActivity(102, 210, 0, -1)
        inscription.reference[3].AddActivity(102, 210, 0, -1)
        inscription.reference[4].AddActivity(102, 210, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 45.0)
        self.assertEquals(cotisation.heures_mois, 183.0)
        self.assertEquals(cotisation.nombre_factures, 4)
    
    def test_1janv_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].AddActivity(102, 210, 0, -1)
        inscription.reference[1].AddActivity(102, 222, 0, -1)
        inscription.reference[2].AddActivity(102, 210, 0, -1)
        inscription.reference[3].AddActivity(102, 222, 0, -1)
        inscription.reference[4].AddActivity(102, 222, 0, -1)
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
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[2].AddActivity(96, 150, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 5.0)
        self.AddJourneePresence(inscrit, datetime.date(2010, 9, 8), 96, 204)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 4.0)

    def test_heures_supp_2_plages_horaires_sur_1_jour(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[2].AddActivity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        # self.assertPrec2Equals(cotisation.heures_semaine, 5.0)
        self.AddJourneePresence(inscrit, datetime.date(2010, 9, 8), 88, 94)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 1.0)

    def test_prorata_suite_a_naissance_enfant(self):
        creche.type = TYPE_ASSOCIATIF
        inscrit = self.AddInscrit()
        inscrit.naissance = datetime.date(2014, 12, 5)
        self.AddFrere(inscrit, datetime.date(2016, 10, 21))
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2016, 1, 1)
        inscription.fin = datetime.date(2016, 12, 31)
        inscription.reference[0].AddActivity(90, 198, 0, -1)
        inscription.reference[1].AddActivity(90, 198, 0, -1)
        inscription.reference[2].AddActivity(96, 198, 0, -1)
        inscription.reference[3].AddActivity(90, 198, 0, -1)
        inscription.reference[4].AddActivity(90, 198, 0, -1)
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
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("Août", options=MOIS_SANS_FACTURE)
        bareme = BaremeCAF(creation=False)
        bareme.debut, bareme.plancher, bareme.plafond = datetime.date(2013, 1, 1), 6876.00, 56665.32
        creche.baremes_caf.append(bareme)
        
    def test_1janv_15fev(self):
        inscrit = self.AddInscrit()
        self.AddParents(inscrit, 57312.0)
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2013, 1, 1)
        inscription.fin = datetime.date(2013, 2, 15)
        inscription.semaines_conges = 5
        inscription.reference[0].AddActivity(102, 222, 0, -1)
        inscription.reference[3].AddActivity(102, 222, 0, -1)
        inscription.reference[4].AddActivity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2013, 1, 1))
        self.assertPrec2Equals(cotisation.heures_semaine, 30.0)
        self.assertPrec2Equals(cotisation.heures_mois, 128.18)
        self.assertEquals(cotisation.nombre_factures, 11)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 302.51)
        facture = Facture(inscrit, 2013, 1, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 302.51)
        facture = Facture(inscrit, 2013, 2, NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(facture.total, 166.38+43.64)
        

class LoupandisesTests(GertrudeTestCase):
    def test_facture_periode_adaptation(self):
        creche.mode_facturation = FACTURATION_PSU
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = ABSENCES_DEDUITES_EN_JOURS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", "Lundi de Pâques", "Jeudi de l'Ascension", "Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("23/10/2010", "02/11/2010")
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 9, 6)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.fin_periode_adaptation = datetime.date(2010, 11, 30)
        inscription.reference[1].AddActivity(141, 201, 0, -1)
        inscription.reference[3].AddActivity(165, 201, 0, -1)
        inscrit.inscriptions.append(inscription)
        inscrit.journees[datetime.date(2010, 11, 4)] = Journee(inscrit, datetime.date(2010, 11, 4))       
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 8), 120, 156)
        self.AddJourneePresence(inscrit, datetime.date(2010, 11, 9), 105, 201)
        inscrit.journees[datetime.date(2010, 11, 18)] = Journee(inscrit, datetime.date(2010, 11, 18))
        facture = Facture(inscrit, 2010, 11)
        self.assertEquals(round(facture.heures_facturees, 2), 29.0)
        self.assertEquals(round(facture.heures_contractualisees, 2), 29.0)
        self.assertEquals(round(facture.heures_supplementaires, 2), 6.0)
        self.assertEquals(round(facture.heures_realisees, 2), 29.0)
        self.assertPrec2Equals(facture.total, 36.25)


class FacturationDebutMoisContratTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_HORAIRES_REELS
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        creche.type = TYPE_MICRO_CRECHE
        creche.formule_taux_horaire = [["mode=hg", 9.50], ["", 7.0]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        
    def test_forfait_mensuel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1) # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, 90.0*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (4*4.0+12*10.0-1.75-1.75) * 7.0)
    
    def test_temps_partiel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1) # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
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
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1)  # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1)  # 10h
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
        creche.mode_facturation = FACTURATION_HORAIRES_REELS
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_PREVISIONNEL
        creche.type = TYPE_MICRO_CRECHE
        creche.formule_taux_horaire = [["mode=hg", 9.50], ["", 7.0]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        __builtin__.sql_connection = None
        
    def test_forfait_mensuel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_MENSUEL
        inscription.forfait_mensuel_heures = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1) # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture(None)
        Facture(inscrit, 2011, 1).Cloture(None)
        Facture(inscrit, 2011, 2).Cloture(None)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0)*7.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-2*1.75) * 7.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.cotisation_mensuelle, 90.0*7.0)
        self.assertEquals(facture.total, (5*4.0+14*10.0-4*1.75) * 7.0)
    
    def test_temps_partiel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1) # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture(None)
        Facture(inscrit, 2011, 1).Cloture(None)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        facture.Cloture(None)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, (5*4.0+14*10.0) * 7.0) # 1120.0
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - 2*1.75*7.0)
    
    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 141, 0, -1) # 4h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*9.5)
        for m in range(3, 13):
            Facture(inscrit, 2010, m).Cloture(None)
        Facture(inscrit, 2011, 1).Cloture(None)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, 1292.0)
        facture.Cloture(None)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 7), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 3, 8), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0 - 2*1.75*9.5)
        
    def test_periode_adaptation(self):
        creche.temps_facturation = FACTURATION_FIN_MOIS
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
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
        creche.mode_facturation = FACTURATION_PSU
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.type = TYPE_PARENTAL
        self.AddConge("01/08/2011", "26/08/2011")
        self.AddConge("03/06/2011", "03/06/2011")
        self.AddConge("Août", options=MOIS_SANS_FACTURE)
        
    def test_heures_supplementaires(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2002, 9, 13))
        self.AddFrere(inscrit, datetime.date(2003, 9, 19))
        inscrit.famille.parents[0].revenus[0].revenu = 6960.0
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2011, 1, 3)
        inscription.fin = datetime.date(2011, 2, 28)
        inscription.fin_periode_adaptation = datetime.date(2011, 1, 5)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2011, 1, 3), NO_ADDRESS | NO_PARENTS)
        self.assertEquals(cotisation.assiette_mensuelle, 580.00)
        self.assertEquals(cotisation.taux_effort, 0.03)        
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 10), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 17), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 24), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 31), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 5), 102, 126)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 12), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 19), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 26), 102, 204)  # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 26), 102, 204)  # 8h30
        facture = Facture(inscrit, 2011, 1)
        self.assertPrec2Equals(facture.total, 10.46)


class BebebulTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.type = TYPE_PARENTAL
        creche.activites[1] = activite = Activite(creation=False)
        activite.value, activite.mode = 1, MODE_PRESENCE_NON_FACTUREE
        
    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2009, 8, 11))
        self.AddFrere(inscrit, datetime.date(2012, 8, 18))
        inscrit.famille.parents[0].revenus[0].revenu = 42966.0
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        inscription.reference[1].AddActivity(102, 144, 0, -1)  # 3h30
        inscription.reference[3].AddActivity(102, 144, 0, -1)  # 3h30
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2012, 10, 1), NO_ADDRESS | NO_PARENTS)
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
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        inscrit.inscriptions.append(inscription)
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 25), 105, 147) # 3h00
        self.AddActivite(inscrit, datetime.date(2012, 10, 25), 105, 147, 1)    # 3h00 adaptation
        facture = Facture(inscrit, 2012, 10)
        self.assertPrec2Equals(facture.total, 0.00)


class RibambelleTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.type = TYPE_PARENTAL
        creche.repartition = REPARTITION_SANS_MENSUALISATION
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
    
    def test_normal(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[4].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 10, 1), NO_ADDRESS|NO_PARENTS)
        self.assertEquals(cotisation.montant_heure_garde, 1.25)
        facture = Facture(inscrit, 2015, 10)
        self.assertEquals(facture.total, 275)
        
    def test_adaptation(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.debut = datetime.date(2015, 10, 1)
        inscription.fin_periode_adaptation = datetime.date(2015, 10, 3)
        self.AddJourneePresence(inscrit, datetime.date(2015, 10, 1), 105, 117) # 1h00
        self.AddJourneePresence(inscrit, datetime.date(2015, 10, 2), 93, 201) # 9h00
        inscription.reference[0].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[2].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[3].AddActivity(93, 213, 0, -1) # 10h
        inscription.reference[4].AddActivity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2015, 10)
        self.assertPrec2Equals(facture.total, 275 - 10*1.25)


class LaCabaneAuxFamillesTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PAJE
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        creche.type = TYPE_MICRO_CRECHE
        creche.repartition = REPARTITION_MENSUALISATION_12MOIS
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_HORAIRES_REELS
        creche.gestion_depart_anticipe = True
        creche.regularisation_fin_contrat = True

    def test_arrivee_et_depart_en_cours_de_mois(self):
        creche.formule_taux_horaire = [["", 7.5]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2015, 1, 15)
        inscription.fin_periode_adaptation = datetime.date(2015, 1, 19)
        inscription.fin = datetime.date(2016, 1, 14)
        inscription.reference[0].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[1].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[2].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[3].AddActivity(93, 213, 0, -1)  # 10h
        inscription.reference[4].AddActivity(93, 213, 0, -1)  # 10h
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 15), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2015, 1, 20), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 1468.75)
        facture = Facture(inscrit, 2015, 1)
        self.assertPrec2Equals(facture.total, 568.55)
        facture = Facture(inscrit, 2016, 1)
        self.assertPrec2Equals(facture.total, 663.31)

    def test_regularisation_conges_non_pris(self):
        creche.formule_taux_horaire = [["revenus>0", 10.0]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 11, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        inscription.depart = datetime.date(2017, 3, 31)
        inscription.reference[0].AddActivity(111, 216, 0, -1)
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2017, 4, 1)
        inscription.fin = datetime.date(2017, 8, 25)
        inscription.reference[0].AddActivity(111, 216, 0, -1)
        inscription.reference[3].AddActivity(111, 216, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2017, 1, 1), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 342.71)
        cotisation = Cotisation(inscrit, datetime.date(2017, 4, 1), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 685.42)
        facture = Facture(inscrit, 2017, 4)
        self.assertPrec2Equals(facture.total, 685.42 + 179.79)


class OPagaioTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.type = TYPE_MICRO_CRECHE
        creche.mode_facturation = FACTURATION_PAJE
        creche.gestion_depart_anticipe = True
        creche.formule_taux_horaire = [["", 9.5]]
        creche.UpdateFormuleTauxHoraire(changed=False)
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.repartition = REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS
        creche.facturation_periode_adaptation = PERIODE_ADAPTATION_GRATUITE
        self.AddConge("26/12/2016", "31/12/2016")
        self.AddConge("24/04/2017", "29/04/2017")

    def test_adaptation_a_cheval_sur_2_mois(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 5
        inscription.debut = datetime.date(2016, 9, 26)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 2)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.reference[0].AddActivity(96, 216, 0, -1)  # 10h
        inscription.reference[4].AddActivity(96, 150, 0, -1)  # 4h30
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 9, 26), NO_ADDRESS | NO_PARENTS)
        self.assertEquals(cotisation.cotisation_mensuelle, 0.0)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 3), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 538.48)
        facture = Facture(inscrit, 2016, 9)
        self.assertEquals(facture.total, 0.0)
        facture = Facture(inscrit, 2016, 10)
        self.assertPrec2Equals(facture.total, 538.48)

    def test_changement_de_contrat(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 10
        inscription.debut = datetime.date(2016, 10, 3)
        inscription.fin_periode_adaptation = datetime.date(2016, 10, 3)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 2, 5)
        inscription.reference[0].AddActivity(102, 216, 0, -1)  # 9.5h
        inscrit.inscriptions.append(inscription)
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_HEBDOMADAIRE
        inscription.forfait_mensuel_heures = 9.0
        inscription.debut = datetime.date(2017, 2, 6)
        inscription.fin = datetime.date(2017, 3, 10)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2016, 10, 4), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 311.77)
        cotisation = Cotisation(inscrit, datetime.date(2017, 2, 6), NO_ADDRESS | NO_PARENTS)
        self.assertPrec2Equals(cotisation.cotisation_mensuelle, 213.75)
        facture = Facture(inscrit, 2017, 2)
        self.assertPrec2Equals(facture.cotisation_mensuelle, 525.52)

    def test_regularisation_conges_non_pris_mode_forfait_hebdomadaire(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
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
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_TEMPS_PARTIEL
        inscription.semaines_conges = 7
        inscription.debut = datetime.date(2017, 3, 1)
        inscription.fin = datetime.date(2017, 8, 31)
        inscription.depart = datetime.date(2017, 5, 31)
        inscription.reference[0].AddActivity(114, 210, 0, -1)  # 9.5h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2017, 5)
        self.assertPrec2Equals(facture.regularisation, 152.00)


if __name__ == '__main__':
    unittest.main()
