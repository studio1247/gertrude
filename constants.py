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

days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
months = ["Janvier", u'Février', "Mars", "Avril", "Mai", "Juin", "Juillet", u'Août', "Septembre", "Octobre", "Novembre", u'Décembre']
months_abbrev = ["Janv", u'Fév', "Mars", "Avril", "Mai", "Juin", "Juil", u'Août', "Sept", "Oct", "Nov", u'Déc']
trimestres = ["1er", u'2ème', u'3ème', u'4ème']

# Profils des utilisateurs
PROFIL_INSCRIPTIONS = 1
PROFIL_TRESORIER = 2
PROFIL_BUREAU = 4
PROFIL_SAISIE_PRESENCES = 8
PROFIL_ADMIN = 16
PROFIL_ALL = PROFIL_ADMIN + PROFIL_INSCRIPTIONS + PROFIL_TRESORIER + PROFIL_BUREAU + PROFIL_SAISIE_PRESENCES

# Types de structures
TYPE_PARENTAL = 0
TYPE_ASSOCIATIF = 1
TYPE_MUNICIPAL = 2
TYPE_GARDERIE_PERISCOLAIRE = 3
TYPE_MICRO_CRECHE = 4
TYPE_ASSISTANTE_MATERNELLE = 5

# Modes des activités
MODE_NORMAL = 0
MODE_LIBERE_PLACE = 1
MODE_SANS_HORAIRES = 2

# Granularité du planning dans la base
BASE_GRANULARITY = 5 # 5 minutes
TAILLE_TABLE_ACTIVITES = 24 * 60 / BASE_GRANULARITY

# Modes d'inscription
MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1
MODE_5_5 = 2
MODE_4_5 = 4
MODE_3_5 = 8
MODE_FORFAIT_HORAIRE = 16
MODE_TEMPS_PARTIEL = 32

# Modes de facturation
FACTURATION_FORFAIT_10H = 0
FACTURATION_PSU = 1
FACTURATION_PAJE = 2
FACTURATION_HORAIRES_REELS = 3
FACTURATION_FORFAIT_MENSUEL = 4
FACTURATION_PSU_TAUX_PERSONNALISES = 5

# Modes de facturation de la période d'adaptation
PERIODE_ADAPTATION_FACTUREE_NORMALEMENT = 0

# Facturation début/fin de mois
FACTURATION_FIN_MOIS = 0
FACTURATION_DEBUT_MOIS = 1

# Modes de traitement des absences pour maladie
DEDUCTION_MALADIE_SANS_CARENCE = 0
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES = 1
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES = 2

# Mode de traitement des jours feries
JOURS_FERIES_NON_DEDUITS = 0
JOURS_FERIES_DEDUITS_ANNUELLEMENT = 1

# MODES de facturation des activites
ACTIVITES_NON_FACTUREES = 0
ACTIVITES_FACTUREES_JOURNEE = 1
ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION = 3

# Options des conges
ACCUEIL_NON_FACTURE = 1 #  jours de nettoyage par exemple
MOIS_SANS_FACTURE = 2 # si présence dans cette periode (mois d'août par exemple), elle est répartie sur les autres mois de l'année 

# Valeurs de présence
ABSENT = 0
PRESENT = 1 << 0 # activité 0
VACANCES = -1
MALADE = -2
SUPPLEMENT = 1 << 29 # pas d'activité > 28 !
PREVISIONNEL = 1 << 30 # flag previsionnel

# Types des champs OpenOffice
FIELD_EUROS = 1

#IDs de boutons
ID_SYNCHRO = 10001
ID_UNDO = 10002

