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

days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
months = ["Janvier", u'Février', "Mars", "Avril", "Mai", "Juin", "Juillet", u'Août', "Septembre", "Octobre", "Novembre", u'Décembre']
months_abbrev = ["Janv", u'Fév', "Mars", "Avril", "Mai", "Juin", "Juil", u'Août', "Sept", "Oct", "Nov", u'Déc']
trimestres = ["1er", u'2ème', u'3ème', u'4ème']

PROFIL_INSCRIPTIONS = 1
PROFIL_TRESORIER = 2
PROFIL_BUREAU = 4
PROFIL_SAISIE_PRESENCES = 8
PROFIL_ADMIN = 16
PROFIL_ALL = PROFIL_ADMIN + PROFIL_INSCRIPTIONS + PROFIL_TRESORIER + PROFIL_BUREAU + PROFIL_SAISIE_PRESENCES

# Attention ces paramètres modifient l'interprétation des données de la base
#BASE_MIN_HOUR = 6 # 6h00
#BASE_MAX_HOUR = 22 # 22h00
BASE_GRANULARITY = 4 # au quart d'heure

# Modes d'accueil
MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1
MODE_4_5 = 2
MODE_3_5 = 4

# Modes de déduction pour maladie
DEDUCTION_TOTALE = 1
DEDUCTION_AVEC_CARENCE = 2

# Valeurs de présence
ABSENT = 0
PRESENT = 1
VACANCES = -1
MALADE = -2
NONINSCRIT = -3
PREVISIONNEL = 256
SUPPLEMENT = 512

ID_SYNCHRO = 10001
ID_UNDO = 10002

