# -*- coding: utf8 -*-

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
BASE_MIN_HOUR = 6 # 6h00
BASE_MAX_HOUR = 22 # 22h00
BASE_GRANULARITY = 4 # au quart d'heure

MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1
MODE_4_5 = 2
MODE_3_5 = 4

PRESENT = 0
VACANCES = 1
MALADE = 2
NONINSCRIT = 3 # utilise dans getPresence
SUPPLEMENT = 4 # utilise dans getPresence

ID_SYNCHRO = 10001
ID_UNDO = 10002

