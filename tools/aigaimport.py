#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import __builtin__
import shutil

sys.path.append('..')

import sqlinterface
from functions import *
from sqlobjects import *

shutil.copyfile("gertrude.db", "../aiga.db")
__builtin__.sql_connection = sqlinterface.SQLConnection("../aiga.db")
__builtin__.creche = sql_connection.Load(None)


def get_lines_splitted(filename):
    result = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            result.append(line.split("\xa9"))
    return result


def get_enfants():
    enfants = {}
    for fields in get_lines_splitted("aiga/utile/enfant.txt"):
        enfant = dict()
        enfant['idx'] = int(fields[0])
        enfant['nom'] = fields[1].decode('cp1252')
        enfant['prenom'] = fields[2].decode('cp1252')
        enfant['naissance'] = str2date(fields[3])
        enfant['sexe'] = int(fields[4])
        enfant['idx_parents'] = int(fields[5])
        # enfant['idx_maman'] = int(fields[6])
        enfant['entree_creche'] = str2date(fields[20])
        enfants[enfant['idx']] = enfant
    return enfants


def get_inscriptions():
    inscriptions = {}
    for fields in get_lines_splitted("aiga/utile/inscript.txt"):
        inscription = dict()
        inscription['idx'] = int(fields[0])
        inscription['idx_enfant'] = int(fields[1])
        inscription['debut'] = str2date(fields[2])
        inscription['fin'] = str2date(fields[3])
        inscription['heures_semaine'] = int(fields[36])
        inscription['tarif_horaire'] = float(fields[37])
        inscriptions[inscription['idx']] = inscription
    return inscriptions


def get_parents():
    parents = {}
    for fields in get_lines_splitted("aiga/utile/parent.txt"):
        parent = dict()
        parent['idx'] = int(fields[0])
        parent['nom_papa'] = fields[1].decode('cp1252')
        parent['prenom_papa'] = fields[2].decode('cp1252')
        parent['adresse_papa'] = fields[3]
        parent['code_postal_papa'] = int(fields[5]) if fields[5] else ''
        parent['ville_papa'] = fields[6]
        parent['allocataire'] = fields[9]
        parent['revenu_papa'] = float(fields[11]) * 12
        parent['nom_maman'] = fields[36].decode('cp1252')
        parent['prenom_maman'] = fields[37].decode('cp1252')
        parent['addresse_maman'] = fields[38]
        parent['code_postal_maman'] = int(fields[39]) if fields[39] else ''
        parent['ville_maman'] = fields[40]
        parent['revenu_maman'] = float(fields[47]) * 12
        parents[parent['idx']] = parent
    return parents


def get_semaines_conges():
    semaines_conges = {}
    for fields in get_lines_splitted("aiga/utile/insczp.txt"):
        entry = dict()
        entry['idx_inscription'] = int(fields[0])
        entry['heures'] = float(fields[1])
        entry['semaines_conges'] = 52 - float(fields[2])
        entry['mois_factures'] = float(fields[3])
        semaines_conges[entry['idx_inscription']] = entry
    return semaines_conges


def get_factures():
    factures = {}
    for fields in get_lines_splitted("aiga/utile/facture.txt"):
        entry = dict()
        entry['idx'] = int(fields[0])
        entry['date'] = GetMonthStart(str2date(fields[1]))
        entry['total'] = float(fields[4])
        entry['idx_inscription'] = int(fields[10])
        factures[entry['idx']] = entry
    return factures


def insert_planning(obj, heures):
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
    for enfant in enfants.values():
        parent = parents[enfant['idx_parents']]
        for tmp in inscriptions.values():
            if tmp['idx_enfant'] == enfant['idx']:
                inscription = tmp
                break
        obj = Inscrit()
        obj.nom = enfant['nom']
        obj.prenom = enfant['prenom']
        obj.naissance = enfant['naissance']
        obj.sexe = enfant['sexe']
        obj.famille.addresse = parent['adresse_papa']
        obj.famille.ville = parent['ville_papa']
        obj.famille.code_postal = parent['code_postal_papa']
        obj.famille.numero_allocataire_caf = parent['allocataire']
        # les parents
        obj.famille.parents["papa"].nom = parent['nom_papa']
        obj.famille.parents["papa"].prenom = parent['prenom_papa']
        obj.famille.parents["papa"].revenus[0].debut = datetime.date(2010, 1, 1)
        obj.famille.parents["papa"].revenus[0].revenu = parent['revenu_papa']
        obj.famille.parents["maman"].nom = parent['nom_maman']
        obj.famille.parents["maman"].prenom = parent['prenom_maman']
        obj.famille.parents["maman"].revenus[0].debut = datetime.date(2010, 1, 1)
        obj.famille.parents["maman"].revenus[0].revenu = parent['revenu_maman']
        # l'inscription
        obj2 = obj.inscriptions[0]
        obj2.mode = MODE_TEMPS_PARTIEL
        obj2.debut = inscription['debut']
        obj2.fin = inscription['fin']
        # horaires
        conges = semaines_conges[inscription['idx']]
        obj2.semaines_conges = conges['semaines_conges']
        insert_planning(obj2, conges['heures'])
    sql_connection.close()


if __name__ == "__main__":
    main()





