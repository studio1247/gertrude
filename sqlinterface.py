##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from constants import *

import os
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3


class BDDConnection(object):
    def __init__(self):
        self.open()
        
    def open(self):
        if not os.path.exists('gertrude.db'):
            self.con = sqlite3.connect('gertrude.db')
            self.create()
        else:
            self.con = sqlite3.connect('gertrude.db')

    def commit(self):
        self.con.commit()
        
    def close(self):
        self.con.commit()
        self.con.close()
        self.con = None
        
    def cursor(self):
        if self.con is None:
            self.open()
        return self.con.cursor()

    def execute(self, cmd, *args):
        return self.con.execute(cmd, *args)
        
    def create(self):
        cur = self.con.cursor()
        cur.execute("""
          CREATE TABLE CRECHE(
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            server_url VARCHAR
          );""")
    
        cur.execute("""
          CREATE TABLE BUREAUX(
            idx INTEGER PRIMARY KEY,
            debut DATE,
            fin DATE,
            president INTEGER REFERENCES INSCRITS(idx),
            vice_president INTEGER REFERENCES INSCRITS(idx),
            tresorier INTEGER REFERENCES INSCRITS(idx),
            secretaire INTEGER REFERENCES INSCRITS(idx)
          );""")
        
        cur.execute("""
          CREATE TABLE BAREMESCAF(
            idx INTEGER PRIMARY KEY,
            debut DATE,
            fin DATE,
            plancher INTEGER,
            plafond INTEGER
          );""")
    
        cur.execute("""
          CREATE TABLE INSCRITS(
            idx INTEGER PRIMARY KEY,
            prenom VARCHAR,
            nom VARCHAR,
            naissance DATE,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            marche BOOLEAN,
            photo VARCHAR
          );""")
        
        cur.execute("""
          CREATE TABLE PARENTS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            prenom VARCHAR,
            nom VARCHAR,
            telephone_domicile VARCHAR,
            telephone_domicile_notes VARCHAR,
            telephone_portable VARCHAR,
            telephone_portable_notes VARCHAR,
            telephone_travail VARCHAR,
            telephone_travail_notes VARCHAR,
            email VARCHAR
          );""")
        
        cur.execute("""  
          CREATE TABLE FRATRIES (
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            prenom VARCHAR,
            naissance DATE,
            entree DATE,
            sortie DATE
          );""")
        
        cur.execute("""  
          CREATE TABLE INSCRIPTIONS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            debut DATE,
            fin DATE,
            mode, INTEGER,
            periode_reference VARCHAR,
            fin_periode_essai DATE
          );""")
        
        cur.execute("""
          CREATE TABLE REVENUS(
            idx INTEGER PRIMARY KEY,
            parent INTEGER REFERENCES PARENTS(idx),
            debut DATE,
            fin DATE,
            revenu INTEGER,
            chomage BOOLEAN,
            regime INTEGER
          );""")
        
        cur.execute("""
          CREATE TABLE PRESENCES(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            previsionnel INTEGER,
            value INTEGER,
            details VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE DATA(
            key VARCHAR,
            value VARCHAR
          );""")
        
        cur.execute("""
          CREATE TABLE USERS(
            idx INTEGER PRIMARY KEY,
            login VARCHAR,
            password VARCHAR,
            profile INTEGER
          );""")
        
        cur.execute("INSERT INTO USERS (idx, login, password, profile) VALUES (NULL,?,?,?)", ("admin", "admin", PROFIL_ALL))


        cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
        self.con.commit()
        
connection = BDDConnection()
