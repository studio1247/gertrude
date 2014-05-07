# -*- coding: utf-8 -*-

import sys, os, __builtin__
sys.path.append("..")
import unittest
import sqlinterface
from sqlobjects import *
from cotisation import *
from facture import Facture
from planning_detaille import PlanningDetailleModifications
from coordonnees_parents import CoordonneesModifications
from ooffice import GenerateOODocument

__builtin__.first_date = datetime.date(2010, 1, 1) 

class GertrudeTestCase(unittest.TestCase):
    def setUp(self):
        __builtin__.creche = Creche()
        creche.activites[0] = activite = Activite(creation=False)
        activite.value, activite.mode = 0, MODE_NORMAL
        
    def AddJourFerie(self, label):
        conge = Conge(creche, creation=False)
        conge.debut = label
        creche.add_conge(conge)
            
    def AddConge(self, debut, fin="", options=0):
        conge = Conge(creche, creation=False)
        conge.debut, conge.fin = debut, fin
        conge.options = options
        creche.add_conge(conge)
    
    def AddParents(self, inscrit, salaire=30000.0):
        inscrit.parents["papa"] = papa = Parent(inscrit, creation=False)
        revenu = Revenu(papa, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), salaire
        papa.revenus.append(revenu)
        inscrit.parents["maman"] = maman = Parent(inscrit, creation=False)
        revenu = Revenu(maman, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), 0.0
        maman.revenus.append(revenu)
        
    def AddInscrit(self):
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'Gertrude', 'GPL'
        self.AddParents(inscrit)
        creche.inscrits.append(inscrit)
        return inscrit
    
    def AddActivite(self, inscrit, date, debut, fin, activite):
        inscrit.journees[date] = Journee(inscrit, date)
        inscrit.journees[date].add_activity(debut, fin, activite, None)
        
    def AddJourneePresence(self, inscrit, date, debut, fin):
        self.AddActivite(inscrit, date, debut, fin, 0)
        
    def AddFrere(self, inscrit, naissance):
        result = Frere_Soeur(inscrit, creation=False)
        result.prenom = "Frere ou Soeur"
        result.nom = "GPL"
        result.naissance = naissance
        inscrit.freres_soeurs.append(result)
        return result
        
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
        day.insert_activity(0, 10, PREVISIONNEL|CLOTURE)
        day.SetActivity(2, 8, 0)
        self.assertEquals(len(day.activites), 2)

class DocumentsTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        self.pwd = os.getcwd()
        os.chdir("..")
        creche.mode_facturation = FACTURATION_PAJE
        creche.formule_taux_horaire = [["", 6.70]]
        creche.update_formule_taux_horaire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        for i in range(10):
            inscrit = self.AddInscrit()
            inscription = Inscription(inscrit, creation=False)
            inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
            inscription.reference[0].add_activity(96, 180, 0, -1)
            inscription.reference[1].add_activity(96, 180, 0, -1)
            inscription.reference[2].add_activity(96, 180, 0, -1)
            inscription.reference[3].add_activity(96, 180, 0, -1)
            inscription.reference[4].add_activity(96, 180, 0, -1)
            inscrit.inscriptions.append(inscription)
    
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
        creche.update_formule_taux_horaire(changed=False)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        
    def test_nospetitspouces(self):
        creche.mode_facturation = FACTURATION_PAJE
        creche.formule_taux_horaire = [["", 6.70]]
        creche.update_formule_taux_horaire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut, inscription.fin = datetime.date(2010, 9, 6), datetime.date(2011, 7, 27)
        inscription.reference[0].add_activity(96, 180, 0, -1)
        inscription.reference[1].add_activity(96, 180, 0, -1)
        inscription.reference[2].add_activity(96, 180, 0, -1)
        inscription.reference[3].add_activity(96, 180, 0, -1)
        inscription.reference[4].add_activity(96, 180, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 6), NO_ADDRESS|NO_PARENTS)
        self.assertEquals(float("%.2f" % cotisation.cotisation_mensuelle), 1001.95)
        facture = Facture(inscrit, 2010, 9, NO_ADDRESS|NO_PARENTS)
        self.assertEquals(float("%.2f" % facture.total), 1001.95)

class MarmousetsTests(GertrudeTestCase):
    def test_1(self):
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        creche.conges_inscription = 1
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", u"15 août", "1er novembre", "11 novembre", u"25 décembre", u"Lundi de Pâques", "Jeudi de l'Ascension"):
            self.AddJourFerie(label)
        conge = Conge(creche, creation=False)
        conge.debut = conge.fin = "14/05/2010"
        creche.add_conge(conge)
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
        inscription.reference[1].add_activity(102, 210, 0, -1)
        inscription.reference[2].add_activity(102, 210, 0, -1)
        inscription.reference[3].add_activity(102, 210, 0, -1)
        inscription.reference[4].add_activity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        conge = CongeInscrit(inscrit, creation=False)
        conge.debut, conge.fin = "01/02/2010", "20/02/2010"
        inscrit.add_conge(conge)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 4), NO_ADDRESS|NO_PARENTS)
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 37.0)
        self.assertEquals(cotisation.heures_periode, 971.0)
        self.assertEquals(cotisation.nombre_factures, 7)
                
class DessineMoiUnMoutonTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = JOURS_FERIES_DEDUITS_ANNUELLEMENT
        creche.arrondi_heures = ARRONDI_HEURE
        creche.arrondi_facturation = ARRONDI_HEURE
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.AddConge("23/08/2010")
        self.AddConge("02/08/2010", "20/08/2010")
        self.AddConge("19/04/2010", "23/04/2010")
        self.AddConge("20/12/2010", "24/12/2010")
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)
        
    def test_24aout_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 8, 24)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].add_activity(102, 210, 0, -1)
        inscription.reference[1].add_activity(102, 210, 0, -1)
        inscription.reference[2].add_activity(102, 210, 0, -1)
        inscription.reference[3].add_activity(102, 210, 0, -1)
        inscription.reference[4].add_activity(102, 210, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 45.0)
        self.assertEquals(cotisation.heures_mois, 196.0)
        self.assertEquals(cotisation.nombre_factures, 4)
        
    def test_9sept_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 9, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].add_activity(102, 210, 0, -1)
        inscription.reference[1].add_activity(102, 210, 0, -1)
        inscription.reference[2].add_activity(102, 210, 0, -1)
        inscription.reference[3].add_activity(102, 210, 0, -1)
        inscription.reference[4].add_activity(102, 210, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 45.0)
        self.assertEquals(cotisation.heures_mois, 183.0)
        self.assertEquals(cotisation.nombre_factures, 4)
    
    def test_1janv_31dec(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[0].add_activity(102, 210, 0, -1)
        inscription.reference[1].add_activity(102, 222, 0, -1)
        inscription.reference[2].add_activity(102, 210, 0, -1)
        inscription.reference[3].add_activity(102, 222, 0, -1)
        inscription.reference[4].add_activity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 48.0)
        self.assertEquals(cotisation.heures_mois, 199.0)
        self.assertEquals(cotisation.nombre_factures, 11)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.total_contractualise, 248.75)
        self.assertEquals(facture.total_facture, 248.75)

    def test_heures_supp_sur_arrondi(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.reference[2].add_activity(96, 150, 0, -1)
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
        inscription.reference[2].add_activity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2010, 9, 1))
        # self.assertEquals(float("%.2f" % cotisation.heures_semaine), 5.0)
        self.AddJourneePresence(inscrit, datetime.date(2010, 9, 8), 88, 94)
        facture = Facture(inscrit, 2010, 9)
        self.assertEquals(facture.heures_supplementaires, 1.0)

class PetitsMoussesTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)
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
        inscription.reference[0].add_activity(102, 222, 0, -1)
        inscription.reference[3].add_activity(102, 222, 0, -1)
        inscription.reference[4].add_activity(102, 222, 0, -1)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2013, 1, 1))
        self.assertEquals(float("%.2f" % cotisation.heures_semaine), 30.0)
        self.assertEquals(float("%.2f" % cotisation.heures_mois), 128.18)
        self.assertEquals(cotisation.nombre_factures, 11)
        self.assertEquals(float("%.2f" % cotisation.cotisation_mensuelle), 302.51)
        facture = Facture(inscrit, 2013, 1, NO_ADDRESS|NO_PARENTS)
        self.assertEquals(float("%.2f" % facture.total), 302.51)
        facture = Facture(inscrit, 2013, 2, NO_ADDRESS|NO_PARENTS)
        self.assertEquals(float("%.2f" % facture.total), 166.38)
        

class LoupandisesTests(GertrudeTestCase):
    def test_facture_periode_adaptation(self):
        creche.mode_facturation = FACTURATION_PSU
        creche.facturation_periode_adaptation = FACTURATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = JOURS_FERIES_DEDUITS_ANNUELLEMENT 
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("23/10/2010", "02/11/2010")
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 9, 6)
        inscription.fin = datetime.date(2010, 12, 31)
        inscription.fin_periode_adaptation = datetime.date(2010, 11, 30)
        inscription.reference[1].add_activity(141, 201, 0, -1)
        inscription.reference[3].add_activity(165, 201, 0, -1)
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
        self.assertEquals(facture.total, 36.25)

class FacturationDebutMoisContratTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_HORAIRES_REELS
        creche.facturation_periode_adaptation = FACTURATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_CONTRAT
        creche.type = TYPE_MICRO_CRECHE
        creche.formule_taux_horaire = [["mode=hg", 9.50], ["", 7.0]]
        creche.update_formule_taux_horaire(changed=False)
        
    def test_forfait_mensuel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_HORAIRE
        inscription.forfait_heures_presence = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
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
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*7.0)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, (4*4+12*10)*7.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1120.0 - (1.75 * 2) * 7.0)
    
    def test_halte_garderie(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
        inscrit.inscriptions.append(inscription)
        facture = Facture(inscrit, 2010, 3)
        self.assertEquals(facture.total, (5*4+14*10)*9.5)
        facture = Facture(inscrit, 2011, 2)
        self.assertEquals(facture.total, 1292.0)
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0)
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 14), 90, 189) # 8h15 
        self.AddJourneePresence(inscrit, datetime.date(2011, 2, 15), 90, 189) # 8h15 
        facture = Facture(inscrit, 2011, 3)
        self.assertEquals(facture.total, 1520.0 - (1.75 * 2) * 9.5)

  
class MonPetitBijouTests(GertrudeTestCase):
    def setUp(self):
        GertrudeTestCase.setUp(self)
        creche.mode_facturation = FACTURATION_HORAIRES_REELS
        creche.facturation_periode_adaptation = FACTURATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_DEBUT_MOIS_PREVISIONNEL
        creche.type = TYPE_MICRO_CRECHE
        creche.formule_taux_horaire = [["mode=hg", 9.50], ["", 7.0]]
        creche.update_formule_taux_horaire(changed=False)
        __builtin__.sql_connection = None
        
    def test_forfait_mensuel(self):
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_HORAIRE
        inscription.forfait_heures_presence = 90.0
        inscription.debut = datetime.date(2010, 3, 1)
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
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
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
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
        inscription.reference[0].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[1].add_activity(93, 213, 0, -1) # 10h
        inscription.reference[2].add_activity(93, 141, 0, -1) # 4h
        inscription.reference[3].add_activity(93, 213, 0, -1) # 10h
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
        facture = Facture(inscrit, 2011, 3, options=TRACES)
        self.assertEquals(facture.total, 1520.0 - 2*1.75*9.5)
        
    def test_periode_adaptation(self):
        creche.temps_facturation = FACTURATION_FIN_MOIS
        inscrit = self.AddInscrit()
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_FORFAIT_HORAIRE
        inscription.forfait_heures_presence = 60.0
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
        creche.facturation_periode_adaptation = FACTURATION_HORAIRES_REELS
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.type = TYPE_PARENTAL
        self.AddConge("01/08/2011", "26/08/2011")
        self.AddConge("03/06/2011", "03/06/2011")
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)       
        
    def test_heures_supplementaires(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2002, 9, 13))
        self.AddFrere(inscrit, datetime.date(2003, 9, 19))
        inscrit.parents["papa"].revenus[0].revenu = 6960.0
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2011, 1, 3)
        inscription.fin = datetime.date(2011, 2, 28)
        inscription.fin_periode_adaptation = datetime.date(2011, 1, 5)
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2011, 1, 3), NO_ADDRESS|NO_PARENTS)
        self.assertEquals(cotisation.assiette_mensuelle, 580.00)
        self.assertEquals(cotisation.taux_effort, 0.03)        
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 10), 102, 204) # 8h30 
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 17), 102, 204) # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 24), 102, 204) # 8h30 
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 31), 102, 204) # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 5), 102, 126) # 8h30 
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 12), 102, 204) # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 19), 102, 204) # 8h30 
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 26), 102, 204) # 8h30
        self.AddJourneePresence(inscrit, datetime.date(2011, 1, 26), 102, 204) # 8h30
        facture = Facture(inscrit, 2011, 1)
        self.assertEquals("%.2f" % facture.total, "10.46")

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
        inscrit.parents["papa"].revenus[0].revenu = 42966.0
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        inscription.reference[1].add_activity(102, 144, 0, -1) # 3h30
        inscription.reference[3].add_activity(102, 144, 0, -1) # 3h30
        inscrit.inscriptions.append(inscription)
        cotisation = Cotisation(inscrit, datetime.date(2012, 10, 1), NO_ADDRESS|NO_PARENTS)
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 2), 105, 138) # 2h45
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 4), 105, 141) # 3h00
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 9), 105, 138) # 2h45
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 11), 105, 132) # 2h15
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 16), 105, 144) # 3h15
        self.AddActivite(inscrit, datetime.date(2012, 10, 18), 102, 144, -1) # conge
        self.AddActivite(inscrit, datetime.date(2012, 10, 23), 105, 147, ABSENCE_NON_PREVENUE) # 3h30 absence non prevenue 
        self.AddActivite(inscrit, datetime.date(2012, 10, 25), 105, 147, 1) # 3h30 permanence
        facture = Facture(inscrit, 2012, 10)
        self.assertEquals("%.2f" % facture.total, "18.73")

    def test_adaptation_sur_presence_supplementaire(self):
        inscrit = self.AddInscrit()
        self.AddFrere(inscrit, datetime.date(2009, 8, 11))
        self.AddFrere(inscrit, datetime.date(2012, 8, 18))
        inscrit.parents["papa"].revenus[0].revenu = 42966.0
        inscription = Inscription(inscrit, creation=False)
        inscription.mode = MODE_HALTE_GARDERIE
        inscription.debut = datetime.date(2012, 10, 1)
        inscrit.inscriptions.append(inscription)
        self.AddJourneePresence(inscrit, datetime.date(2012, 10, 25), 105, 147) # 3h00
        self.AddActivite(inscrit, datetime.date(2012, 10, 25), 105, 147, 1)    # 3h00 adaptation
        facture = Facture(inscrit, 2012, 10)
        self.assertEquals("%.2f" % facture.total, "0.00")

if __name__ == '__main__':
    unittest.main()
