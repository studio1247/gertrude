import sys, os, __builtin__
sys.path.append("..")
import unittest
import sqlinterface
from sqlobjects import *
from cotisation import *

class GertrudeTests(unittest.TestCase):

    def test_creation_bdd(self):
        filename = "gertrude.db"
        if os.path.isfile(filename):
            os.remove(filename)
        con = sqlinterface.SQLConnection(filename)
        con.Create()
        
class PAJETests(unittest.TestCase):

    def test_paje(self):
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
        self.assertRaises(CotisationException, Cotisation, inscrit, (datetime.date(2010, 1, 1), None), NO_ADDRESS|NO_PARENTS)
        creche.formule_taux_horaire = [["", 0.0]]
        creche.update_formule_taux_horaire(changed=False)
        cotisation = Cotisation(inscrit, (datetime.date(2010, 1, 1), None), NO_ADDRESS|NO_PARENTS)
        
        


if __name__ == '__main__':
    unittest.main()
