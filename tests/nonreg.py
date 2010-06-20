import sys, os
sys.path.append("..")
import unittest
import sqlinterface

class GertrudeTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_creation_bdd(self):
        os.remove(sqlinterface.DB_FILENAME)
        con = sqlinterface.SQLConnection()
        con.create()


if __name__ == '__main__':
    unittest.main()
