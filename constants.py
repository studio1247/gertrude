# -*- coding: cp1252 -*-

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

VERSION = 4

PROFIL_INSCRIPTIONS = 1
PROFIL_TRESORIER = 2
PROFIL_BUREAU = 4
PROFIL_SAISIE_PRESENCES = 8
PROFIL_ADMIN = 16
PROFIL_ALL = PROFIL_ADMIN + PROFIL_INSCRIPTIONS + PROFIL_TRESORIER + PROFIL_BUREAU + PROFIL_SAISIE_PRESENCES

# Attention avant de modifier ces paramètres
# Ils modifient l'interprétation des données de la base
BASE_MIN_HOUR = 6 # 6h00
BASE_MAX_HOUR = 22 # 22h00
BASE_GRANULARITY = 4 # au quart d'heure

# Ces paramètres peuvent être modifiés sans danger
# Ils modifient l'affichage du planning
heureOuverture = 7.75
heureFermeture = 18.5
heureAffichageMin = 7.75
heureAffichageMax = 20
heureGranularite = 4 # au quart d'heure

tranches = [(heureOuverture, 12, 4), (12, 14, 2), (14, heureFermeture, 4)]
