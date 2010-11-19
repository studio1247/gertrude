# -*- coding: utf-8 -*-

import sys, os, __builtin__
sys.path.append("..")
import unittest
import sqlinterface
from sqlobjects import *
from cotisation import *
from facture import Facture

class GertrudeTests(unittest.TestCase):
    def test_creation_bdd(self):
        filename = "gertrude.db"
        if os.path.isfile(filename):
            os.remove(filename)
        con = sqlinterface.SQLConnection(filename)
        con.Create()

class PAJETests(unittest.TestCase):
    def test_pas_de_taux_horaire(self):
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PAJE
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        inscrit.papa = Parent(inscrit, creation=False)
        inscrit.maman = Parent(inscrit, creation=False)
        inscription = Inscription(inscrit, creation=False)
        inscription.debut = datetime.date(2010, 1, 1)
        inscrit.inscriptions.append(inscription)
        self.assertRaises(CotisationException, Cotisation, inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        creche.formule_taux_horaire = [["", 0.0]]
        creche.update_formule_taux_horaire(changed=False)
        cotisation = Cotisation(inscrit, datetime.date(2010, 1, 1), NO_ADDRESS|NO_PARENTS)
        
    def test_nospetitspouces(self):
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PAJE
        creche.formule_taux_horaire = [["", 6.70]]
        creche.update_formule_taux_horaire(changed=False)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        inscrit.papa = Parent(inscrit, creation=False)
        inscrit.maman = Parent(inscrit, creation=False)
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

class MarmousetsTests(unittest.TestCase):
    def test_1(self):
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_DEBUT_MOIS
        creche.conges_inscription = 1
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", u"15 août", "1er novembre", "11 novembre", u"25 décembre", u"Lundi de Pâques", "Jeudi de l'Ascension"):
            conge = Conge(creche, creation=False)
            conge.debut = label
            creche.add_conge(conge)
        conge = Conge(creche, creation=False)
        conge.debut = conge.fin = "14/05/2010"
        creche.add_conge(conge)
        bareme = BaremeCAF(creation=False)
        bareme.debut, bareme.plancher, bareme.plafond = datetime.date(2010, 1, 1), 6876.00, 53400.00
        creche.baremes_caf.append(bareme)
        bureau = Bureau(creation=False)
        bureau.debut = datetime.date(2010, 1, 1)
        creche.bureaux.append(bureau)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        inscrit.papa = Parent(inscrit, creation=False)
        revenu = Revenu(inscrit.papa, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), 30000.0
        inscrit.papa.revenus.append(revenu)
        inscrit.maman = Parent(inscrit, creation=False)
        revenu = Revenu(inscrit.maman, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), 0.0
        inscrit.maman.revenus.append(revenu)
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
        self.assertEquals(cotisation.heures_annee, 971.0)
        self.assertEquals(cotisation.nombre_factures, 7)

class GertrudeTestCase(unittest.TestCase):
    def AddJourFerie(self, label):
        conge = Conge(creche, creation=False)
        conge.debut = label
        creche.add_conge(conge)
            
    def AddConge(self, debut, fin=None, options=0):
        conge = Conge(creche, creation=False)
        if fin is None:
            fin = debut
        conge.debut, conge.fin = debut, fin
        conge.options = options
        creche.add_conge(conge)
    
    def AddParents(self, inscrit):
        inscrit.papa = Parent(inscrit, creation=False)
        revenu = Revenu(inscrit.papa, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), 30000.0
        inscrit.papa.revenus.append(revenu)
        inscrit.maman = Parent(inscrit, creation=False)
        revenu = Revenu(inscrit.maman, creation=False)
        revenu.debut, revenu.revenu = datetime.date(2008, 1, 1), 0.0
        inscrit.maman.revenus.append(revenu)
                
class DessineMoiUnMoutonTests(GertrudeTestCase):
    def test_24aout_31dec(self):
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = JOURS_FERIES_DEDUITS_ANNUELLEMENT 
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.AddConge("23/08/2010")
        self.AddConge("02/08/2010", "20/08/2010")
        self.AddConge("19/04/2010", "23/04/2010")
        self.AddConge("20/12/2010", "24/12/2010")
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        self.AddParents(inscrit)
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
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = JOURS_FERIES_DEDUITS_ANNUELLEMENT 
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.AddConge("23/08/2010")
        self.AddConge("02/08/2010", "20/08/2010")
        self.AddConge("19/04/2010", "23/04/2010")
        self.AddConge("20/12/2010", "24/12/2010")
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        self.AddParents(inscrit)
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
        __builtin__.creche = Creche()
        creche.mode_facturation = FACTURATION_PSU
        creche.temps_facturation = FACTURATION_FIN_MOIS
        creche.facturation_jours_feries = JOURS_FERIES_DEDUITS_ANNUELLEMENT 
        for label in ("Week-end", "1er janvier", "14 juillet", "1er novembre", "11 novembre", u"Lundi de Pâques", "Jeudi de l'Ascension", u"Lundi de Pentecôte"):
            self.AddJourFerie(label)
        self.AddConge("30/07/2010", options=ACCUEIL_NON_FACTURE)
        self.AddConge("23/08/2010")
        self.AddConge("02/08/2010", "20/08/2010")
        self.AddConge("19/04/2010", "23/04/2010")
        self.AddConge("20/12/2010", "24/12/2010")
        self.AddConge(u"Août", options=MOIS_SANS_FACTURE)
        inscrit = Inscrit(creation=False)
        inscrit.prenom, inscrit.nom = 'gertrude', 'gertrude'
        self.AddParents(inscrit)
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
        
    

if __name__ == '__main__':
    unittest.main()
