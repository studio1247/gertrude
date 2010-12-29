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
import wx

VERSION = 47

def getdate(s):
    if s is None:
        return None
    annee, mois, jour = map(lambda x: int(x), s.split('-'))
    return datetime.date(annee, mois, jour)

class SQLConnection(object):
    def __init__(self, filename):
        self.filename = filename
        self.con = None

    def open(self):
        self.con = sqlite3.connect(self.filename)

    def commit(self):
        if self.con:
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

    def Create(self, progress_handler=default_progress_handler):
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
            telephone VARCHAR,
            ouverture FLOAT,
            fermeture FLOAT,
            affichage_min FLOAT,
            affichage_max FLOAT,
            granularite INTEGER,
            mois_payes INTEGER,
            preinscriptions BOOLEAN,
            presences_previsionnelles BOOLEAN,
            presences_supplementaires BOOLEAN,
            modes_inscription INTEGER,
            minimum_maladie INTEGER,
            email VARCHAR,
            type INTEGER,
            capacite INTEGER,
            mode_facturation INTEGER,
            temps_facturation INTEGER,
            conges_inscription INTEGER,
            tarification_activites INTEGER,
            traitement_maladie INTEGER,
            majoration_localite FLOAT,
            facturation_jours_feries INTEGER,
            facturation_periode_adaptation INTEGER,
            formule_taux_horaire VARCHAR,
            gestion_alertes BOOLEAN
          );""")
        
        cur.execute("""
          CREATE TABLE SITES(
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            telephone VARCHAR,
            capacite INTEGER
          );""")

        cur.execute("""
          CREATE TABLE BUREAUX(
            idx INTEGER PRIMARY KEY,
            debut DATE,
            fin DATE,
            president VARCHAR,
            vice_president VARCHAR,
            tresorier VARCHAR,
            secretaire VARCHAR,
            directeur VARCHAR
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
            couleur VARCHAR,
            couleur_supplement VARCHAR,
            couleur_previsionnel VARCHAR,
            tarif INTEGER
          );""")
        
        cur.execute("""  
          CREATE TABLE CONTRATS(
            idx INTEGER PRIMARY KEY,
            employe INTEGER REFERENCES EMPLOYES(idx),
            site INTEGER REFERENCES SITES(idx),
            debut DATE,
            fin DATE,
            fonction VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE EMPLOYES(
            idx INTEGER PRIMARY KEY,
            prenom VARCHAR,
            nom VARCHAR,
            telephone_domicile VARCHAR,
            telephone_domicile_notes VARCHAR,
            telephone_portable VARCHAR,
            telephone_portable_notes VARCHAR,
            email VARCHAR,
            diplomes VARCHAR
          );""")
        
        cur.execute("""  
          CREATE TABLE PROFESSEURS (
            idx INTEGER PRIMARY KEY,
            prenom VARCHAR,
            nom VARCHAR,
            entree DATE,
            sortie DATE
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
            numero_securite_sociale VARCHAR,
            numero_allocataire_caf VARCHAR,
            handicap BOOLEAN,
            majoration BOOLEAN,
            marche BOOLEAN,
            photo VARCHAR,
            notes VARCHAR,
            notes_parents VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE PARENTS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            relation VARCHAR,
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
          CREATE TABLE REFERENTS (
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            prenom VARCHAR,
            nom VARCHAR,
            telephone VARCHAR
          );""")

        cur.execute("""  
          CREATE TABLE INSCRIPTIONS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            preinscription BOOLEAN,
            forfait_mensuel FLOAT,
            site INTEGER REFERENCES SITES(idx),
            sites_preinscription VARCHAR,
            professeur INTEGER REFERENCES PROFESSEURS(idx),
            debut DATE,
            fin DATE,
            mode, INTEGER,
            fin_periode_adaptation DATE,
            duree_reference INTEGER,
            semaines_conges INTEGER
          );""")

        cur.execute("""
          CREATE TABLE REF_ACTIVITIES(
            idx INTEGER PRIMARY KEY,
            reference INTEGER REFERENCES INSCRIPTIONS(idx),
            day INTEGER,
            value INTEGER,
            debut INTEGER,
            fin INTEGER
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
            fin VARCHAR,
            label VARCHAR,
            options INTEGER
          );""")
        
        cur.execute("""
          CREATE TABLE CONGES_INSCRITS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            debut VARCHAR,
            fin VARCHAR,
            label VARCHAR
          );""")
        
        cur.execute("""  
          CREATE TABLE ALERTES (
            idx INTEGER PRIMARY KEY,
            texte VARCHAR,
            date DATE,
            acquittement BOOLEAN
          );""")

        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", u"15 août", "1er novembre", "11 novembre", u"25 décembre", u"Lundi de Pâques", "Jeudi de l'Ascension"):
            cur.execute("INSERT INTO CONGES (idx, debut) VALUES (NULL, ?)", (label, ))
        cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
        cur.execute('INSERT INTO CRECHE(idx, nom, adresse, code_postal, ville, telephone, ouverture, fermeture, affichage_min, affichage_max, granularite, mois_payes, preinscriptions, presences_previsionnelles, presences_supplementaires, modes_inscription, minimum_maladie, email, type, capacite, mode_facturation, temps_facturation, conges_inscription, tarification_activites, traitement_maladie, majoration_localite, facturation_jours_feries, facturation_periode_adaptation, formule_taux_horaire, gestion_alertes) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                     ("","","","","",7.75,18.5,7.75,19.0,15,12,False,False,True,MODE_HALTE_GARDERIE + MODE_4_5 + MODE_3_5,15,"",TYPE_PARENTAL,0,FACTURATION_FORFAIT_10H,FACTURATION_FIN_MOIS,0,0,DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES,0.0,JOURS_FERIES_NON_DEDUITS,PERIODE_ADAPTATION_FACTUREE_NORMALEMENT,"None", False))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2006, 9, 1), datetime.date(2007, 8, 31), 6547.92, 51723.60))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2007, 9, 1), datetime.date(2008, 12, 31), 6660.00, 52608.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2009, 1, 1), datetime.date(2009, 12, 31), 6876.00, 53400.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2010, 1, 1), datetime.date(2010, 12, 31), 6956.64, 54895.20))

        couleur = [5, 203, 28, 150, wx.SOLID]
        couleur_supplement = [5, 203, 28, 250, wx.SOLID]
        couleur_previsionnel = [5, 203, 28, 50, wx.SOLID]
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, tarif) VALUES(NULL,?,?,?,?,?,?,?)', (u"Présences", 0, 0, str(couleur), str(couleur_supplement), str(couleur_previsionnel), .0))
        vacances = (0, 0, 255, 150, wx.SOLID)
        malade = (190, 35, 29, 150, wx.SOLID)
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, tarif) VALUES(NULL,?,?,?,?,?,?,?)', (u"Vacances", -1, 0, str(vacances), str(vacances), str(vacances), .0))
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, tarif) VALUES(NULL,?,?,?,?,?,?,?)', (u"Malade", -2, 0, str(malade), str(malade), str(malade), .0))

        self.con.commit()

    def Liste(self):
        con = sqlite3.connect(self.filename)
        cur = con.cursor()
        cur.execute('SELECT prenom, nom FROM INSCRITS')
        return ["%s %s" % entry for entry in cur.fetchall()]
        
    def Load(self, progress_handler=default_progress_handler):
        if not self.con:
            self.open()

        if not self.translate(progress_handler):
            return None

        progress_handler.display(u"Chargement en mémoire de la base ...")

        cur = self.cursor()

        cur.execute('SELECT nom, adresse, code_postal, ville, telephone, ouverture, fermeture, affichage_min, affichage_max, granularite, mois_payes, preinscriptions, presences_previsionnelles, presences_supplementaires, modes_inscription, minimum_maladie, email, type, capacite, mode_facturation, temps_facturation, conges_inscription, tarification_activites, traitement_maladie, majoration_localite, facturation_jours_feries, facturation_periode_adaptation, formule_taux_horaire, gestion_alertes, idx FROM CRECHE')
        creche_entry = cur.fetchall()
        if len(creche_entry) > 0:
            creche = Creche()
            creche.nom, creche.adresse, creche.code_postal, creche.ville, creche.telephone, creche.ouverture, creche.fermeture, creche.affichage_min, creche.affichage_max, creche.granularite, creche.mois_payes, creche.preinscriptions, creche.presences_previsionnelles, creche.presences_supplementaires, creche.modes_inscription, creche.minimum_maladie, creche.email, creche.type, creche.capacite, creche.mode_facturation, creche.temps_facturation, creche.conges_inscription, creche.tarification_activites, creche.traitement_maladie, creche.majoration_localite, creche.facturation_jours_feries, creche.facturation_periode_adaptation, formule_taux_horaire, creche.gestion_alertes, idx = creche_entry[0]
            creche.formule_taux_horaire, creche.idx = eval(formule_taux_horaire), idx
        else:
            creche = Creche()
        creche.update_formule_taux_horaire(changed=False)
        
        cur.execute('SELECT nom, adresse, code_postal, ville, telephone, capacite, idx FROM SITES')
        for site_entry in cur.fetchall():
            site = Site(creation=False)
            site.nom, site.adresse, site.code_postal, site.ville, site.telephone, site.capacite, site.idx = site_entry
            creche.sites.append(site)
                
        cur.execute('SELECT login, password, profile, idx FROM USERS')
        for users_entry in cur.fetchall():
            user = User(creation=False)
            user.login, user.password, user.profile, user.idx = users_entry
            # print user.login, user.password
            creche.users.append(user)

        cur.execute('SELECT debut, fin, label, options, idx FROM CONGES')
        for conges_entry in cur.fetchall():
            conge = Conge(creche, creation=False)
            conge.debut, conge.fin, conge.label, conge.options, conge.idx = conges_entry
            creche.add_conge(conge, calcule=False)
        creche.calcule_jours_conges()

        cur.execute('SELECT debut, fin, plancher, plafond, idx FROM BAREMESCAF')
        for bareme_entry in cur.fetchall():
            bareme = BaremeCAF(creation=False)
            bareme.debut, bareme.fin, bareme.plancher, bareme.plafond, idx = bareme_entry
            bareme.debut, bareme.fin, bareme.idx = getdate(bareme.debut), getdate(bareme.fin), idx
            creche.baremes_caf.append(bareme)

        cur.execute('SELECT label, value, mode, couleur, couleur_supplement, couleur_previsionnel, tarif, idx FROM ACTIVITIES')
        activites_by_idx = {}
        for entry in cur.fetchall():
            activity = Activite(creation=False)
            activity.label, activity.value, activity.mode, activity.couleur, activity.couleur_supplement, activity.couleur_previsionnel, activity.tarif, activity.idx = entry
            if activity.value < 0:
                creche.couleurs[activity.value] = activity
            else:
                creche.activites[activity.value] = activity
                
        cur.execute('SELECT prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, email, diplomes, idx FROM EMPLOYES')
        for employe_entry in cur.fetchall():
            employe = Employe(creation=False)
            employe.prenom, employe.nom, employe.telephone_domicile, employe.telephone_domicile_notes, employe.telephone_portable, employe.telephone_portable_notes, employe.email, employe.diplomes, employe.idx = employe_entry
            creche.employes.append(employe)
            cur.execute('SELECT debut, fin, site, fonction, idx FROM CONTRATS WHERE employe=?', (employe.idx,))
            for debut, fin, site_idx, fonction, idx in cur.fetchall():
                contrat = Contrat(employe, creation=False)
                site = None
                for s in creche.sites:
                    if s.idx == site_idx:
                        site = s
                        break
                contrat.debut, contrat.fin, contrat.site, contrat.fonction, contrat.idx = getdate(debut), getdate(fin), site, fonction, idx
                employe.contrats.append(contrat)

        cur.execute('SELECT prenom, nom, entree, sortie, idx FROM PROFESSEURS')
        for professeur_entry in cur.fetchall():
            professeur = Professeur(creation=False)
            professeur.prenom, professeur.nom, professeur.entree, professeur.sortie, idx = professeur_entry
            professeur.entree = getdate(professeur.entree)
            professeur.sortie = getdate(professeur.sortie)
            professeur.idx = idx
            creche.professeurs.append(professeur)

        cur.execute('SELECT idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, handicap, majoration, marche, photo FROM INSCRITS')
        for idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, handicap, majoration, marche, photo in cur.fetchall():
            if photo:
                photo = binascii.a2b_base64(photo)
            inscrit = Inscrit(creation=False)
            creche.inscrits.append(inscrit)
            inscrit.prenom, inscrit.nom, inscrit.sexe, inscrit.naissance, inscrit.adresse, inscrit.code_postal, inscrit.ville, inscrit.numero_securite_sociale, inscrit.numero_allocataire_caf, inscrit.handicap, inscrit.majoration, inscrit.marche, inscrit.photo, inscrit.idx = prenom, nom, sexe, getdate(naissance), adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, handicap, majoration, getdate(marche), photo, idx
            cur.execute('SELECT prenom, naissance, entree, sortie, idx FROM FRATRIES WHERE inscrit=?', (inscrit.idx,))
            for frere_entry in cur.fetchall():
                frere = Frere_Soeur(inscrit, creation=False)
                frere.prenom, frere.naissance, frere.entree, frere.sortie, idx = frere_entry
                frere.naissance, frere.entree, frere.sortie, frere.idx = getdate(frere.naissance), getdate(frere.entree), getdate(frere.sortie), idx
                inscrit.freres_soeurs.append(frere)
            cur.execute('SELECT prenom, nom, telephone, idx FROM REFERENTS WHERE inscrit=?', (inscrit.idx,))
            for referent_entry in cur.fetchall():
                referent = Referent(inscrit, creation=False)
                referent.prenom, referent.nom, referent.telephone, referent.idx = referent_entry
                inscrit.referents.append(referent)
            cur.execute('SELECT idx, debut, fin, mode, forfait_mensuel, fin_periode_adaptation, duree_reference, semaines_conges, preinscription, site, sites_preinscription, professeur FROM INSCRIPTIONS WHERE inscrit=?', (inscrit.idx,))
            for idx, debut, fin, mode, forfait_mensuel, fin_periode_adaptation, duree_reference, semaines_conges, preinscription, site, sites_preinscription, professeur in cur.fetchall():
                inscription = Inscription(inscrit, duree_reference, creation=False)
                for tmp in creche.sites:
                    if site == tmp.idx:
                        inscription.site = tmp
                if sites_preinscription:
                    for site_preinscription in sites_preinscription.split():
                        site_preinscription = int(site_preinscription)
                        for tmp in creche.sites:
                            if site_preinscription == tmp.idx:
                                inscription.sites_preinscription.append(tmp)
                for tmp in creche.professeurs:
                    if professeur == tmp.idx:
                        inscription.professeur = tmp
                inscription.debut, inscription.fin, inscription.mode, inscription.preinscription, inscription.forfait_mensuel, inscription.fin_periode_adaptation, inscription.semaines_conges, inscription.idx = getdate(debut), getdate(fin), mode, preinscription, forfait_mensuel, getdate(fin_periode_adaptation), semaines_conges, idx
                inscrit.inscriptions.append(inscription)
            for inscription in inscrit.inscriptions:
                cur.execute('SELECT day, value, debut, fin, idx FROM REF_ACTIVITIES WHERE reference=?', (inscription.idx,))
                for day, value, debut, fin, idx in cur.fetchall():
                    reference_day = inscription.reference[day]
                    reference_day.add_activity(debut, fin, value, idx)
                    # print inscrit.prenom, day, debut, fin, value
            cur.execute('SELECT debut, fin, label, idx FROM CONGES_INSCRITS WHERE inscrit=?', (inscrit.idx,))
            for conges_entry in cur.fetchall():
                conge = CongeInscrit(inscrit, creation=False)
                conge.debut, conge.fin, conge.label, conge.idx = conges_entry
                inscrit.conges.append(conge)
            inscrit.calcule_jours_conges(creche)
            
            cur.execute('SELECT relation, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email, idx FROM PARENTS WHERE inscrit=?', (inscrit.idx,))
            for parent_entry in cur.fetchall():
                parent = Parent(inscrit, creation=False)
                parent.relation, parent.prenom, parent.nom, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email, parent.idx = parent_entry
                inscrit.parents[parent.relation] = parent
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
                # print inscrit.prenom, key, debut, fin, value
                journee.add_activity(debut, fin, value, idx)

        cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire, directeur FROM BUREAUX')
        for idx, debut, fin, president, vice_president, tresorier, secretaire, directeur in cur.fetchall():
            bureau = Bureau(creation=False)
            bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire, bureau.directeur, bureau.idx = getdate(debut), getdate(fin), president, vice_president, tresorier, secretaire, directeur, idx
            creche.bureaux.append(bureau)
            
        cur.execute('SELECT idx, date, texte, acquittement FROM ALERTES')
        for idx, date, texte, acquittement in cur.fetchall():
            alerte = Alerte(getdate(date), texte, acquittement, creation=False)
            alerte.idx = idx
            creche.alertes[texte] = alerte
            
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
            cur.execute('UPDATE CRECHE SET presences_previsionnelles=?', (False,))
            cur.execute('UPDATE CRECHE SET modes_inscription=?', (7,))

        if version < 7:
            cur.execute("ALTER TABLE INSCRITS ADD sexe INTEGER;")
            cur.execute('UPDATE INSCRITS SET sexe=?', (1,))

        if version < 8:
            cur.execute("""
              CREATE TABLE EMPLOYES(
                idx INTEGER PRIMARY KEY,
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
            cur.execute('UPDATE CRECHE SET minimum_maladie=?', (15,))

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
                    if previsionnel:
                        value += (1 << 30) # PREVISIONNEL
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

        if version < 18:
            cur.execute('SELECT ouverture, fermeture FROM CRECHE')
            ouverture, fermeture = cur.fetchall()[0]
            tranches = [(ouverture, 12), (12, 14), (14, fermeture)]
            __builtin__.creche = Creche()
            
            cur.execute("""
              CREATE TABLE REF_ACTIVITIES(
                idx INTEGER PRIMARY KEY,
                reference INTEGER REFERENCES INSCRIPTIONS(idx),
                day INTEGER,
                value INTEGER,
                debut INTEGER,
                fin INTEGER
              );""")

            cur.execute('SELECT idx, periode_reference FROM INSCRIPTIONS')
            for idx, periode_reference in cur.fetchall():
                inscription = Inscription(None, False)
                inscription.idx = idx
                periode_reference = eval(periode_reference)
                for weekday in range(5):
                    day = ReferenceDay(inscription, weekday)
                    for i, tranche in enumerate(tranches):
                        debut, fin = tranche
                        for j in range(int(debut*4), int(fin*4)):
                            day.values[j] = periode_reference[weekday][i]
                    day.save()
        
        if version < 19:
            cur.execute('UPDATE CRECHE SET modes_inscription=? WHERE modes_inscription=?', (1+2+4+8, 7))
            cur.execute('UPDATE CRECHE SET modes_inscription=? WHERE modes_inscription=?', (2, 0))
            cur.execute('UPDATE INSCRIPTIONS SET mode=? WHERE mode=?', (2, 0))
            
        if version < 20:
            for label in ["Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", u"15 août", "1er novembre", "11 novembre", u"25 décembre", u"Lundi de Pâques", "Jeudi de l'Ascension"]:
                cur.execute("INSERT INTO CONGES (idx, debut) VALUES (NULL, ?)", (label, ))

        if version < 21:
            if version >= 10:
                cur.execute('SELECT mode_maladie FROM CRECHE')
                mode_maladie = cur.fetchall()[0][0]
                if mode_maladie == 2:
                    mode_facturation = 2 # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
                else:
                    mode_facturation = 0
            else:
                mode_facturation = 2 # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
            cur.execute("ALTER TABLE CRECHE ADD mode_facturation INTEGER;")
            cur.execute('UPDATE CRECHE SET mode_facturation=?', (mode_facturation,))

        if version < 22:
            cur.execute("ALTER TABLE CRECHE ADD type INTEGER;")
            cur.execute('UPDATE CRECHE SET type=?', (0,))
            cur.execute("ALTER TABLE CRECHE ADD telephone VARCHAR;")
            cur.execute('UPDATE CRECHE SET telephone=?', ("",))           

        if version < 23 and version >= 21:
            cur.execute('SELECT mode_facturation FROM CRECHE')
            mode_facturation = cur.fetchall()[0][0]
            if mode_facturation & 1:
                mode_facturation -= 1
            else:
                mode_facturation += 1
            cur.execute('UPDATE CRECHE SET mode_facturation=?', (mode_facturation,))

        if version < 24:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD duree_reference INTEGER;")
            cur.execute('UPDATE INSCRIPTIONS SET duree_reference=?', (7,))
        
        if version < 25:
            couleurs = [[5, 203, 28, 150, wx.SOLID],
                        [250, 0, 0, 150, wx.BDIAGONAL_HATCH],
                        [0, 0, 255, 150, wx.FDIAGONAL_HATCH],
                        [255, 0, 255, 150, wx.FDIAGONAL_HATCH],
                        [255, 255, 0, 150, wx.FDIAGONAL_HATCH]]
            couleurs_supplement = [[5, 203, 28, 250, wx.SOLID],
                        [250, 0, 0, 250, wx.BDIAGONAL_HATCH],
                        [0, 0, 255, 250, wx.FDIAGONAL_HATCH],
                        [255, 0, 255, 250, wx.FDIAGONAL_HATCH],
                        [255, 255, 0, 250, wx.FDIAGONAL_HATCH]]
            couleurs_previsionnel = [[5, 203, 28, 50, wx.SOLID],
                        [250, 0, 0, 50, wx.BDIAGONAL_HATCH],
                        [0, 0, 255, 50, wx.FDIAGONAL_HATCH],
                        [255, 0, 255, 50, wx.FDIAGONAL_HATCH],
                        [255, 255, 0, 50, wx.FDIAGONAL_HATCH]]
            cur.execute("ALTER TABLE CRECHE ADD presences_supplementaires BOOLEAN;")
            cur.execute("ALTER TABLE ACTIVITIES ADD couleur VARCHAR;")
            cur.execute("ALTER TABLE ACTIVITIES ADD couleur_supplement VARCHAR;")
            cur.execute("ALTER TABLE ACTIVITIES ADD couleur_previsionnel VARCHAR;")
            cur.execute('UPDATE CRECHE SET presences_supplementaires=?', (True,))
            cur.execute('SELECT idx, color FROM ACTIVITIES')
            for idx, couleur in cur.fetchall():
                cur.execute('UPDATE ACTIVITIES SET couleur=?, couleur_supplement=?, couleur_previsionnel=? WHERE idx=?', (str(couleurs[couleur]), str(couleurs_supplement[couleur]), str(couleurs_previsionnel[couleur]), idx))
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', (u"Présences", 0, 0, str(couleurs[0]), str(couleurs_supplement[0]), str(couleurs_previsionnel[0])))
            
        if version < 26:
            vacances = (0, 0, 255, 150, wx.SOLID)
            malade = (190, 35, 29, 150, wx.SOLID)
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', (u"Vacances", -1, 0, str(vacances), str(vacances), str(vacances)))
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', (u"Malade", -2, 0, str(malade), str(malade), str(malade)))

        if version < 27:
            cur.execute("ALTER TABLE CRECHE ADD tarification_activites INTEGER;")
            cur.execute('UPDATE CRECHE SET tarification_activites=?', (0,))
            cur.execute("ALTER TABLE ACTIVITIES ADD tarif FLOAT;")
            cur.execute('SELECT idx FROM ACTIVITIES')
            for (idx, ) in cur.fetchall():
                cur.execute('UPDATE ACTIVITIES SET tarif=? WHERE idx=?', (.0, idx))

        if version < 28:
            cur.execute("ALTER TABLE CRECHE ADD traitement_maladie INTEGER;")
            cur.execute('SELECT mode_facturation FROM CRECHE')
            mode_facturation = cur.fetchall()[0][0]
            if mode_facturation & 2: # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
                cur.execute('UPDATE CRECHE SET traitement_maladie=?', (2,)) # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
                cur.execute('UPDATE CRECHE SET mode_facturation=?', (mode_facturation-2,))
            else:
                cur.execute('UPDATE CRECHE SET traitement_maladie=?', (0,)) # DEDUCTION_MALADIE_SANS_CARENCE

        if version < 29:
            cur.execute('ALTER TABLE CRECHE ADD forfait_horaire FLOAT')
            cur.execute('UPDATE CRECHE SET forfait_horaire=0.0')
            cur.execute('ALTER TABLE CRECHE ADD majoration_localite FLOAT')
            cur.execute('UPDATE CRECHE SET majoration_localite=0.0')
            cur.execute('ALTER TABLE INSCRITS ADD majoration BOOLEAN')
            cur.execute('UPDATE INSCRITS SET majoration=0')
            cur.execute('ALTER TABLE INSCRIPTIONS ADD semaines_conges INTEGER')
            cur.execute('UPDATE INSCRIPTIONS SET semaines_conges=0')  

        if version < 30:
            cur.execute('SELECT debut, fin, idx FROM ACTIVITES')
            for debut, fin, idx in cur.fetchall():
                cur.execute('UPDATE ACTIVITES SET debut=?, fin=? WHERE idx=?', (debut*3, fin*3, idx))
            cur.execute('SELECT debut, fin, idx FROM REF_ACTIVITIES')
            for debut, fin, idx in cur.fetchall():
                cur.execute('UPDATE REF_ACTIVITIES SET debut=?, fin=? WHERE idx=?', (debut*3, fin*3, idx))
            cur.execute('SELECT granularite FROM CRECHE')
            granularite = 60 / cur.fetchall()[0][0] 
            cur.execute('UPDATE CRECHE SET granularite=?', (granularite,))
        
        if version < 31:
            cur.execute("ALTER TABLE CRECHE ADD facturation_jours_feries INTEGER")
            cur.execute('UPDATE CRECHE SET facturation_jours_feries=?', (0,))
            
        if version < 32:
            cur.execute("ALTER TABLE CONGES ADD label VARCHAR")
            cur.execute("ALTER TABLE CONGES ADD options INTEGER")
            cur.execute('UPDATE CONGES SET label=?, options=?', ("", 0))

        if version < 33:
            cur.execute("""  
              CREATE TABLE REFERENTS (
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                prenom VARCHAR,
                nom VARCHAR,
                telephone VARCHAR
              );""")
            
        if version < 34:
            cur.execute("""
              CREATE TABLE SITES(
                idx INTEGER PRIMARY KEY,
                nom VARCHAR
              );""")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD site INTEGER REFERENCES SITES(idx)")
            
        if version < 35:
            cur.execute("ALTER TABLE SITES ADD adresse VARCHAR;")
            cur.execute("ALTER TABLE SITES ADD code_postal INTEGER;")
            cur.execute("ALTER TABLE SITES ADD ville VARCHAR;")
            cur.execute("ALTER TABLE SITES ADD telephone VARCHAR;")
            cur.execute('UPDATE SITES SET adresse=?, code_postal=?, ville=?, telephone=?', ('','','',''))
            cur.execute("""  
              CREATE TABLE CONTRATS(
                idx INTEGER PRIMARY KEY,
                employe INTEGER REFERENCES EMPLOYES(idx),
                site INTEGER REFERENCES SITES(idx),
                debut DATE,
                fin DATE,
                fonction VARCHAR
              );""")
            cur.execute("ALTER TABLE EMPLOYES ADD diplomes VARCHAR;")
            cur.execute('UPDATE EMPLOYES SET diplomes=?', ('',))
            
        if version < 36:
            cur.execute("ALTER TABLE CRECHE ADD temps_facturation INTEGER;")
            cur.execute("UPDATE CRECHE SET temps_facturation=?;", (0,))
            
        if version < 37:
            cur.execute("ALTER TABLE CRECHE ADD conges_inscription INTEGER;")
            cur.execute("UPDATE CRECHE SET conges_inscription=?;", (0,))
            cur.execute("""
              CREATE TABLE CONGES_INSCRITS(
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                debut VARCHAR,
                fin VARCHAR,
                label VARCHAR
              );""")
                       
        if version < 38:
            cur.execute("ALTER TABLE SITES ADD capacite INTEGER;")
            cur.execute("UPDATE SITES SET capacite=?;", (0,))
            cur.execute("ALTER TABLE CRECHE ADD formule_taux_horaire VARCHAR;")
            cur.execute('SELECT forfait_horaire FROM CRECHE')
            forfait_horaire = cur.fetchall()[0][0] 
            if forfait_horaire == 0.0:
                cur.execute('UPDATE CRECHE SET formule_taux_horaire="None"')
            else:
                cur.execute("UPDATE CRECHE SET formule_taux_horaire=?;", ('[["", %f]]' % forfait_horaire,))

        if version < 39:
            parents = { }
            cur.execute('SELECT prenom, nom, idx FROM PARENTS;')
            for parent_prenom, parent_nom, parent_idx in cur.fetchall():
                parents[parent_idx] = parent_prenom + " " + parent_nom
            cur.execute("ALTER TABLE BUREAUX RENAME TO OLD;")
            cur.execute("""
              CREATE TABLE BUREAUX(
                idx INTEGER PRIMARY KEY,
                debut DATE,
                fin DATE,
                president VARCHAR,
                vice_president VARCHAR,
                tresorier VARCHAR,
                secretaire VARCHAR
              );""")
            cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire FROM OLD;')
            for idx, debut, fin, president, vice_president, tresorier, secretaire in cur.fetchall():
                president = parents.get(president, "")
                vice_president = parents.get(vice_president, "")
                tresorier = parents.get(tresorier, "")
                secretaire = parents.get(secretaire, "")                
                cur.execute('INSERT INTO BUREAUX (idx, debut, fin, president, vice_president, tresorier, secretaire) VALUES (NULL,?,?,?,?,?,?)', (debut, fin, president, vice_president, tresorier, secretaire))
            cur.execute('DROP TABLE OLD;')
            
        if version < 40:
            cur.execute("""  
              CREATE TABLE PROFESSEURS (
                idx INTEGER PRIMARY KEY,
                prenom VARCHAR,
                nom VARCHAR,
                entree DATE,
                sortie DATE
              );""")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD professeur INTEGER REFERENCES PROFESSEURS(idx);")
            
        if version < 41:
            cur.execute("ALTER TABLE BUREAUX ADD directeur VARCHAR;")          

        if version < 42:
            cur.execute("ALTER TABLE CRECHE ADD facturation_periode_adaptation INTEGER")
            cur.execute('UPDATE CRECHE SET facturation_periode_adaptation=?', (0,))
            cur.execute("ALTER TABLE INSCRIPTIONS ADD fin_periode_adaptation DATE")
            cur.execute('UPDATE INSCRIPTIONS SET fin_periode_adaptation=fin_periode_essai')
            
        if version < 43:
            cur.execute("ALTER TABLE INSCRITS ADD numero_securite_sociale VARCHAR")
            cur.execute("ALTER TABLE INSCRITS ADD numero_allocataire_caf VARCHAR")
            cur.execute("ALTER TABLE INSCRITS ADD handicap BOOLEAN")
            cur.execute('UPDATE INSCRITS SET numero_securite_sociale=""')
            cur.execute('UPDATE INSCRITS SET numero_allocataire_caf=""')
            cur.execute('UPDATE INSCRITS SET handicap=0')
            
        if version < 44:
            cur.execute("ALTER TABLE PARENTS ADD relation VARCHAR;")
            cur.execute('SELECT idx FROM INSCRITS')
            for inscrit_idx in cur.fetchall():
                cur.execute('SELECT idx FROM PARENTS WHERE inscrit=?', (inscrit_idx[0],))
                papa_idx, maman_idx = cur.fetchall()
                cur.execute('UPDATE PARENTS SET relation=? WHERE idx=?', ("papa", papa_idx[0]))
                cur.execute('UPDATE PARENTS SET relation=? WHERE idx=?', ("maman", maman_idx[0]))
                
        if version < 45:
            cur.execute("ALTER TABLE INSCRITS ADD notes VARCHAR;")
            cur.execute('UPDATE INSCRITS SET notes=?', ("",))
            cur.execute("ALTER TABLE INSCRITS ADD notes_parents VARCHAR;")
            cur.execute('UPDATE INSCRITS SET notes_parents=?', ("",))
            cur.execute("""  
              CREATE TABLE ALERTES (
                idx INTEGER PRIMARY KEY,
                texte VARCHAR,
                date DATE,
                acquittement BOOLEAN
              );""")
            
        if version < 46:
            cur.execute("ALTER TABLE CRECHE ADD gestion_alertes BOOLEAN")
            cur.execute('UPDATE CRECHE SET gestion_alertes=?', (False,))
            cur.execute("ALTER TABLE CRECHE ADD preinscriptions BOOLEAN")
            cur.execute('UPDATE CRECHE SET preinscriptions=?', (False,))
            cur.execute("ALTER TABLE INSCRIPTIONS ADD sites_preinscription VARCHAR")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD preinscription BOOLEAN")
            cur.execute("UPDATE INSCRIPTIONS SET preinscription=?", (False,))
        
        if version < 47:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD forfait_mensuel FLOAT")
            cur.execute("UPDATE INSCRIPTIONS SET forfait_mensuel=?", (.0,))
            
        if version < VERSION:
            try:
                cur.execute("DELETE FROM DATA WHERE key=?", ("VERSION", ))
            except sqlite3.OperationalError:
                pass

            cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
            cur.execute("VACUUM")

            self.commit()

        return True
