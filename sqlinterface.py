# -*- coding: utf-8 -*-

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

import os, __builtin__
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
from sqlobjects import *

DB_FILENAME = 'gertrude.db'
VERSION = 8

class SQLConnection(object):
    def __init__(self):
        self.con = None
        
    def open(self):
        self.con = sqlite3.connect(DB_FILENAME)

    def commit(self):
        self.con.commit()
        
    def close(self):
        if self.con:
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
        if not self.con:
            self.open()
            
        cur = self.con.cursor()
        cur.execute("""
          CREATE TABLE CRECHE(
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            mois_payes INTEGER,
            presences_previsionnelles BOOLEAN,
            modes_inscription INTEGER
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
          CREATE TABLE EMPLOYES(
            idx INTEGER PRIMARY KEY,
            date_embauche DATE,
            prenom VARCHAR,
            nom VARCHAR,
            telephone_domicile VARCHAR,
            telephone_domicile_notes VARCHAR,
            telephone_portable VARCHAR,
            telephone_portable_notes VARCHAR,
            email VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE INSCRITS(
            idx INTEGER PRIMARY KEY,
            prenom VARCHAR,
            nom VARCHAR,
            sexe INTEGER,
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
        
        cur.execute("""
          CREATE TABLE CONGES(
            idx INTEGER PRIMARY KEY,
            debut VARCHAR,
            fin VARCHAR
          );""")

        cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
        self.con.commit()

    def load(self):
        if not self.con:
            self.open()
            
        def getdate(str):
            if str is None:
                return None
            annee, mois, jour = map(lambda x: int(x), str.split('-'))
            return datetime.date(annee, mois, jour)

        self.translate()

        cur = self.cursor()

        cur.execute('SELECT nom, adresse, code_postal, ville, mois_payes, presences_previsionnelles, modes_inscription, idx FROM CRECHE')
        creche_entry = cur.fetchall()
        if len(creche_entry) > 0:
            creche = Creche(creation=False)
            creche.nom, creche.adresse, creche.code_postal, creche.ville, creche.mois_payes, creche.presences_previsionnelles, creche.modes_inscription, creche.idx = creche_entry[0]
        else:
            creche = Creche()

        cur.execute('SELECT login, password, profile, idx FROM USERS')
        for users_entry in cur.fetchall():
            user = User(creation=False)
            user.login, user.password, user.profile, user.idx = users_entry
            creche.users.append(user)

        cur.execute('SELECT debut, fin, idx FROM CONGES')
        for conges_entry in cur.fetchall():
            conge = Conge(creation=False)
            conge.debut, conge.fin, conge.idx = conges_entry
            creche.add_conge(conge)

        cur.execute('SELECT debut, fin, plancher, plafond, idx FROM BAREMESCAF')
        for bareme_entry in cur.fetchall():
            bareme = BaremeCAF(creation=False)
            bareme.debut, bareme.fin, bareme.plancher, bareme.plafond, idx = bareme_entry
            bareme.debut, bareme.fin, bareme.idx = getdate(bareme.debut), getdate(bareme.fin), idx
            creche.baremes_caf.append(bareme)

        cur.execute('SELECT date_embauche, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, email, idx FROM EMPLOYES')
        for employe_entry in cur.fetchall():
            employe = Employe(creation=False)
            employe.date_embauche = getdate(employe_entry[0])
            employe.prenom, employe.nom, employe.telephone_domicile, employe.telephone_domicile_notes, employe.telephone_portable, employe.telephone_portable_notes, employe.email, employe.idx = employe_entry[1:]
            creche.employes.append(employe)

        parents = {None: None}
        cur.execute('SELECT idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, marche, photo FROM INSCRITS')
        for idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, marche, photo in cur.fetchall():
            if photo:
                photo = binascii.a2b_base64(photo)
            inscrit = Inscrit(creation=False)
            creche.inscrits.append(inscrit)
            inscrit.prenom, inscrit.nom, inscrit.sexe, inscrit.naissance, inscrit.adresse, inscrit.code_postal, inscrit.ville, inscrit.marche, inscrit.photo, inscrit.idx = prenom, nom, sexe, getdate(naissance), adresse, code_postal, ville, getdate(marche), photo, idx
            cur.execute('SELECT prenom, naissance, entree, sortie, idx FROM FRATRIES WHERE inscrit=?', (inscrit.idx,))
            for frere_entry in cur.fetchall():
                frere = Frere_Soeur(inscrit, creation=False)
                frere.prenom, frere.naissance, frere.entree, frere.sortie, idx = frere_entry
                frere.naissance, frere.entree, frere.sortie, frere.idx = getdate(frere.naissance), getdate(frere.entree), getdate(frere.sortie), idx
                inscrit.freres_soeurs.append(frere)
            cur.execute('SELECT idx, debut, fin, mode, periode_reference, fin_periode_essai FROM INSCRIPTIONS WHERE inscrit=?', (inscrit.idx,))
            for idx, debut, fin, mode, periode_reference, fin_periode_essai in cur.fetchall():
                inscription = Inscription(inscrit, creation=False)
                inscription.debut, inscription.fin, inscription.mode, inscription.periode_reference, inscription.fin_periode_essai, inscription.idx = getdate(debut), getdate(fin), mode, eval(periode_reference), getdate(fin_periode_essai), idx
                inscrit.inscriptions.append(inscription)
            cur.execute('SELECT prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email, idx FROM PARENTS WHERE inscrit=?', (inscrit.idx,))
            for parent_entry in cur.fetchall():
                parent = Parent(inscrit, creation=False)
                parent.prenom, parent.nom, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email, parent.idx = parent_entry
                parents[parent.idx] = parent
                if not inscrit.papa:
                    inscrit.papa = parent
                else:
                    inscrit.maman = parent
                cur.execute('SELECT debut, fin, revenu, chomage, regime, idx FROM REVENUS WHERE parent=?', (parent.idx,))
                for revenu_entry in cur.fetchall():
                    revenu = Revenu(parent, creation=False)
                    revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.regime, idx = revenu_entry
                    revenu.debut, revenu.fin, revenu.idx = getdate(revenu.debut), getdate(revenu.fin), idx
                    parent.revenus.append(revenu)
            cur.execute('SELECT date, previsionnel, value, details, idx FROM PRESENCES WHERE inscrit=?', (inscrit.idx,))
            for date, previsionnel, value, details, idx in cur.fetchall():
                presence = Presence(inscrit, getdate(date), previsionnel, value, creation=False)
                presence.set_details(details)
                presence.idx = idx
                inscrit.presences[getdate(date)] = presence

        cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire FROM BUREAUX')
        for idx, debut, fin, president, vice_president, tresorier, secretaire in cur.fetchall():
            bureau = Bureau(creation=False)
            bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire, bureau.idx = getdate(debut), getdate(fin), parents[president], parents[vice_president], parents[tresorier], parents[secretaire], idx
            creche.bureaux.append(bureau)

        creche.inscrits.sort()
        return creche

    def translate(self):
        cur = self.cursor()
        try:
            cur.execute('SELECT value FROM DATA WHERE key="VERSION"')
            version = int(cur.fetchall()[0][0])
        except:
            version = 0

        print version, '=>', VERSION

        if version < 1:
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

##        Not used now
##        if version < 2:
##            cur.execute("ALTER TABLE CRECHE ADD server_url VARCHAR;")
##            cur.execute('UPDATE CRECHE SET server_url=?', ("",))

        if version < 3:
            cur.execute("ALTER TABLE PRESENCES RENAME TO OLD;")
            cur.execute("""
              CREATE TABLE PRESENCES(
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                date DATE,
                previsionnel INTEGER,
                value INTEGER,
                details VARCHAR
              );""")
            def encode_details(details):
                details = eval(details)
                if details is None:
                    return None
                result = 0
                for i, v in enumerate(details):
                    result += v << i
                return result
            cur.execute('SELECT inscrit, date, previsionnel, value, details FROM OLD')
            for inscrit, date, previsionnel, value, details in cur.fetchall():
                cur.execute('INSERT INTO PRESENCES (idx, inscrit, date, previsionnel, value, details) VALUES (NULL,?,?,?,?,?)', (inscrit, date, previsionnel, value, encode_details(details)))
            cur.execute('DROP TABLE OLD')

        if version < 4:
            cur.execute('SELECT details, idx FROM PRESENCES')
            for details, idx in cur.fetchall():
                if details is not None:
                    details = eval(details) << 7
                    cur.execute('UPDATE PRESENCES SET details=? WHERE idx=?', (details, idx))
            
        if version < 5:
            cur.execute("""
              CREATE TABLE CONGES(
                idx INTEGER PRIMARY KEY,
                debut VARCHAR,
                fin VARCHAR
              );""")

        if version < 6:
            cur.execute("ALTER TABLE CRECHE ADD mois_payes INTEGER;")
            cur.execute("ALTER TABLE CRECHE ADD presences_previsionnelles BOOLEAN;")
            cur.execute("ALTER TABLE CRECHE ADD modes_inscription INTEGER;")
            cur.execute('UPDATE CRECHE SET mois_payes=?', (12,))
            cur.execute('UPDATE CRECHE SET presences_previsionnelles=?', (True,))
            cur.execute('UPDATE CRECHE SET modes_inscription=?', (MODE_HALTE_GARDERIE+MODE_4_5+MODE_3_5,))

        if version < 7:
            cur.execute("ALTER TABLE INSCRITS ADD sexe INTEGER;")
            cur.execute('UPDATE INSCRITS SET sexe=?', (1,))
            
        if version < 8:
            cur.execute("""
              CREATE TABLE EMPLOYES(
                idx INTEGER PRIMARY KEY,
                date_embauche DATE,
                prenom VARCHAR,
                nom VARCHAR,
                telephone_domicile VARCHAR,
                telephone_domicile_notes VARCHAR,
                telephone_portable VARCHAR,
                telephone_portable_notes VARCHAR,
                email VARCHAR
            );""")            

        if version < VERSION:
            try:
                cur.execute("DELETE FROM DATA WHERE key=?", ("VERSION", ))
            except sqlite3.OperationalError:
                pass

            cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
            cur.execute("VACUUM")

            self.commit()
        
__builtin__.sql_connection = SQLConnection()
