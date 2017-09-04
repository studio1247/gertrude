# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime, __builtin__
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
from functions import *
from sqlobjects import *
from facture import FactureCloturee
import wx
import bcrypt

VERSION = 108


def getdate(s):
    try:
        annee, mois, jour = map(lambda x: int(x), s.split('-'))
        return datetime.date(annee, mois, jour)
    except:
        return None


class SQLConnection(object):
    def __init__(self, filename):
        self.filename = filename
        self.con = None

    def open(self, autosave=False):
        print "Open database %r" % self.filename
        if autosave:
            self.con = sqlite3.connect(self.filename, isolation_level=None)
        else:
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

        progress_handler.display("Création d'une nouvelle base ...")

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
            preinscriptions BOOLEAN,
            presences_previsionnelles BOOLEAN,
            presences_supplementaires BOOLEAN,
            modes_inscription INTEGER,
            minimum_maladie INTEGER,
            email VARCHAR,
            type INTEGER,
            mode_saisie_planning INTEGER,
            periode_revenus INTEGER,
            mode_facturation INTEGER,
            temps_facturation INTEGER,
            repartition INTEGER,
            conges_inscription INTEGER,
            tarification_activites INTEGER,
            traitement_maladie INTEGER,
            facturation_jours_feries INTEGER,
            facturation_periode_adaptation INTEGER,
            formule_taux_effort VARCHAR,
            masque_alertes INTEGER,
            age_maximum INTEGER,
            seuil_alerte_inscription INTEGER,
            cloture_facturation INTEGER,
            arrondi_heures INTEGER,
            arrondi_facturation INTEGER,
            arrondi_facturation_periode_adaptation INTEGER,
            arrondi_mensualisation INTEGER,
            arrondi_heures_salaries INTEGER,
            arrondi_mensualisation_euros INTEGER,
            arrondi_semaines INTEGER,
            gestion_maladie_hospitalisation BOOLEAN,
            tri_inscriptions INTEGER,
            tri_planning INTEGER,
            tri_factures INTEGER,
            smtp_server VARCHAR,
            caf_email VARCHAR,
            mode_accueil_defaut INTEGER,
            gestion_absences_non_prevenues BOOLEAN,
            gestion_maladie_sans_justificatif BOOLEAN,
            gestion_preavis_conges BOOLEAN,
            gestion_depart_anticipe BOOLEAN,
            alerte_depassement_planning BOOLEAN,
            last_tablette_synchro VARCHAR,
            changement_groupe_auto BOOLEAN,
            allergies VARCHAR,
            regularisation_fin_contrat BOOLEAN,
            date_raz_permanences DATE,
            conges_payes_salaries INTEGER,
            conges_supplementaires_salaries INTEGER,
            cout_journalier FLOAT,
            iban VARCHAR,
            bic VARCHAR,
            creditor_id VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE SITES(
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            telephone VARCHAR,
            capacite INTEGER,
            groupe INTEGER
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
            directeur VARCHAR,
            gerant VARCHAR,
            directeur_adjoint VARCHAR,
            comptable VARCHAR
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
          CREATE TABLE TARIFS_HORAIRES(
            idx INTEGER PRIMARY KEY,
            debut DATE,
            fin DATE,
            formule VARCHAR
          );""")

        cur.execute("""  
          CREATE TABLE RESERVATAIRES (
            idx INTEGER PRIMARY KEY,
            debut DATE,
            fin DATE,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            telephone VARCHAR,
            email VARCHAR,
            places INTEGER,
            heures_jour FLOAT,
            heures_semaine FLOAT,
            options INTEGER,
            periode_facturation INTEGER,
            delai_paiement INTEGER,
            tarif FLOAT
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
            formule_tarif VARCHAR,
            owner INTEGER
          );""")

        cur.execute("""  
          CREATE TABLE CONTRATS(
            idx INTEGER PRIMARY KEY,
            employe INTEGER REFERENCES EMPLOYES(idx),
            site INTEGER REFERENCES SITES(idx),
            debut DATE,
            fin DATE,
            fonction VARCHAR,
            duree_reference INTEGER
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
            diplomes VARCHAR,
            combinaison VARCHAR
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
          CREATE TABLE FAMILLES(
            idx INTEGER PRIMARY KEY,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
            numero_securite_sociale VARCHAR,
            numero_allocataire_caf VARCHAR,
            medecin_traitant VARCHAR,
            telephone_medecin_traitant VARCHAR,
            assureur VARCHAR,
            numero_police_assurance VARCHAR,
            code_client VARCHAR,
            tarifs INTEGER,
            notes VARCHAR,
            iban VARCHAR,
            bic VARCHAR,
            mandate_id VARCHAR,
            jour_prelevement_automatique INTEGER,
            date_premier_prelevement_automatique DATE
          );""")

        cur.execute("""
          CREATE TABLE INSCRITS(
            idx INTEGER PRIMARY KEY,
            prenom VARCHAR,
            nom VARCHAR,
            sexe INTEGER,
            naissance DATE,
            handicap BOOLEAN,
            marche BOOLEAN,
            photo VARCHAR,
            notes VARCHAR,
            combinaison VARCHAR,
            categorie INTEGER REFERENCES CATEGORIES(idx),
            allergies VARCHAR,
            famille INTEGER REFERENCES FAMILLES(idx)
          );""")

        cur.execute("""
          CREATE TABLE PARENTS(
            idx INTEGER PRIMARY KEY,
            famille INTEGER REFERENCES FAMILLES(idx),
            relation VARCHAR,
            prenom VARCHAR,
            nom VARCHAR,
            adresse VARCHAR,
            code_postal INTEGER,
            ville VARCHAR,
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
            famille INTEGER REFERENCES FAMILLES(idx),
            prenom VARCHAR,
            naissance DATE,
            entree DATE,
            sortie DATE
          );""")

        cur.execute("""  
          CREATE TABLE REFERENTS (
            idx INTEGER PRIMARY KEY,
            famille INTEGER REFERENCES FAMILLES(idx),
            prenom VARCHAR,
            nom VARCHAR,
            telephone VARCHAR
          );""")

        cur.execute("""  
          CREATE TABLE INSCRIPTIONS(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            preinscription BOOLEAN,
            reservataire INTEGER REFERENCES RESERVATAIRES(idx),
            groupe INTEGER REFERENCES GROUPES(idx),
            forfait_mensuel FLOAT,
            frais_inscription FLOAT,
            allocation_mensuelle_caf FLOAT,
            site INTEGER REFERENCES SITES(idx),
            sites_preinscription VARCHAR,
            professeur INTEGER REFERENCES PROFESSEURS(idx),
            debut DATE,
            fin DATE,
            depart DATE,
            mode, INTEGER,
            fin_periode_adaptation DATE,
            duree_reference INTEGER,
            forfait_mensuel_heures FLOAT,
            semaines_conges INTEGER,
            heures_permanences FLOAT,
            newsletters INTEGER
          );""")

        cur.execute("""
          CREATE TABLE CAPACITE(
            idx INTEGER PRIMARY KEY,
            value INTEGER,
            debut INTEGER,
            fin INTEGER,
            jour INTEGER
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
          CREATE TABLE REF_JOURNEES_SALARIES(
            idx INTEGER PRIMARY KEY,
            reference INTEGER REFERENCES CONTRATS(idx),
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
            conge_parental BOOLEAN,
            regime INTEGER
          );""")

        cur.execute("""
          CREATE TABLE COMMENTAIRES(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            commentaire VARCHAR
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
          CREATE TABLE PLANNING_HEBDOMADAIRE(
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            activity INTEGER,
            value FLOAT
          );""")

        cur.execute("""
          CREATE TABLE ACTIVITES_SALARIES(
            idx INTEGER PRIMARY KEY,
            salarie INTEGER REFERENCES EMPLOYES(idx),
            date DATE,
            value INTEGER,
            debut INTEGER,
            fin INTEGER
          );""")

        cur.execute("""
          CREATE TABLE COMMENTAIRES_SALARIES(
            idx INTEGER PRIMARY KEY,
            salarie INTEGER REFERENCES SALARIES(idx),
            date DATE,
            commentaire VARCHAR
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
          CREATE TABLE CONGES_SALARIES(
            idx INTEGER PRIMARY KEY,
            salarie INTEGER REFERENCES EMPLOYES(idx),
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

        cur.execute("""
          CREATE TABLE CHARGES (
            idx INTEGER PRIMARY KEY,
            date DATE,
            charges FLOAT
          );""")

        cur.execute("""
          CREATE TABLE FACTURES (
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            cotisation_mensuelle FLOAT,
            total_contractualise FLOAT,
            total_realise FLOAT,
            total_facture FLOAT,
            supplement_activites FLOAT,
            supplement FLOAT,
            deduction FLOAT
          );""")

        cur.execute("""
          CREATE TABLE ENCAISSEMENTS (
            idx INTEGER PRIMARY KEY,
            famille INTEGER REFERENCES FAMILLES(idx),
            date DATE,
            valeur FLOAT,
            moyen_paiement INTEGER
          );""")

        cur.execute("""
          CREATE TABLE NUMEROS_FACTURE (
            idx INTEGER PRIMARY KEY,
            date DATE,
            valeur INTEGER
          );""")

        cur.execute("""
          CREATE TABLE CORRECTIONS (
            idx INTEGER PRIMARY KEY,
            inscrit INTEGER REFERENCES INSCRITS(idx),
            date DATE,
            valeur FLOAT,
            libelle VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE GROUPES (
            idx INTEGER PRIMARY KEY,
            nom VARCHAR,
            ordre INTEGER,
            age_maximum INTEGER
          );""")

        cur.execute("""
          CREATE TABLE CATEGORIES (
            idx INTEGER PRIMARY KEY,
            nom VARCHAR
          );""")

        cur.execute("""
          CREATE TABLE TARIFSSPECIAUX (
            idx INTEGER PRIMARY KEY,
            label VARCHAR,
            type INTEGER,
            unite INTEGER,
            valeur FLOAT
          );""")

        cur.execute("""
          CREATE TABLE PLAGESHORAIRES (
            idx INTEGER PRIMARY KEY,
            debut FLOAT,
            fin FLOAT,
            flags INTEGER
          );""")

        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
            cur.execute("INSERT INTO CONGES (idx, debut) VALUES (NULL, ?)", (label, ))
        cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
        cur.execute('INSERT INTO CRECHE(idx, nom, adresse, code_postal, ville, telephone, ouverture, fermeture, affichage_min, affichage_max, granularite, preinscriptions, presences_previsionnelles, presences_supplementaires, modes_inscription,                         minimum_maladie, email, type,          mode_saisie_planning, periode_revenus, mode_facturation, temps_facturation,    repartition,                       conges_inscription, tarification_activites, traitement_maladie,                          facturation_jours_feries,      facturation_periode_adaptation,          formule_taux_effort, masque_alertes, age_maximum, seuil_alerte_inscription, cloture_facturation, arrondi_heures, arrondi_facturation, arrondi_facturation_periode_adaptation, arrondi_mensualisation,    arrondi_heures_salaries, arrondi_mensualisation_euros, arrondi_semaines,           gestion_maladie_hospitalisation, tri_inscriptions, tri_planning, tri_factures, smtp_server, caf_email, mode_accueil_defaut, gestion_absences_non_prevenues, gestion_maladie_sans_justificatif, gestion_preavis_conges, gestion_depart_anticipe, alerte_depassement_planning, last_tablette_synchro, changement_groupe_auto, allergies, regularisation_fin_contrat, date_raz_permanences, conges_payes_salaries, conges_supplementaires_salaries, cout_journalier) VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                   (                         "",  "",      "",          "",    "",        7.75,      18.5,      7.75,          19.0,          15,          False,           False,                     True,                      MODE_HALTE_GARDERIE + MODE_4_5 + MODE_3_5, 3,               "",    TYPE_PARENTAL, SAISIE_HORAIRE,       REVENUS_YM2,     FACTURATION_PSU,  FACTURATION_FIN_MOIS, REPARTITION_MENSUALISATION_12MOIS, 0,                  0,                      DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES, ABSENCES_DEDUITES_EN_SEMAINES, PERIODE_ADAPTATION_FACTUREE_NORMALEMENT, "None",              0,              3,           3,                        0,                   SANS_ARRONDI,   SANS_ARRONDI,        SANS_ARRONDI,                           ARRONDI_HEURE_PLUS_PROCHE, SANS_ARRONDI,            SANS_ARRONDI,                 ARRONDI_SEMAINE_SUPERIEURE, False,                           TRI_NOM,          TRI_NOM,      TRI_NOM,      "",          "",        0,                   False,                          False,                             False,                  False,                   False,                       "",                    False,                  "",        True,                       None,                 25,                    0,                               0.0))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2006, 9, 1), datetime.date(2007, 8, 31),  6547.92, 51723.60))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2007, 9, 1), datetime.date(2008, 12, 31), 6660.00, 52608.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2009, 1, 1), datetime.date(2009, 12, 31), 6876.00, 53400.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2010, 1, 1), datetime.date(2010, 12, 31), 6956.64, 54895.20))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2011, 1, 1), datetime.date(2011, 12, 31), 7060.92, 85740.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2012, 1, 1), datetime.date(2012, 12, 31), 7181.04, 85740.00))
        cur.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (datetime.date(2013, 1, 1), datetime.date(2013, 12, 31), 7306.56, 85740.00))

        couleur = [5, 203, 28, 150, wx.SOLID]
        couleur_supplement = [5, 203, 28, 250, wx.SOLID]
        couleur_previsionnel = [5, 203, 28, 50, wx.SOLID]
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)', ("Présences", 0, 0, str(couleur), str(couleur_supplement), str(couleur_previsionnel), ""))
        vacances = (0, 0, 255, 150, wx.SOLID)
        malade = (190, 35, 29, 150, wx.SOLID)
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)', ("Vacances", -1, 0, str(vacances), str(vacances), str(vacances), ""))
        cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)', ("Malade", -2, 0, str(malade), str(malade), str(malade), ""))

        self.con.commit()

    def Liste(self):
        con = sqlite3.connect(self.filename)
        cur = con.cursor()
        cur.execute('SELECT prenom, nom FROM INSCRITS WHERE prenom != "" AND nom != ""')
        return ["%s %s" % entry for entry in cur.fetchall()]

    def decloture(self):
        cur = self.cursor()
        cur.execute('DELETE FROM FACTURES where inscrit=? AND date=?', (76, datetime.date(2016, 11, 1)))
        # cur.execute('DELETE FROM FACTURES where date=?', (datetime.date(2016, 12, 1), ))
        # cur.execute('UPDATE INSCRIPTIONS SET debut=?, fin=?', (datetime.date(2017, 1, 1), datetime.date(2017, 12, 31)))
        self.commit()
        print "Facture déclôturée"

    def remove_all_inscrits(self):
        cur = self.cursor()
        cur.execute('DELETE FROM INSCRITS')
        cur.execute('DELETE FROM FAMILLES')
        cur.execute('DELETE FROM PARENTS')
        cur.execute('DELETE FROM REVENUS')
        cur.execute('DELETE FROM COMMENTAIRES')
        cur.execute('DELETE FROM REFERENTS')
        cur.execute('DELETE FROM FRATRIES')
        cur.execute('DELETE FROM INSCRIPTIONS')
        cur.execute('DELETE FROM REF_ACTIVITIES')
        cur.execute('DELETE FROM EMPLOYES')
        cur.execute('DELETE FROM CONTRATS')
        cur.execute('DELETE FROM REF_JOURNEES_SALARIES')
        cur.execute('DELETE FROM PROFESSEURS')
        cur.execute('DELETE FROM CONGES_INSCRITS')
        cur.execute('DELETE FROM CONGES_SALARIES')
        cur.execute('DELETE FROM ALERTES')
        cur.execute('DELETE FROM FACTURES')
        cur.execute('DELETE FROM CORRECTIONS')
        cur.execute('DELETE FROM ENCAISSEMENTS')
        cur.execute('DELETE FROM ACTIVITES')
        cur.execute('DELETE FROM ACTIVITES_SALARIES')
        cur.execute('DELETE FROM PLANNING_HEBDOMADAIRE')
        cur.execute('DELETE FROM NUMEROS_FACTURE')
        self.commit()

    def Load(self, progress_handler=default_progress_handler, autosave=False):
        if not self.con:
            self.open(autosave=autosave)

        # pour decloturer une facture dans une base plus ancienne
        if 0:
            self.decloture()
            exit(0)

        # pour supprimer toutes les inscriptions
        if 0:
            self.remove_all_inscrits()
            exit(0)

        if not self.translate(progress_handler):
            return None

        if progress_handler:
            progress_handler.display("Chargement en mémoire de la base ...")

        cur = self.cursor()

        cur.execute('SELECT nom, adresse, code_postal, ville, telephone, ouverture, fermeture, affichage_min, affichage_max, granularite, preinscriptions, presences_previsionnelles, presences_supplementaires, modes_inscription, minimum_maladie, email, type, mode_saisie_planning, periode_revenus, mode_facturation, repartition, temps_facturation, conges_inscription, tarification_activites, traitement_maladie, facturation_jours_feries, facturation_periode_adaptation, formule_taux_effort, masque_alertes, age_maximum, seuil_alerte_inscription, cloture_facturation, arrondi_heures, arrondi_facturation, arrondi_facturation_periode_adaptation, arrondi_mensualisation, arrondi_heures_salaries, arrondi_mensualisation_euros, arrondi_semaines, gestion_maladie_hospitalisation, tri_inscriptions, tri_planning, tri_factures, smtp_server, caf_email, mode_accueil_defaut, gestion_absences_non_prevenues, gestion_maladie_sans_justificatif, gestion_preavis_conges, gestion_depart_anticipe, alerte_depassement_planning, last_tablette_synchro, changement_groupe_auto, allergies, regularisation_fin_contrat, date_raz_permanences, conges_payes_salaries, conges_supplementaires_salaries, cout_journalier, iban, bic, creditor_id, idx FROM CRECHE')
        creche_entry = cur.fetchall()
        if len(creche_entry) > 0:
            creche = Creche()
            creche.nom, creche.adresse, creche.code_postal, creche.ville, creche.telephone, creche.ouverture, creche.fermeture, creche.affichage_min, creche.affichage_max, creche.granularite, creche.preinscriptions, creche.presences_previsionnelles, creche.presences_supplementaires, creche.modes_inscription, creche.minimum_maladie, creche.email, creche.type, creche.mode_saisie_planning, creche.periode_revenus, creche.mode_facturation, creche.repartition, creche.temps_facturation, creche.conges_inscription, creche.tarification_activites, creche.traitement_maladie, creche.facturation_jours_feries, creche.facturation_periode_adaptation, formule_taux_effort, creche.masque_alertes, creche.age_maximum, creche.seuil_alerte_inscription, creche.cloture_facturation, creche.arrondi_heures, creche.arrondi_facturation, creche.arrondi_facturation_periode_adaptation, creche.arrondi_mensualisation, creche.arrondi_heures_salaries, creche.arrondi_mensualisation_euros, creche.arrondi_semaines, creche.gestion_maladie_hospitalisation, creche.tri_inscriptions, creche.tri_planning, creche.tri_factures, creche.smtp_server, creche.caf_email, creche.mode_accueil_defaut, creche.gestion_absences_non_prevenues, creche.gestion_maladie_sans_justificatif, creche.gestion_preavis_conges, creche.gestion_depart_anticipe, creche.alerte_depassement_planning, creche.last_tablette_synchro, creche.changement_groupe_auto, creche.allergies, creche.regularisation_fin_contrat, creche.date_raz_permanences, creche.conges_payes_salaries, creche.conges_supplementaires_salaries, creche.cout_journalier, creche.iban, creche.bic, creditor_id, idx = creche_entry[0]
            creche.formule_taux_effort, creche.date_raz_permanences, creche.idx = eval(formule_taux_effort), getdate(creche.date_raz_permanences), idx
        else:
            creche = Creche()
        creche.UpdateFormuleTauxEffort(changed=False)

        cur.execute('SELECT nom, ordre, age_maximum, idx from GROUPES')
        for groupe_entry in cur.fetchall():
            groupe = Groupe(creation=False)
            groupe.nom, groupe.ordre, groupe.age_maximum, groupe.idx = groupe_entry
            creche.groupes.append(groupe)

        cur.execute('SELECT nom, idx from CATEGORIES')
        for categorie_entry in cur.fetchall():
            categorie = Categorie(creation=False)
            categorie.nom, categorie.idx = categorie_entry
            creche.categories.append(categorie)

        cur.execute('SELECT value, debut, fin, jour, idx FROM CAPACITE')
        for value, debut, fin, jour, idx in cur.fetchall():
            try:
                creche.tranches_capacite[jour].AddActivity(debut, fin, value, idx)
            except:
                print "TODO"

        cur.execute('SELECT nom, adresse, code_postal, ville, telephone, capacite, groupe, idx FROM SITES')
        for site_entry in cur.fetchall():
            site = Site(creation=False)
            site.nom, site.adresse, site.code_postal, site.ville, site.telephone, site.capacite, site.groupe, site.idx = site_entry
            creche.sites.append(site)

        cur.execute('SELECT login, password, profile, idx FROM USERS')
        for users_entry in cur.fetchall():
            user = User(creation=False)
            user.login, user.password, user.profile, user.idx = users_entry
            # print user.login, user.password
            creche.users.append(user)

        cur.execute('SELECT debut, fin, nom, adresse, code_postal, ville, telephone, email, places, heures_jour, heures_semaine, options, periode_facturation, tarif, delai_paiement, idx FROM RESERVATAIRES')
        for reservataire_entry in cur.fetchall():
            reservataire = Reservataire(creation=False)
            debut, fin, reservataire.nom, reservataire.adresse, reservataire.code_postal, reservataire.ville, reservataire.telephone, reservataire.email, reservataire.places, reservataire.heures_jour, reservataire.heures_semaine, reservataire.options, reservataire.periode_facturation, reservataire.tarif, reservataire.delai_paiement, idx = reservataire_entry
            reservataire.debut, reservataire.fin, reservataire.idx = getdate(debut), getdate(fin), idx
            creche.reservataires.append(reservataire)

        cur.execute('SELECT label, type, unite, valeur, idx FROM TARIFSSPECIAUX')
        for tarifs_entry in cur.fetchall():
            tarif = TarifSpecial(creation=False)
            tarif.label, tarif.type, tarif.unite, tarif.valeur, tarif.idx = tarifs_entry
            creche.tarifs_speciaux.append(tarif)

        cur.execute('SELECT debut, fin, flags, idx FROM PLAGESHORAIRES')
        for plages_entry in cur.fetchall():
            plage = PlageHoraire(creation=False)
            plage.debut, plage.fin, plage.flags, plage.idx = plages_entry
            creche.plages_horaires.append(plage)

        cur.execute('SELECT debut, fin, label, options, idx FROM CONGES')
        for conges_entry in cur.fetchall():
            conge = Conge(creche, creation=False)
            conge.debut, conge.fin, conge.label, conge.options, conge.idx = conges_entry
            creche.AddConge(conge, calcule=False)
        creche.CalculeJoursConges()

        cur.execute('SELECT debut, fin, plancher, plafond, idx FROM BAREMESCAF')
        for bareme_entry in cur.fetchall():
            bareme = BaremeCAF(creation=False)
            bareme.debut, bareme.fin, bareme.plancher, bareme.plafond, idx = bareme_entry
            bareme.debut, bareme.fin, bareme.idx = getdate(bareme.debut), getdate(bareme.fin), idx
            creche.baremes_caf.append(bareme)

        cur.execute('SELECT debut, fin, formule, idx FROM TARIFS_HORAIRES')
        for tarif_entry in cur.fetchall():
            tarif = TarifHoraire(creation=False)
            tarif.debut, tarif.fin, tarif.formule, idx = tarif_entry
            tarif.debut, tarif.fin, tarif.formule, tarif.idx = getdate(tarif.debut), getdate(tarif.fin), eval(tarif.formule), idx
            tarif.UpdateFormule(changed=False)
            creche.tarifs_horaires.append(tarif)

        cur.execute('SELECT date, charges, idx FROM CHARGES')
        for charges_entry in cur.fetchall():
            charges = Charges(creation=False)
            date, charges.charges, idx = charges_entry
            charges.date, charges.idx = getdate(date), idx
            creche.charges[charges.date] = charges

        cur.execute('SELECT label, value, mode, couleur, couleur_supplement, couleur_previsionnel, formule_tarif, owner, idx FROM ACTIVITIES')
        for entry in cur.fetchall():
            activity = Activite(creation=False)
            activity.label, activity.value, activity.mode, activity.couleur, activity.couleur_supplement, activity.couleur_previsionnel, activity.formule_tarif, activity.owner, activity.idx = entry
            if activity.value < 0:
                creche.couleurs[activity.value] = activity
            else:
                creche.activites[activity.value] = activity

        cur.execute('SELECT prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, email, diplomes, combinaison, idx FROM EMPLOYES')
        for salarie_entry in cur.fetchall():
            salarie = Salarie(creation=False)
            salarie.prenom, salarie.nom, salarie.telephone_domicile, salarie.telephone_domicile_notes, salarie.telephone_portable, salarie.telephone_portable_notes, salarie.email, salarie.diplomes, salarie.combinaison, salarie.idx = salarie_entry
            creche.salaries.append(salarie)
            cur.execute('SELECT debut, fin, site, fonction, duree_reference, idx FROM CONTRATS WHERE employe=?', (salarie.idx,))
            for debut, fin, site_idx, fonction, duree_reference, idx in cur.fetchall():
                contrat = Contrat(salarie, duree_reference, creation=False)
                site = None
                for s in creche.sites:
                    if s.idx == site_idx:
                        site = s
                        break
                contrat.debut, contrat.fin, contrat.site, contrat.fonction, contrat.idx = getdate(debut), getdate(fin), site, fonction, idx
                salarie.contrats.append(contrat)

            for contrat in salarie.contrats:
                cur.execute('SELECT day, value, debut, fin, idx FROM REF_JOURNEES_SALARIES WHERE reference=?', (contrat.idx,))
                for day, value, debut, fin, idx in cur.fetchall():
                    if value in creche.activites and day < len(contrat.reference):
                        reference_day = contrat.reference[day]
                        reference_day.AddActivity(debut, fin, value, idx)
                        # print inscrit.prenom, inscrit.prenom, day, debut, fin, value

            cur.execute('SELECT date, value, debut, fin, idx FROM ACTIVITES_SALARIES WHERE salarie=? AND date>=?', (salarie.idx, config.first_date))
            for date, value, debut, fin, idx in cur.fetchall():
                key = getdate(date)
                if key in salarie.journees:
                    journee = salarie.journees[key]
                else:
                    journee = JourneeSalarie(salarie, key)
                    salarie.journees[key] = journee
                # print salarie.prenom, salarie.nom, key, debut, fin, value
                journee.AddActivity(debut, fin, value, idx)

            cur.execute('SELECT date, commentaire, idx FROM COMMENTAIRES_SALARIES WHERE salarie=?', (salarie.idx,))
            for date, commentaire, idx in cur.fetchall():
                key = getdate(date)
                if key in salarie.journees:
                    journee = salarie.journees[key]
                else:
                    journee = JourneeSalarie(salarie, key)
                    salarie.journees[key] = journee
                journee.commentaire, journee.commentaire_idx = commentaire, idx

            cur.execute('SELECT debut, fin, label, idx FROM CONGES_SALARIES WHERE salarie=?', (salarie.idx,))
            for conges_entry in cur.fetchall():
                conge = CongeSalarie(salarie, creation=False)
                conge.debut, conge.fin, conge.label, conge.idx = conges_entry
                salarie.conges.append(conge)
            salarie.CalculeJoursConges(creche)

        cur.execute('SELECT prenom, nom, entree, sortie, idx FROM PROFESSEURS')
        for professeur_entry in cur.fetchall():
            professeur = Professeur(creation=False)
            professeur.prenom, professeur.nom, professeur.entree, professeur.sortie, idx = professeur_entry
            professeur.entree = getdate(professeur.entree)
            professeur.sortie = getdate(professeur.sortie)
            professeur.idx = idx
            creche.professeurs.append(professeur)

        cur.execute('SELECT idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, code_client, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, code_client, tarifs, notes, iban, bic, mandate_id, jour_prelevement_automatique, date_premier_prelevement_automatique FROM FAMILLES')
        for idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, code_client, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, code_client, tarifs, notes, iban, bic, mandate_id, jour_prelevement_automatique, date_premier_prelevement_automatique in cur.fetchall():
            famille = Famille(creation=False)
            famille.adresse, famille.code_postal, famille.ville, famille.numero_securite_sociale, famille.numero_allocataire_caf, famille.code_client, famille.medecin_traitant, famille.telephone_medecin_traitant, famille.assureur, famille.numero_police_assurance, famille.code_client, famille.tarifs, famille.notes, famille.iban, famille.bic, famille.mandate_id, famille.jour_prelevement_automatique, famille.date_premier_prelevement_automatique, famille.idx = adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, code_client, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, code_client, tarifs, notes, iban, bic, mandate_id, jour_prelevement_automatique, getdate(date_premier_prelevement_automatique), idx
            creche.familles.append(famille)
            cur.execute('SELECT relation, prenom, nom, adresse, code_postal, ville, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email, idx FROM PARENTS WHERE famille=?', (famille.idx,))
            for i, parent_entry in enumerate(cur.fetchall()):
                parent = Parent(famille, creation=False)
                parent.relation, parent.prenom, parent.nom, parent.adresse, parent.code_postal, parent.ville, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email, parent.idx = parent_entry
                if i < 2:
                    famille.parents[i] = parent
                else:
                    print "Famille avec plus de 2 parents : fonction non supportée"
                    continue
                cur.execute('SELECT debut, fin, revenu, chomage, conge_parental, regime, idx FROM REVENUS WHERE parent=?', (parent.idx,))
                for revenu_entry in cur.fetchall():
                    revenu = Revenu(parent, creation=False)
                    revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.conge_parental, revenu.regime, idx = revenu_entry
                    revenu.debut, revenu.fin, revenu.idx = getdate(revenu.debut), getdate(revenu.fin), idx
                    if 0:
                        # convertit N-2 en CAFPRO
                        if revenu.debut:
                            revenu.debut = datetime.date(revenu.debut.year+2, revenu.debut.month, revenu.debut.day)
                        if revenu.fin:
                            revenu.fin = datetime.date(revenu.fin.year+2, revenu.fin.month, revenu.fin.day)
                    parent.revenus.append(revenu)
            cur.execute('SELECT prenom, naissance, entree, sortie, idx FROM FRATRIES WHERE famille=?', (famille.idx,))
            for frere_entry in cur.fetchall():
                frere = Frere_Soeur(famille, creation=False)
                frere.prenom, frere.naissance, frere.entree, frere.sortie, idx = frere_entry
                frere.naissance, frere.entree, frere.sortie, frere.idx = getdate(frere.naissance), getdate(frere.entree), getdate(frere.sortie), idx
                famille.freres_soeurs.append(frere)
            cur.execute('SELECT prenom, nom, telephone, idx FROM REFERENTS WHERE famille=?', (famille.idx,))
            for referent_entry in cur.fetchall():
                referent = Referent(famille, creation=False)
                referent.prenom, referent.nom, referent.telephone, referent.idx = referent_entry
                famille.referents.append(referent)
            cur.execute('SELECT idx, date, valeur, moyen_paiement FROM ENCAISSEMENTS where famille=?', (famille.idx,))
            for idx, date, valeur, moyen_paiement in cur.fetchall():
                date = getdate(date)
                famille.encaissements.append(Encaissement(famille, date, valeur, moyen_paiement, idx))

        cur.execute('SELECT idx, prenom, nom, sexe, naissance, handicap, marche, notes, photo, combinaison, categorie, allergies, famille FROM INSCRITS')
        for idx, prenom, nom, sexe, naissance, handicap, marche, notes, photo, combinaison, categorie, allergies, famille in cur.fetchall():
            # print idx, prenom, nom, naissance
            if photo:
                photo = binascii.a2b_base64(photo)
            inscrit = Inscrit(creation=False)
            creche.inscrits.append(inscrit)
            for tmp in creche.categories:
                if categorie == tmp.idx:
                    inscrit.categorie = tmp
                    break
            for tmp in creche.familles:
                if famille == tmp.idx:
                    inscrit.famille = tmp
                    break
            inscrit.prenom, inscrit.nom, inscrit.sexe, inscrit.naissance, inscrit.handicap, inscrit.marche, inscrit.notes, inscrit.photo, inscrit.combinaison, inscrit.allergies, inscrit.idx = prenom, nom, sexe, getdate(naissance), handicap, getdate(marche), notes, photo, combinaison, allergies, idx
            cur.execute('SELECT idx, debut, fin, depart, mode, reservataire, groupe, forfait_mensuel, frais_inscription, allocation_mensuelle_caf, fin_periode_adaptation, duree_reference, forfait_mensuel_heures, semaines_conges, heures_permanences, preinscription, site, sites_preinscription, professeur, newsletters FROM INSCRIPTIONS WHERE inscrit=?', (inscrit.idx,))
            for idx, debut, fin, depart, mode, reservataire, groupe, forfait_mensuel, frais_inscription, allocation_mensuelle_caf, fin_periode_adaptation, duree_reference, forfait_mensuel_heures, semaines_conges, heures_permanences, preinscription, site, sites_preinscription, professeur, newsletters in cur.fetchall():
                inscription = Inscription(inscrit, duree_reference, creation=False)
                for tmp in creche.sites:
                    if site == tmp.idx:
                        inscription.site = tmp
                for tmp in creche.groupes:
                    if groupe == tmp.idx:
                        inscription.groupe = tmp
                for tmp in creche.reservataires:
                    if reservataire == tmp.idx:
                        inscription.reservataire = tmp
                if sites_preinscription:
                    for site_preinscription in sites_preinscription.split():
                        site_preinscription = int(site_preinscription)
                        for tmp in creche.sites:
                            if site_preinscription == tmp.idx:
                                inscription.sites_preinscription.append(tmp)
                for tmp in creche.professeurs:
                    if professeur == tmp.idx:
                        inscription.professeur = tmp
                inscription.debut, inscription.fin, inscription.depart, inscription.mode, inscription.preinscription, inscription.forfait_mensuel_heures, inscription.forfait_mensuel, inscription.frais_inscription, inscription.allocation_mensuelle_caf, inscription.fin_periode_adaptation, inscription.semaines_conges, inscription.heures_permanences, inscription.newsletters, inscription.idx = getdate(debut), getdate(fin), getdate(depart), mode, preinscription, forfait_mensuel_heures, forfait_mensuel, frais_inscription, allocation_mensuelle_caf, getdate(fin_periode_adaptation), semaines_conges, heures_permanences, newsletters, idx
                inscrit.inscriptions.append(inscription)
                inscrit.inscriptions.sort(key=lambda element: element.debut if element.debut else today)
            for inscription in inscrit.inscriptions:
                cur.execute('SELECT day, value, debut, fin, idx FROM REF_ACTIVITIES WHERE reference=?', (inscription.idx,))
                for day, value, debut, fin, idx in cur.fetchall():
                    if value <= 0 or (value & 0xffff) in creche.activites:
                        try:
                            reference_day = inscription.reference[day]
                            reference_day.AddActivity(debut, fin, value, idx)
                        except Exception, e:
                            print inscrit.prenom, inscrit.nom, day, debut, fin, value, e
                    # print inscrit.prenom, day, debut, fin, value
            cur.execute('SELECT debut, fin, label, idx FROM CONGES_INSCRITS WHERE inscrit=?', (inscrit.idx,))
            for conges_entry in cur.fetchall():
                conge = CongeInscrit(inscrit, creation=False)
                conge.debut, conge.fin, conge.label, conge.idx = conges_entry
                inscrit.conges.append(conge)
            inscrit.CalculeJoursConges(creche)

            cur.execute('SELECT date, value, debut, fin, idx FROM ACTIVITES WHERE inscrit=? AND date>=?', (inscrit.idx, config.first_date))
            for date, value, debut, fin, idx in cur.fetchall():
                key = getdate(date)
                if key in inscrit.journees:
                    journee = inscrit.journees[key]
                else:
                    journee = Journee(inscrit, key)
                    inscrit.journees[key] = journee
                # print inscrit.prenom, key, debut, fin, value
                if value <= 0 or (value & 0xffff) in creche.activites:
                    journee.AddActivity(debut, fin, value, idx)

            cur.execute('SELECT date, activity, value, idx FROM PLANNING_HEBDOMADAIRE WHERE inscrit=?', (inscrit.idx,))
            for date, activity, value,idx in cur.fetchall():
                key = getdate(date)
                if key in inscrit.semaines:
                    semaine = inscrit.semaines[key]
                else:
                    semaine = WeekPlanning(inscrit, date)
                    inscrit.semaines[key] = semaine
                # print inscrit.prenom, key, debut, fin, value
                semaine.SetActivity(activity, value, idx)

            cur.execute('SELECT date, commentaire, idx FROM COMMENTAIRES WHERE inscrit=?', (inscrit.idx,))
            for date, commentaire, idx in cur.fetchall():
                key = getdate(date)
                if key in inscrit.journees:
                    journee = inscrit.journees[key]
                else:
                    journee = Journee(inscrit, key)
                    inscrit.journees[key] = journee
                journee.commentaire, journee.commentaire_idx = commentaire, idx

            cur.execute('SELECT idx, date, cotisation_mensuelle, total_contractualise, total_realise, total_facture, supplement_activites, supplement, deduction FROM FACTURES where inscrit=?', (inscrit.idx,))
            for idx, date, cotisation_mensuelle, total_contractualise, total_realise, total_facture, supplement_activites, supplement, deduction in cur.fetchall():
                date = getdate(date)
                inscrit.factures_cloturees[date] = FactureCloturee(inscrit, date, cotisation_mensuelle, total_contractualise, total_realise, total_facture, supplement_activites, supplement, deduction)

            cur.execute('SELECT idx, date, valeur, libelle FROM CORRECTIONS where inscrit=?', (inscrit.idx,))
            for idx, date, valeur, libelle in cur.fetchall():
                date = getdate(date)
                inscrit.corrections[date] = Correction(inscrit, date, valeur, libelle, idx)

        cur.execute('SELECT idx, date, valeur FROM NUMEROS_FACTURE')
        for idx, date, valeur in cur.fetchall():
            date = getdate(date)
            creche.numeros_facture[date] = NumeroFacture(date, valeur, idx)

        cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire, directeur, gerant, directeur_adjoint, comptable FROM BUREAUX')
        for idx, debut, fin, president, vice_president, tresorier, secretaire, directeur, gerant, directeur_adjoint, comptable in cur.fetchall():
            bureau = Bureau(creation=False)
            bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire, bureau.directeur, bureau.gerant, bureau.directeur_adjoint, bureau.comptable, bureau.idx = getdate(debut), getdate(fin), president, vice_president, tresorier, secretaire, directeur, gerant, directeur_adjoint, comptable, idx
            creche.bureaux.append(bureau)

        cur.execute('SELECT idx, date, texte, acquittement FROM ALERTES')
        for idx, date, texte, acquittement in cur.fetchall():
            alerte = Alerte(getdate(date), texte, acquittement, creation=False)
            alerte.idx = idx
            creche.alertes[texte] = alerte

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
            progress_handler.display("Base de données plus récente que votre version de Gertrude (%d > %d) !" % (version, VERSION))
            return False

        if progress_handler:
            progress_handler.display("Conversion de la base de données (version %d => version %d) ..." % (version, VERSION))

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
            cur.execute("ALTER TABLE CRECHE ADD presences_previsionnelles BOOLEAN;")
            cur.execute("ALTER TABLE CRECHE ADD modes_inscription INTEGER;")
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
            cur.execute('UPDATE CRECHE SET email=?', ("",))

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
                        value += (1 << 30)  # PREVISIONNEL
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
                    day = JourneeReferenceInscription(inscription, weekday)
                    for i, tranche in enumerate(tranches):
                        debut, fin = tranche
                        if periode_reference[weekday][i]:
                            day.SetActivity(int(debut*12), int(fin*12), 0)

        if version < 19:
            cur.execute('UPDATE CRECHE SET modes_inscription=? WHERE modes_inscription=?', (1+2+4+8, 7))
            cur.execute('UPDATE CRECHE SET modes_inscription=? WHERE modes_inscription=?', (2, 0))
            cur.execute('UPDATE INSCRIPTIONS SET mode=? WHERE mode=?', (2, 0))

        if version < 20:
            for label in ["Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"]:
                cur.execute("INSERT INTO CONGES (idx, debut) VALUES (NULL, ?)", (label, ))

        if version < 21:
            if version >= 10:
                cur.execute('SELECT mode_maladie FROM CRECHE')
                mode_maladie = cur.fetchall()[0][0]
                if mode_maladie == 2:
                    mode_facturation = 2  # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
                else:
                    mode_facturation = 0
            else:
                mode_facturation = 2  # DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
            cur.execute("ALTER TABLE CRECHE ADD mode_facturation INTEGER;")
            cur.execute('UPDATE CRECHE SET mode_facturation=?', (mode_facturation,))

        if version < 22:
            cur.execute("ALTER TABLE CRECHE ADD type INTEGER;")
            cur.execute('UPDATE CRECHE SET type=?', (0,))
            cur.execute("ALTER TABLE CRECHE ADD telephone VARCHAR;")
            cur.execute('UPDATE CRECHE SET telephone=?', ("",))

        if 21 <= version < 23:
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
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', ("Présences", 0, 0, str(couleurs[0]), str(couleurs_supplement[0]), str(couleurs_previsionnel[0])))

        if version < 26:
            vacances = (0, 0, 255, 150, wx.SOLID)
            malade = (190, 35, 29, 150, wx.SOLID)
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', ("Vacances", -1, 0, str(vacances), str(vacances), str(vacances)))
            cur.execute('INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel) VALUES(NULL,?,?,?,?,?,?)', ("Malade", -2, 0, str(malade), str(malade), str(malade)))

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
            parents = {}
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

        if version < 48:
            cur.execute("UPDATE CONGES SET label='' WHERE label IS NULL")
            cur.execute("UPDATE CONGES_INSCRITS SET label='' WHERE label IS NULL")

        if version < 49:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD forfait_heures_presence INTEGER")
            cur.execute("UPDATE INSCRIPTIONS SET forfait_heures_presence=?", (0,))

        if version < 50:
            cur.execute("""
              CREATE TABLE CHARGES (
                idx INTEGER PRIMARY KEY,
                date DATE,
                charges FLOAT
              );""")

        if version < 51:
            cur.execute("ALTER TABLE CRECHE ADD formule_taux_effort VARCHAR;")
            cur.execute('UPDATE CRECHE SET formule_taux_effort="None"')

        if version < 52:
            cur.execute("""
              CREATE TABLE FACTURES (
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                date DATE,
                cotisation_mensuelle FLOAT,
                total_contractualise FLOAT,
                total_realise FLOAT,
                total_facture FLOAT,
                supplement_activites FLOAT,
                supplement FLOAT,
                deduction FLOAT
              );""")

        if version < 53:
            cur.execute("ALTER TABLE CRECHE ADD cloture_factures BOOLEAN")
            cur.execute('UPDATE CRECHE SET cloture_factures=?', (False,))

        if version < 54:
            cur.execute("""
              CREATE TABLE GROUPES (
                idx INTEGER PRIMARY KEY,
                nom VARCHAR
              );""")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD groupe INTEGER REFERENCES GROUPES(idx)")

        if version < 55:
            cur.execute("ALTER TABLE CRECHE ADD arrondi_heures INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_heures=?', (0,))

        if version < 56:
            cur.execute("ALTER TABLE CRECHE ADD gestion_maladie_hospitalisation BOOLEAN")
            cur.execute('UPDATE CRECHE SET gestion_maladie_hospitalisation=?', (False,))

        if version < 57:
            cur.execute("ALTER TABLE GROUPES ADD ordre INTEGER")
            cur.execute("SELECT idx FROM GROUPES")
            for i, idx in enumerate(cur.fetchall()):
                cur.execute('UPDATE GROUPES SET ordre=? WHERE idx=?', (i, idx[0]))

        if version < 58:
            cur.execute("ALTER TABLE CRECHE ADD tri_planning INTEGER")
            cur.execute('UPDATE CRECHE SET tri_planning=?', (TRI_NOM,))

        if version < 59:
            cur.execute("""
              CREATE TABLE TARIFSSPECIAUX (
                idx INTEGER PRIMARY KEY,
                label VARCHAR,
                reduction BOOLEAN,
                pourcentage BOOLEAN,
                valeur FLOAT
              );""")
            cur.execute("ALTER TABLE INSCRITS ADD tarifs INTEGER")
            cur.execute('UPDATE INSCRITS SET tarifs=0')
            cur.execute('SELECT majoration_localite FROM CRECHE')
            majoration = cur.fetchall()[0][0]
            if majoration:
                result = cur.execute('INSERT INTO TARIFSSPECIAUX (idx, label, reduction, pourcentage, valeur) VALUES (NULL,?,?,?,?)', ("Majoration (enfant hors localité)", False, False, majoration))
                cur.execute('UPDATE INSCRITS SET tarifs=? WHERE majoration=?', (1<<result.lastrowid, True))

        if version < 60:
            cur.execute("ALTER TABLE CRECHE ADD debut_pause FLOAT")
            cur.execute("ALTER TABLE CRECHE ADD fin_pause FLOAT")
            cur.execute('UPDATE CRECHE SET debut_pause=?', (0,))
            cur.execute('UPDATE CRECHE SET fin_pause=?', (0,))

        if version < 61:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD frais_inscription FLOAT")
            cur.execute("UPDATE INSCRIPTIONS SET frais_inscription=?", (.0,))

        if version < 62:
            cur.execute("""
              CREATE TABLE CORRECTIONS (
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                date DATE,
                valeur FLOAT,
                libelle VARCHAR
              );""")
            cur.execute("ALTER TABLE CRECHE ADD smtp_server VARCHAR;")
            cur.execute("ALTER TABLE CRECHE ADD caf_email VARCHAR;")

        if version < 63:
            cur.execute("ALTER TABLE CRECHE ADD mode_accueil_defaut INTEGER;")
            cur.execute("ALTER TABLE CRECHE ADD gestion_absences_non_prevenues BOOLEAN;")
            cur.execute("UPDATE CRECHE SET mode_accueil_defaut=?", (0,))
            cur.execute("UPDATE CRECHE SET gestion_absences_non_prevenues=?", (False,))

        if version < 64:
            cur.execute("""
                CREATE TABLE COMMENTAIRES(
                  idx INTEGER PRIMARY KEY,
                  inscrit INTEGER REFERENCES INSCRITS(idx),
                  date DATE,
                  commentaire VARCHAR
                );""")

        if version < 65:
            cur.execute("ALTER TABLE CRECHE ADD gestion_depart_anticipe BOOLEAN;")
            cur.execute("UPDATE CRECHE SET gestion_depart_anticipe=?", (False,))
            cur.execute("ALTER TABLE INSCRIPTIONS ADD depart DATE;")
            cur.execute("UPDATE INSCRIPTIONS SET depart=?", (None,))

        if version < 66:
            cur.execute("""
              CREATE TABLE REF_JOURNEES_SALARIES(
                idx INTEGER PRIMARY KEY,
                reference INTEGER REFERENCES CONTRATS(idx),
                day INTEGER,
                value INTEGER,
                debut INTEGER,
                fin INTEGER
              );""")

            cur.execute("""
              CREATE TABLE CONGES_SALARIES(
                idx INTEGER PRIMARY KEY,
                salarie INTEGER REFERENCES EMPLOYES(idx),
                debut VARCHAR,
                fin VARCHAR,
                label VARCHAR
              );""")

            cur.execute("""
              CREATE TABLE ACTIVITES_SALARIES(
                idx INTEGER PRIMARY KEY,
                salarie INTEGER REFERENCES EMPLOYES(idx),
                date DATE,
                value INTEGER,
                debut INTEGER,
                fin INTEGER
              );""")

        if version < 67:
            cur.execute("ALTER TABLE CONTRATS ADD duree_reference INTEGER;")
            cur.execute('UPDATE CONTRATS SET duree_reference=?', (7,))
            cur.execute('DELETE FROM REF_JOURNEES_SALARIES where day>6')

        if version < 68:
            cur.execute('SELECT capacite, ouverture, fermeture, debut_pause, fin_pause FROM CRECHE')
            capacite, ouverture, fermeture, debut_pause, fin_pause = cur.fetchall()[0]
            cur.execute("""
              CREATE TABLE CAPACITE(
                idx INTEGER PRIMARY KEY,
                value INTEGER,
                debut INTEGER,
                fin INTEGER
              );""")
            if debut_pause > ouverture and fin_pause > debut_pause and fermeture > fin_pause:
                start, end = int(ouverture*(60 / BASE_GRANULARITY)), int(debut_pause*(60 / BASE_GRANULARITY))
                cur.execute('INSERT INTO CAPACITE (idx, value, debut, fin) VALUES (NULL,?,?,?)', (capacite, start, end))
                start, end = int(fin_pause*(60 / BASE_GRANULARITY)), int(fermeture*(60 / BASE_GRANULARITY))
                cur.execute('INSERT INTO CAPACITE (idx, value, debut, fin) VALUES (NULL,?,?,?)', (capacite, start, end))
            else:
                start, end = int(ouverture*(60 / BASE_GRANULARITY)), int(fermeture*(60 / BASE_GRANULARITY))
                cur.execute('INSERT INTO CAPACITE (idx, value, debut, fin) VALUES (NULL,?,?,?)', (capacite, start, end))

        if version < 69:
            cur.execute("""  
              CREATE TABLE RESERVATAIRES (
                idx INTEGER PRIMARY KEY,
                debut DATE,
                fin DATE,
                nom VARCHAR,
                adresse VARCHAR,
                code_postal INTEGER,
                ville VARCHAR,
                telephone VARCHAR,
                email VARCHAR,
                places INTEGER,
                heures_jour FLOAT,
                heures_semaine FLOAT,
                options INTEGER
              );""")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD reservataire INTEGER REFERENCES RESERVATAIRES(idx)")

        if version < 70:
            cur.execute("ALTER TABLE CRECHE ADD arrondi_heures_salaries INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_heures_salaries=?', (0,))
            cur.execute("ALTER TABLE CRECHE ADD periode_revenus INTEGER;")
            cur.execute('UPDATE CRECHE SET periode_revenus=?', (0,))

        if version < 71:
            cur.execute('SELECT arrondi_heures FROM CRECHE')
            arrondi_heures = cur.fetchall()[0][0]
            cur.execute("ALTER TABLE CRECHE ADD arrondi_facturation INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_facturation=?', (arrondi_heures,))

        if version < 72:
            cur.execute("ALTER TABLE TARIFSSPECIAUX ADD type INTEGER")
            cur.execute("ALTER TABLE TARIFSSPECIAUX ADD unite INTEGER")
            cur.execute('UPDATE TARIFSSPECIAUX SET type=?', (0,))
            cur.execute('UPDATE TARIFSSPECIAUX SET unite=?', (0,))
            cur.execute('UPDATE TARIFSSPECIAUX SET type=? WHERE reduction=?', (1, True))
            cur.execute('UPDATE TARIFSSPECIAUX SET unite=? WHERE pourcentage=?', (1, True))

        if version < 73:
            cur.execute("ALTER TABLE INSCRITS ADD combinaison VARCHAR;")
            cur.execute('UPDATE INSCRITS SET combinaison=?', ("",))

        if version < 74:
            cur.execute("ALTER TABLE BUREAUX ADD gerant VARCHAR;")
            cur.execute("ALTER TABLE BUREAUX ADD directeur_adjoint VARCHAR;")
            cur.execute("ALTER TABLE BUREAUX ADD comptable VARCHAR;")
            cur.execute("ALTER TABLE ACTIVITIES ADD owner INTEGER;")
            cur.execute('UPDATE ACTIVITIES SET owner=0;')
            cur.execute("ALTER TABLE CRECHE ADD age_maximum INTEGER")
            cur.execute('UPDATE CRECHE SET age_maximum=?', (3,))

        if version < 75:
            cur.execute("""
              CREATE TABLE CATEGORIES (
                idx INTEGER PRIMARY KEY,
                nom VARCHAR
              );""")
            cur.execute("ALTER TABLE INSCRITS ADD categorie INTEGER REFERENCES CATEGORIES(idx)")

        if version < 76:
            cur.execute("ALTER TABLE CRECHE ADD alerte_depassement_planning BOOLEAN;")
            cur.execute("UPDATE CRECHE SET alerte_depassement_planning=?", (False,))

        if version < 77:
            cur.execute("ALTER TABLE CRECHE ADD gestion_maladie_sans_justificatif BOOLEAN;")
            cur.execute("ALTER TABLE CRECHE ADD gestion_preavis_conges BOOLEAN;")
            cur.execute("UPDATE CRECHE SET gestion_maladie_sans_justificatif=?", (False,))
            cur.execute("UPDATE CRECHE SET gestion_preavis_conges=?", (False,))

        if version < 78:
            cur.execute('SELECT debut_pause, fin_pause FROM CRECHE')
            debut_pause, fin_pause = cur.fetchall()[0]
            cur.execute("""
              CREATE TABLE PLAGESHORAIRES (
                idx INTEGER PRIMARY KEY,
                debut FLOAT,
                fin FLOAT,
                flags INTEGER
              );""")
            if debut_pause != 0 and fin_pause != 0:
                cur.execute('INSERT INTO PLAGESHORAIRES (idx, debut, fin, flags) VALUES (NULL,?,?,?)', (debut_pause, fin_pause, PLAGE_FERMETURE))

        if version < 79:
            cur.execute("ALTER TABLE CRECHE ADD last_tablette_synchro VARCHAR;")
            cur.execute("UPDATE CRECHE SET last_tablette_synchro=?", ("",))

        if version < 80:
            cur.execute("ALTER TABLE REVENUS ADD conge_parental BOOLEAN;")
            cur.execute("UPDATE REVENUS SET conge_parental=?", (False,))

        if version < 81:
            cur.execute("ALTER TABLE CRECHE ADD repartition INTEGER;")
            cur.execute("UPDATE CRECHE SET repartition=?", (REPARTITION_MENSUALISATION_12MOIS,))

        if version < 82:
            cur.execute("""
              CREATE TABLE NUMEROS_FACTURE (
                idx INTEGER PRIMARY KEY,
                date DATE,
                valeur INTEGER
              );""")

        if version < 83:
            cur.execute('SELECT value, debut, fin, idx FROM CAPACITE')
            capacite = cur.fetchall()
            cur.execute("DELETE FROM CAPACITE")
            cur.execute("ALTER TABLE CAPACITE ADD jour INTEGER;")
            for value, debut, fin, idx in capacite:
                for jour in range(7):
                    cur.execute('INSERT INTO CAPACITE (idx, value, debut, fin, jour) VALUES (NULL,?,?,?,?)', (value, debut, fin, jour))
            cur.execute("ALTER TABLE INSCRITS ADD medecin_traitant VARCHAR;")
            cur.execute("UPDATE INSCRITS SET medecin_traitant=?", ("",))
            cur.execute("ALTER TABLE INSCRITS ADD telephone_medecin_traitant VARCHAR;")
            cur.execute("UPDATE INSCRITS SET telephone_medecin_traitant=?", ("",))
            cur.execute("ALTER TABLE INSCRITS ADD assureur VARCHAR;")
            cur.execute("UPDATE INSCRITS SET assureur=?", ("",))
            cur.execute("ALTER TABLE INSCRITS ADD numero_police_assurance VARCHAR;")
            cur.execute("UPDATE INSCRITS SET numero_police_assurance=?", ("",))

        if version < 84:
            cur.execute("ALTER TABLE CRECHE ADD seuil_alerte_inscription INTEGER")
            cur.execute('UPDATE CRECHE SET seuil_alerte_inscription=?', (3,))

        if version < 85:
            cur.execute("ALTER TABLE CRECHE ADD changement_groupe_auto BOOLEAN;")
            cur.execute("UPDATE CRECHE SET changement_groupe_auto=?", (False,))
            cur.execute("ALTER TABLE GROUPES ADD age_maximum INTEGER")
            cur.execute('UPDATE GROUPES SET age_maximum=?', (0,))
            cur.execute("ALTER TABLE CRECHE ADD allergies VARCHAR;")
            cur.execute("UPDATE CRECHE SET allergies=?", ("",))
            cur.execute("ALTER TABLE INSCRITS ADD allergies VARCHAR;")
            cur.execute("UPDATE INSCRITS SET allergies=?", ("",))

        if version < 86:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD allocation_mensuelle_caf FLOAT")
            cur.execute("UPDATE INSCRIPTIONS SET allocation_mensuelle_caf=?", (.0,))

        if version < 87:
            cur.execute("ALTER TABLE CRECHE ADD regularisation_fin_contrat BOOLEAN;")
            cur.execute("UPDATE CRECHE SET regularisation_fin_contrat=?", (True,))

        if version < 88:
            # TODO notes_parents marche ?
            cur.execute("""
              CREATE TABLE FAMILLES(
                idx INTEGER PRIMARY KEY,
                adresse VARCHAR,
                code_postal INTEGER,
                ville VARCHAR,
                numero_securite_sociale VARCHAR,
                numero_allocataire_caf VARCHAR,
                medecin_traitant VARCHAR,
                telephone_medecin_traitant VARCHAR,
                assureur VARCHAR,
                numero_police_assurance VARCHAR,
                tarifs INTEGER,
                notes VARCHAR
              );""")
            cur.execute("ALTER TABLE INSCRITS ADD famille INTEGER REFERENCES FAMILLES(idx);")
            cur.execute("ALTER TABLE PARENTS ADD famille INTEGER REFERENCES FAMILLES(idx);")
            cur.execute("ALTER TABLE FRATRIES ADD famille INTEGER REFERENCES FAMILLES(idx);")
            cur.execute("ALTER TABLE REFERENTS ADD famille INTEGER REFERENCES FAMILLES(idx);")
            cur.execute('SELECT idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes_parents FROM INSCRITS')
            for idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes in cur.fetchall():
                result = self.con.execute('INSERT INTO FAMILLES (idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?)', (adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes))
                cur.execute('UPDATE INSCRITS SET famille=? WHERE idx=?', (result.lastrowid, idx))
                cur.execute('UPDATE PARENTS SET famille=? WHERE inscrit=?', (result.lastrowid, idx))
                cur.execute('UPDATE FRATRIES SET famille=? WHERE inscrit=?', (result.lastrowid, idx))
                cur.execute('UPDATE REFERENTS SET famille=? WHERE inscrit=?', (result.lastrowid, idx))

        if version < 89:
            cur.execute("ALTER TABLE EMPLOYES ADD combinaison VARCHAR;")
            cur.execute('UPDATE EMPLOYES SET combinaison=?', ("",))

        if version < 90:
            cur.execute("ALTER TABLE FAMILLES ADD code_client VARCHAR;")
            cur.execute('UPDATE FAMILLES SET code_client=?', ("",))
            cur.execute("ALTER TABLE CRECHE ADD tri_factures INTEGER")
            cur.execute('UPDATE CRECHE SET tri_factures=?', (TRI_NOM,))

        if version < 91:
            try:
                cur.execute("""
                  CREATE TABLE ENCAISSEMENTS (
                    idx INTEGER PRIMARY KEY,
                    famille INTEGER REFERENCES FAMILLES(idx),
                    date DATE,
                    valeur FLOAT,
                    moyen_paiement INTEGER
                  );""")
            except:
                print "Erreur sur creation table ENCAISSEMENTS"

        if version < 92:
            cur.execute("ALTER TABLE SITES ADD groupe INTEGER;")
            cur.execute("UPDATE SITES SET groupe=?;", (0,))

        if version < 93:
            cur.execute("ALTER TABLE CRECHE ADD arrondi_mensualisation_euros INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_mensualisation_euros=?', (SANS_ARRONDI,))
            cur.execute("ALTER TABLE CRECHE ADD arrondi_semaines INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_semaines=?', (ARRONDI_SEMAINE_SUPERIEURE,))

        if version < 94:
            cur.execute("ALTER TABLE INSCRIPTIONS ADD forfait_mensuel_heures FLOAT")
            cur.execute('SELECT idx, forfait_heures_presence FROM INSCRIPTIONS')
            for idx, forfait_heures_presence in cur.fetchall():
                cur.execute("UPDATE INSCRIPTIONS SET forfait_mensuel_heures=? WHERE idx=?", (forfait_heures_presence, idx))

        if version < 95:
            cur.execute("ALTER TABLE CRECHE ADD tri_inscriptions INTEGER")
            cur.execute('UPDATE CRECHE SET tri_inscriptions=?', (TRI_NOM,))

        if version < 96:
            cur.execute("ALTER TABLE CRECHE ADD mode_saisie_planning INTEGER")
            cur.execute('UPDATE CRECHE SET mode_saisie_planning=?', (0,))
            cur.execute("""
              CREATE TABLE PLANNING_HEBDOMADAIRE(
                idx INTEGER PRIMARY KEY,
                inscrit INTEGER REFERENCES INSCRITS(idx),
                date DATE,
                activity INTEGER,
                value FLOAT
              );""")
            cur.execute("ALTER TABLE ACTIVITIES ADD formule_tarif VARCHAR;")
            cur.execute('SELECT idx, tarif FROM ACTIVITIES')
            for (idx, tarif) in cur.fetchall():
                cur.execute('UPDATE ACTIVITIES SET formule_tarif=? WHERE idx=?', (str(tarif), idx))
            cur.execute("ALTER TABLE INSCRIPTIONS ADD heures_permanences FLOAT;")
            cur.execute('UPDATE INSCRIPTIONS SET heures_permanences=?', (0,))
            cur.execute("ALTER TABLE CRECHE ADD date_raz_permanences;")
            cur.execute("UPDATE CRECHE SET date_raz_permanences=?", (None,))

        if version < 97:
            cur.execute("ALTER TABLE CRECHE ADD conges_payes_salaries INTEGER")
            cur.execute('UPDATE CRECHE SET conges_payes_salaries=?', (25,))
            cur.execute("ALTER TABLE CRECHE ADD conges_supplementaires_salaries INTEGER")
            cur.execute('UPDATE CRECHE SET conges_supplementaires_salaries=?', (0,))
            cur.execute("""
                CREATE TABLE COMMENTAIRES_SALARIES(
                  idx INTEGER PRIMARY KEY,
                  salarie INTEGER REFERENCES SALARIES(idx),
                  date DATE,
                  commentaire VARCHAR
                );""")
            cur.execute("ALTER TABLE CRECHE ADD cout_journalier FLOAT")
            cur.execute('UPDATE CRECHE SET cout_journalier=?', (.0,))

        if version < 98:
            cur.execute('SELECT arrondi_facturation FROM CRECHE')
            arrondi_facturation = cur.fetchall()[0][0]
            cur.execute("ALTER TABLE CRECHE ADD arrondi_facturation_periode_adaptation INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_facturation_periode_adaptation=?', (arrondi_facturation,))

        if version < 99:
            cur.execute("ALTER TABLE CRECHE ADD arrondi_mensualisation INTEGER")
            cur.execute('UPDATE CRECHE SET arrondi_mensualisation=?', (ARRONDI_HEURE_PLUS_PROCHE,))

        if version < 100:
            cur.execute("ALTER TABLE PARENTS ADD adresse VARCHAR;")
            cur.execute("ALTER TABLE PARENTS ADD code_postal INTEGER;")
            cur.execute("ALTER TABLE PARENTS ADD ville VARCHAR;")
            cur.execute('SELECT adresse, code_postal, ville, idx FROM FAMILLES')
            for adresse, code_postal, ville, famille in cur.fetchall():
                cur.execute("UPDATE PARENTS SET adresse=?, code_postal=?, ville=? WHERE famille=?", (adresse, code_postal, ville, famille))

        if version < 101:
            cur.execute('SELECT login, password, idx FROM USERS')
            for login, password, idx in cur.fetchall():
                hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                cur.execute("UPDATE USERS SET password=? WHERE idx=?", (hashed, idx))

        if version < 102:
            cur.execute('SELECT profile, idx FROM USERS')
            for old_profile, idx in cur.fetchall():
                if old_profile == 31:
                    profile = 127
                elif old_profile:
                    profile = old_profile & 1
                    if old_profile & 2:
                        profile |= 4 + 8
                    if old_profile & 4:
                        profile |= 16 + 8
                    if old_profile & 8:
                        profile |= 2
                    if old_profile & 16:
                        profile |= 64
                    if old_profile & 32:
                        profile |= 128
                cur.execute("UPDATE USERS SET profile=? WHERE idx=?", (profile, idx))

        if version < 103:
            cur.execute("ALTER TABLE CRECHE ADD cloture_facturation INTEGER;")
            cur.execute("SELECT cloture_factures FROM CRECHE")
            cloture_facturation = CLOTURE_FACTURES_AVEC_CONTROLE if cur.fetchall()[0][0] else CLOTURE_FACTURES_OFF
            cur.execute('UPDATE CRECHE SET cloture_facturation=?', (cloture_facturation,))

        if version < 104:
            cur.execute("ALTER TABLE CRECHE ADD iban VARCHAR;")
            cur.execute("ALTER TABLE CRECHE ADD bic VARCHAR;")
            cur.execute("ALTER TABLE FAMILLES ADD iban VARCHAR;")
            cur.execute("ALTER TABLE FAMILLES ADD bic VARCHAR;")
            cur.execute("ALTER TABLE FAMILLES ADD jour_prelevement_automatique INTEGER;")
            cur.execute("ALTER TABLE FAMILLES ADD date_premier_prelevement_automatique DATE;")

        if version < 105:
            cur.execute("ALTER TABLE RESERVATAIRES ADD periode_facturation INTEGER;")
            cur.execute("ALTER TABLE RESERVATAIRES ADD delai_paiement INTEGER;")
            cur.execute("ALTER TABLE RESERVATAIRES ADD tarif FLOAT;")
            cur.execute("ALTER TABLE INSCRIPTIONS ADD newsletters INTEGER;")
            cur.execute("UPDATE RESERVATAIRES SET periode_facturation=1, delai_paiement=30;")
            cur.execute("UPDATE INSCRIPTIONS SET newsletters=0;")

        if version < 106:
            cur.execute("ALTER TABLE CRECHE ADD masque_alertes INTEGER;")
            cur.execute("SELECT gestion_alertes FROM CRECHE")
            masque_alertes = 7 if cur.fetchall()[0][0] else 0
            cur.execute('UPDATE CRECHE SET masque_alertes=?', (masque_alertes,))

        if version < 107:
            cur.execute("ALTER TABLE CRECHE ADD creditor_id VARCHAR;")
            cur.execute("ALTER TABLE FAMILLES ADD mandate_id VARCHAR;")

        if version < 108:
            cur.execute("SELECT formule_taux_horaire FROM CRECHE")
            formule_taux_horaire = cur.fetchall()[0][0]
            cur.execute("""
              CREATE TABLE TARIFS_HORAIRES(
                idx INTEGER PRIMARY KEY,
                debut DATE,
                fin DATE,
                formule VARCHAR
              )""")
            cur.execute("INSERT INTO TARIFS_HORAIRES (idx, debut, fin, formule) VALUES (NULL, ?, ?, ?)", (None, None, formule_taux_horaire))

        if version < VERSION:
            try:
                cur.execute("DELETE FROM DATA WHERE key=?", ("VERSION", ))
            except sqlite3.OperationalError:
                pass

            cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))
            try:
                cur.execute("VACUUM")
            except:
                pass

            self.commit()

        return True
