#!/usr/bin/python
# -*- coding: utf-8 -*-

# from __future__ import unicode_literals

import os
import sys
import __builtin__
import shutil

sys.path.append('..')

import sqlinterface
from functions import *
from sqlobjects import *
from config import *

shutil.copyfile("gertrude.db", "../aiga.db")
__builtin__.sql_connection = sqlinterface.SQLConnection("../aiga.db")
__builtin__.creche = sql_connection.Load(None)


def get_lines_splitted(filename):
    result = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            result.append(line.split(chr(169)))
    return result


def get_enfants():
    enfants = {}
    for fields in get_lines_splitted("aiga/enfant.txt"):
        enfant = dict()
        enfant['idx'] = int(fields[0])
        enfant['nom'] = fields[1].decode('cp1252')
        enfant['prenom'] = fields[2].decode('cp1252')
        enfant['naissance'] = str2date(fields[3])
        enfant['sexe'] = int(fields[4])
        enfant['idx_parents'] = int(fields[5])
        enfant['idx_medecin'] = int(fields[6])
        enfant['entree_creche'] = str2date(fields[20])
        enfants[enfant['idx']] = enfant
    return enfants


def get_medecins():
    medecins = {}
    for fields in get_lines_splitted("aiga/medecin.txt"):
        medecin = dict()
        medecin['idx'] = int(fields[0])
        medecin['nom'] = fields[1].decode('cp1252')
        medecins[medecin['idx']] = medecin
    return medecins


def get_inscriptions():
    inscriptions = {}
    for fields in get_lines_splitted("aiga/inscript.txt"):
        inscription = dict()
        inscription['idx'] = int(fields[0])
        inscription['idx_enfant'] = int(fields[1])
        inscription['debut'] = str2date(fields[2])
        inscription['fin'] = str2date(fields[3])
        inscription['heures_semaine'] = float(fields[67])  # int(fields[36])
        inscription['tarif_horaire'] = float(fields[37])
        inscriptions[inscription['idx']] = inscription
    return inscriptions


def get_parents():
    parents = {}
    for fields in get_lines_splitted("aiga/parent.txt"):
        # for i, field in enumerate(fields):
        #     if field:
        #         print i, ":", field,
        # print
        parent = dict()
        parent['idx'] = int(fields[0])
        parent['nom_papa'] = fields[1].decode('cp1252')
        parent['prenom_papa'] = fields[2].decode('cp1252')
        parent['adresse_papa'] = fields[3].decode('cp1252')
        parent['code_postal_papa'] = int(fields[5]) if fields[5] else ''
        parent['ville_papa'] = fields[6].decode('cp1252')
        parent['telephone_domicile_papa'] = fields[7].replace(".", " ")
        parent['telephone_portable_papa'] = fields[18].replace(".", " ")
        parent['telephone_travail_papa'] = fields[23].replace(".", " ")
        parent['email_papa'] = fields[68]
        parent['allocataire'] = fields[9]
        parent['revenu_papa'] = float(fields[11]) * 12
        parent['nom_maman'] = fields[36].decode('cp1252')
        parent['prenom_maman'] = fields[37].decode('cp1252')
        parent['adresse_maman'] = fields[38]
        parent['code_postal_maman'] = int(fields[39]) if fields[39] else ''
        parent['ville_maman'] = fields[40]
        parent['telephone_domicile_maman'] = fields[41].replace(".", " ")
        parent['telephone_portable_maman'] = fields[67].replace(".", " ")
        parent['email_maman'] = fields[69]
        parent['revenu_maman'] = float(fields[47]) * 12
        parents[parent['idx']] = parent
        # print parent
    return parents


def get_salaries():
    salaries = []
    for fields in get_lines_splitted("aiga/employe.txt"):
        entry = dict()
        entry['nom'] = fields[0].decode('cp1252')
        entry['prenom'] = fields[2].decode('cp1252')
        entry['adresse'] = fields[3].decode('cp1252')
        try:
            entry['code_postal'] = int(fields[5])
        except:
            entry['code_postal'] = ""
        entry['ville'] = fields[6].decode('cp1252')
        entry['telephone_domicile'] = fields[7].decode('cp1252').replace(".", " ")
        salaries.append(entry)
    return salaries


def get_semaines_conges():
    semaines_conges = {}
    for fields in get_lines_splitted("aiga/insczp.txt"):
        entry = dict()
        entry['idx_inscription'] = int(fields[0])
        entry['heures'] = float(fields[1]) if len(fields) > 1 else 0.0
        entry['semaines_conges'] = 52 - float(fields[2]) if len(fields) > 2 else 0
        entry['mois_factures'] = float(fields[3]) if len(fields) > 3 else 12.0
        semaines_conges[entry['idx_inscription']] = entry
    return semaines_conges


def get_factures():
    factures = {}
    for fields in get_lines_splitted("aiga/facture.txt"):
        entry = dict()
        entry['idx'] = int(fields[0], 16)
        entry['date'] = GetMonthStart(str2date(fields[1]))
        entry['total'] = float(fields[4])
        entry['idx_inscription'] = int(fields[10])
        factures[entry['idx']] = entry
    return factures


def insert_planning(obj, heures):
    print "insert_planning(%d)" % heures
    jour = 0
    while heures > 0:
        count = min(heures, 10)
        obj.reference[jour].InsertActivity(8 * 12, 8 * 12 + count * 12, 0)
        heures -= count
        jour += 1


def main():
    print "Start import ..."
    enfants = get_enfants()
    parents = get_parents()
    inscriptions = get_inscriptions()
    semaines_conges = get_semaines_conges()
    factures = get_factures()
    medecins = get_medecins()
    print "medecins", medecins
    salaries = get_salaries()
    for salarie in salaries:
        obj = Salarie()
        obj.nom = salarie['nom']
        obj.prenom = salarie['prenom']
        obj.telephone_domicile = salarie['telephone_domicile']
    for enfant in enfants.values():
        parent = parents[enfant['idx_parents']]
        obj = Inscrit()
        obj.nom = enfant['nom']
        obj.prenom = enfant['prenom']
        obj.naissance = enfant['naissance']
        obj.sexe = enfant['sexe']
        obj.famille.adresse = parent['adresse_papa']
        obj.famille.ville = parent['ville_papa']
        obj.famille.code_postal = parent['code_postal_papa']
        obj.famille.medecin_traitant = medecins[enfant['idx_medecin']]['nom']
        obj.famille.numero_allocataire_caf = parent['allocataire']
        # les parents
        obj.famille.parents[0].nom = parent['nom_papa']
        obj.famille.parents[0].prenom = parent['prenom_papa']
        obj.famille.parents[0].telephone_domicile = parent['telephone_domicile_papa']
        obj.famille.parents[0].telephone_portable = parent['telephone_portable_papa']
        obj.famille.parents[0].telephone_travail = parent['telephone_travail_papa']
        obj.famille.parents[0].email = parent['email_papa']
        obj.famille.parents[0].adresse = parent['adresse_papa']
        obj.famille.parents[0].ville = parent['ville_papa']
        obj.famille.parents[0].code_postal = parent['code_postal_papa']
        obj.famille.parents[0].revenus[0].debut = datetime.date(2010, 1, 1)
        obj.famille.parents[0].revenus[0].revenu = parent['revenu_papa']
        obj.famille.parents[1].nom = parent['nom_maman']
        obj.famille.parents[1].prenom = parent['prenom_maman']
        obj.famille.parents[1].telephone_domicile = parent['telephone_domicile_maman']
        obj.famille.parents[1].telephone_portable = parent['telephone_portable_maman']
        obj.famille.parents[1].email = parent['email_maman']
        obj.famille.parents[1].adresse = parent['adresse_papa']
        obj.famille.parents[1].ville = parent['ville_papa']
        obj.famille.parents[1].code_postal = parent['code_postal_papa']
        obj.famille.parents[1].revenus[0].debut = datetime.date(2010, 1, 1)
        obj.famille.parents[1].revenus[0].revenu = parent['revenu_maman']
        # les inscriptions
        obj.inscriptions[0].delete()
        del obj.inscriptions[0]
        for inscription in inscriptions.values():
            if inscription['idx_enfant'] == enfant['idx']:
                obj_inscription = Inscription(obj)
                obj_inscription.mode = MODE_TEMPS_PARTIEL
                obj_inscription.debut = inscription['debut']
                obj_inscription.fin = inscription['fin']
                # horaires
                conges = semaines_conges[inscription['idx']]
                obj_inscription.semaines_conges = conges['semaines_conges']
                insert_planning(obj_inscription, conges['heures'])
    sql_connection.close()


if __name__ == "__main__":
    main()





