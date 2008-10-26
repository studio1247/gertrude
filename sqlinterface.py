# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import os, datetime, __builtin__
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
from functions import *
from sqlobjects import *

DB_FILENAME = 'gertrude.db'
VERSION = 17

def getdate(s):
    if s is None:
        return None
    annee, mois, jour = map(lambda x: int(x), s.split('-'))
    return datetime.date(annee, mois, jour)

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

    def create(self, progress_handler=default_progress_handler):
        if not self.con:
            self.open()

        progress_handler.display(u"Création d'une nouvelle base ...")

        cur = self.con.cursor()
        cur.execute("""
          CREATE TABLE CRECHE(
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            ouverture FLOAT,
            fermeture FLOAT,
            affichage_min FLOAT,
            affichage_max FLOAT,
            granularite INTEGER,
            mois_payes INTEGER,
            presences_previsionnelles BOOLEAN,
            modes_inscription INTEGER,
            minimum_maladie INTEGER,
            mode_maladie INTEGER,
            email VARCHAR,
            capacite INTEGER
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
          CREATE TABLE ACTIVITIES(
            idx INTEGER PRIMARY KEY,
            label VARCHAR,
            value INTEGER,
            mode INTEGER,
            color INTEGER
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
            absent BOOLEAN,
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
          CREATE TABLE ACTIVITES(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            value INTEGER,
            debut INTEGER,
            fin INTEGER
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
        cur.execute('INSERT INTO CRECHE(idx, nom, adresse, code_postal, ville, ouverture, fermeture, affichage_min, affichage_max, granularite, mois_payes, presences_previsionnelles, modes_inscription, minimum_maladie, mode_maladie, email, capacite) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', ("","","","",7.75,18.5,7.75,19.0,4,12,True,MODE_HALTE_GARDERIE + MODE_4_5 + MODE_3_5,15,DEDUCTION_AVEC_CARENCE,"",0))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2006, 9, 1), datetime.date(2007, 8, 31), 6547.92, 51723.60))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2007, 9, 1), datetime.date(2008, 12, 31), 6660.00, 52608.00))
        self.con.commit()

    def load(self, progress_handler=default_progress_handler):
        if not self.con:
            self.open()

        if not self.translate(progress_handler):
            return None

        progress_handler.display(u"Chargement en mémoire de la base ...")

        cur = self.cursor()

        cur.execute('SELECT nom, adresse, code_postal, ville, ouverture, fermeture, affichage_min, affichage_max, granularite, mois_payes, presences_previsionnelles, modes_inscription, minimum_maladie, mode_maladie, email, capacite, idx FROM CRECHE')
        creche_entry = cur.fetchall()
        if len(creche_entry) > 0:
            creche = Creche()
            creche.nom, creche.adresse, creche.code_postal, creche.ville, creche.ouverture, creche.fermeture, creche.affichage_min, creche.affichage_max, creche.granularite, creche.mois_payes, creche.presences_previsionnelles, creche.modes_inscription, creche.minimum_maladie, creche.mode_maladie, creche.email, creche.capacite, creche.idx = creche_entry[0]
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

        cur.execute('SELECT label, value, mode, color, idx FROM ACTIVITIES')
        for entry in cur.fetchall():
            activity = Activite(creation=False)
            activity.label, activity.value, activity.mode, activity.color, activity.idx = entry
            creche.activites[activity.value] = activity
        
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
            cur.execute('SELECT absent, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email, idx FROM PARENTS WHERE inscrit=?', (inscrit.idx,))
            for parent_entry in cur.fetchall():
                parent = Parent(inscrit, creation=False)
                parent.absent, parent.prenom, parent.nom, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email, parent.idx = parent_entry
                parents[parent.idx] = parent
                if not inscrit.papa:
                    inscrit.papa = parent
                else:
                    inscrit.maman = parent
                if not parent.absent:
                    cur.execute('SELECT debut, fin, revenu, chomage, regime, idx FROM REVENUS WHERE parent=?', (parent.idx,))
                    for revenu_entry in cur.fetchall():
                        revenu = Revenu(parent, creation=False)
                        revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.regime, idx = revenu_entry
                        revenu.debut, revenu.fin, revenu.idx = getdate(revenu.debut), getdate(revenu.fin), idx
                        parent.revenus.append(revenu)
            cur.execute('SELECT date, value, debut, fin, idx FROM ACTIVITES WHERE inscrit=?', (inscrit.idx,))
            for date, value, debut, fin, idx in cur.fetchall():
                key = getdate(date)
                if key in inscrit.journees:
                    journee = inscrit.journees[key]
                else:
                    journee = Journee(inscrit, key)
                    inscrit.journees[key] = journee
                journee.add_activity(debut, fin, value, idx)

        cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire FROM BUREAUX')
        for idx, debut, fin, president, vice_president, tresorier, secretaire in cur.fetchall():
            bureau = Bureau(creation=False)
            bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire, bureau.idx = getdate(debut), getdate(fin), parents[president], parents[vice_president], parents[tresorier], parents[secretaire], idx
            creche.bureaux.append(bureau)

        creche.inscrits.sort()
        return creche

    def translate(self, progress_handler=default_progress_handler):
        cur = self.cursor()
        try:
            cur.execute('SELECT value FROM DATA WHERE key="VERSION"')
            version = int(cur.fetchall()[0][0])
        except:
            version = 0

        if version == VERSION:
            return True

        if version > VERSION:
            progress_handler.display(u"Base de données plus récente que votre version de Gertrude !")
            return False

        progress_handler.display(u"Conversion de la base de données (version %d => version %d) ..." % (version, VERSION))

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

        if version < 9:
            cur.execute("ALTER TABLE PARENTS ADD absent BOOLEAN;")
            cur.execute('UPDATE PARENTS SET absent=?', (False,))

        if version < 10:
            cur.execute("ALTER TABLE CRECHE ADD minimum_maladie INTEGER;")
            cur.execute("ALTER TABLE CRECHE ADD mode_maladie INTEGER;")
            cur.execute('UPDATE CRECHE SET minimum_maladie=?', (15,))
            cur.execute('UPDATE CRECHE SET mode_maladie=?', (DEDUCTION_AVEC_CARENCE,))

        if version < 11:
            cur.execute("ALTER TABLE CRECHE ADD email VARCHAR;")
            cur.execute("ALTER TABLE CRECHE ADD capacite INTEGER;")
            cur.execute('UPDATE CRECHE SET email=?', ("",))
            cur.execute('UPDATE CRECHE SET capacite=?', (0,))

        if version < 12:
            cur.execute("ALTER TABLE CRECHE ADD ouverture FLOAT;")
            cur.execute("ALTER TABLE CRECHE ADD fermeture FLOAT;")
            cur.execute("ALTER TABLE CRECHE ADD affichage_min FLOAT;")
            cur.execute("ALTER TABLE CRECHE ADD affichage_max FLOAT;")
            cur.execute('UPDATE CRECHE SET ouverture=?', (7.75,))
            cur.execute('UPDATE CRECHE SET fermeture=?', (18.5,))
            cur.execute('UPDATE CRECHE SET affichage_min=?', (7.75,))
            cur.execute('UPDATE CRECHE SET affichage_max=?', (19.0,))
            cur.execute("ALTER TABLE CRECHE ADD granularite INTEGER;")
            cur.execute('UPDATE CRECHE SET granularite=?', (4,))

        if version < 13:
            cur.execute('SELECT debut, fin, idx FROM REVENUS;')
            for debut, fin, idx in cur.fetchall():
                if debut is not None:
                    debut = datetime.date(getdate(debut).year-1, 1, 1)
                    sql_connection.execute('UPDATE REVENUS SET debut=? WHERE idx=?', (debut, idx))
                if fin is not None:
                    fin = datetime.date(getdate(fin).year-2, 12, 31)
                    sql_connection.execute('UPDATE REVENUS SET fin=? WHERE idx=?', (fin, idx))

        if version < 14:
            cur.execute('UPDATE BAREMESCAF SET fin=? WHERE debut=? and fin=? and plancher=? and plafond=?;', (datetime.date(2008, 12, 31), datetime.date(2007, 9, 1), datetime.date(2008, 8, 31), 6660.00, 52608.00))

        if version < 15:
            cur.execute("""
              CREATE TABLE ACTIVITES(
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                date DATE,
                value INTEGER,
                debut INTEGER,
                fin INTEGER
                );""")
            cur.execute('SELECT inscrit, date, value, previsionnel, details FROM PRESENCES')
            for inscrit_idx, date, value, previsionnel, val_details in cur.fetchall():
                if value == 0:
                    value = 1
                    if previsionnel:
                        value += 256
                    if isinstance(val_details, basestring):
                        val_details = eval(val_details)
                    details = 64 * [0]
                    for i in range(64):
                        if val_details & (1 << i):
                            details[i] = 1
                   
                    a = v = 0
                    h = 6*4
                    while h <= 22*4:
                        if h == 22*4:
                            nv = 0
                        else:
                            nv = details[h-(6*4)]
                        if nv != v:
                            if v != 0:
                                sql_connection.execute('INSERT INTO ACTIVITES (idx, inscrit, date, value, debut, fin) VALUES (NULL,?,?,?,?,?)', (inscrit_idx, date, value, a, h))
                            a = h
                            v = nv
                        h += 1
                elif value in (1, 2): # VACANCES & MALADE
                    sql_connection.execute('INSERT INTO ACTIVITES (idx, inscrit, date, value, debut, fin) VALUES (NULL,?,?,?,?,?)', (inscrit_idx, date, -value, 32, 72))
            cur.execute("DROP TABLE PRESENCES;")
                                   
        if version < 16:
            cur.execute("""
              CREATE TABLE ACTIVITIES(
                idx INTEGER PRIMARY KEY,
                label VARCHAR,
                value INTEGER,
                mode INTEGER
              );""")

        if version < 17:
            cur.execute("ALTER TABLE ACTIVITIES ADD color INTEGER;")
            cur.execute('SELECT value, idx FROM ACTIVITIES')
            activities = []
            for value, idx in cur.fetchall():
                activities.append((value, idx))
            for value, idx in activities:
                cur.execute('UPDATE ACTIVITIES SET color=? WHERE idx=?', (value,idx))
            
        if version < VERSION:
            try:
                cur.execute("DELETE FROM DATA WHERE key=?", ("VERSION", ))
            except sqlite3.OperationalError:
                pass

            cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
            cur.execute("VACUUM")

            self.commit()

        return True

__builtin__.sql_connection = SQLConnection()
