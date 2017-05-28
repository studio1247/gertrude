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


days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
months_abbrev = ["Janv", "Fév", "Mars", "Avril", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
trimestres = ["1er", "2ème", "3ème", "4ème"]

# Profils des utilisateurs
PROFIL_INSCRIPTIONS = 1
PROFIL_PLANNING = 2
PROFIL_FACTURATION = 4
PROFIL_SALARIES = 8
PROFIL_TABLEAUX_DE_BORD = 16
PROFIL_ALL = 63
PROFIL_ADMIN = 64
PROFIL_LECTURE_SEULE = 128
PROFIL_SUPERADMIN = 256

TypesProfil = [
    ("Administrateur", PROFIL_ALL | PROFIL_ADMIN),
    ("Equipe", PROFIL_ALL),
    ("Inscriptions, planning et salariés", PROFIL_INSCRIPTIONS | PROFIL_SALARIES),
    ("Inscriptions et planning", PROFIL_INSCRIPTIONS | PROFIL_PLANNING),
    ("Saisie planning", PROFIL_PLANNING),
    ("Utilisateur lecture seule", PROFIL_ALL | PROFIL_LECTURE_SEULE),
    ("Planning lecture seule", PROFIL_PLANNING | PROFIL_LECTURE_SEULE),
]

# Types de structures
TYPE_PARENTAL = 0
TYPE_ASSOCIATIF = 1
TYPE_MUNICIPAL = 2
TYPE_GARDERIE_PERISCOLAIRE = 3
TYPE_MICRO_CRECHE = 4
TYPE_ASSISTANTE_MATERNELLE = 5
TYPE_FAMILIAL = 6
TYPE_MULTI_ACCUEIL = 7

TypesCreche = [
    ("Parental", TYPE_PARENTAL),
    ("Familial", TYPE_FAMILIAL),
    ("Associatif", TYPE_ASSOCIATIF),
    ("Municipal", TYPE_MUNICIPAL),
    ("Micro-crèche", TYPE_MICRO_CRECHE),
    ("Multi-accueil", TYPE_MULTI_ACCUEIL),
    ("Assistante maternelle", TYPE_ASSISTANTE_MATERNELLE),
    ("Garderie périscolaire", TYPE_GARDERIE_PERISCOLAIRE)
]

# Mode de saisie des plannings
SAISIE_HORAIRE = 0
SAISIE_JOURS_SEMAINE = 1
SAISIE_HEURES_SEMAINE = 2

# Modes des activités
MODE_NORMAL = 0
MODE_LIBERE_PLACE = 1
MODE_SANS_HORAIRES = 2
MODE_PRESENCE_NON_FACTUREE = 4
MODE_SYSTEMATIQUE_SANS_HORAIRES = 5
MODE_PERMANENCE = 6

ActivityModes = [
    ("Normal", 0),
    ("Libère une place", MODE_LIBERE_PLACE),
    ("Sans horaires", MODE_SANS_HORAIRES),
    ("Présence non facturée", MODE_PRESENCE_NON_FACTUREE),
    ("Sans horaire, systématique", MODE_SYSTEMATIQUE_SANS_HORAIRES),
    ("Permanence", MODE_PERMANENCE)
]

# Propriétaires des activités
ACTIVITY_OWNER_ALL = 0
ACTIVITY_OWNER_ENFANTS = 1
ACTIVITY_OWNER_SALARIES = 2

# Granularité du planning dans la base
BASE_GRANULARITY = 5  # 5 minutes
DAY_SIZE = 24 * 60 / BASE_GRANULARITY

# Modes d'inscription
MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1
MODE_5_5 = 2
MODE_4_5 = 4
MODE_3_5 = 8
MODE_FORFAIT_MENSUEL = 16
MODE_TEMPS_PARTIEL = 32
MODE_ACCUEIL_URGENCE = 64
MODE_FORFAIT_HEBDOMADAIRE = 128
MODE_MAX = MODE_FORFAIT_HEBDOMADAIRE

ModeAccueilItems = [
    ("Temps plein", MODE_5_5),
    ("Temps partiel", MODE_TEMPS_PARTIEL),
    # ("4/5èmes", MODE_4_5),
    # ("3/5èmes", MODE_3_5),
    ("Forfait horaire mensuel", MODE_FORFAIT_MENSUEL),
    ("Forfait horaire hebdomadaire", MODE_FORFAIT_HEBDOMADAIRE),
    ("Halte-garderie", MODE_HALTE_GARDERIE),
    ("Accueil urgence", MODE_ACCUEIL_URGENCE)
]

PeriodiciteFacturationItems = [
    ("Mensuelle", 1),
    ("Trimestrielle", 3),
    ("Semestrielle", 6),
    ("Annuelle", 12)
]

Regimes = [
    "Pas de sélection",
    "Régime général",
    "Régime de la fonction publique",
    "Régime MSA",
    "Régime EDF-GDF",
    "Régime RATP",
    "Régime Pêche maritime",
    "Régime Marins du Commerce",
    "Régime RSI",
    "Régime SNCF"
]

# Modes encaissement
ENCAISSEMENT_ESPECES = 0
ENCAISSEMENT_VIREMENT = 1
ENCAISSEMENT_CHEQUE = 2
ENCAISSEMENT_CESU = 3
ENCAISSEMENT_TIPI = 4
ENCAISSEMENT_TITRE_RECETTE = 5

ModesEncaissement = ("Espèces", "Virement", "Chèque", "Chèque CESU", "TIPI", "Titre de recette")

ModeEncaissementItems = [
    ("Espèces", ENCAISSEMENT_ESPECES),
    ("Virement", ENCAISSEMENT_VIREMENT),
    ("Chèque", ENCAISSEMENT_CHEQUE),
    ("Chèque CESU", ENCAISSEMENT_CESU),
    ("Titre de recette", ENCAISSEMENT_TITRE_RECETTE),
]

# Nombre de semaines de reference
MAX_SEMAINES_REFERENCE = 10

# Modes de facturation
FACTURATION_FORFAIT_10H = 0
FACTURATION_PSU = 1
FACTURATION_PAJE = 2
FACTURATION_HORAIRES_REELS = 3
FACTURATION_FORFAIT_MENSUEL = 4
FACTURATION_PSU_TAUX_PERSONNALISES = 5

# Modes de facturation de la période d'adaptation
PERIODE_ADAPTATION_FACTUREE_NORMALEMENT = 0
PERIODE_ADAPTATION_HORAIRES_REELS = 3
PERIODE_ADAPTATION_GRATUITE = 4

# Facturation début/fin de mois
FACTURATION_FIN_MOIS = 0
FACTURATION_DEBUT_MOIS_CONTRAT = 1
FACTURATION_DEBUT_MOIS_PREVISIONNEL = 2

# Modes de répartition
REPARTITION_MENSUALISATION_12MOIS = 0
REPARTITION_SANS_MENSUALISATION = 1
REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS = 2
REPARTITION_MENSUALISATION_CONTRAT = 3

# Periode de revenus
REVENUS_YM2 = 0
REVENUS_CAFPRO = 1

# Types des tarifs spéciaux
TARIF_SPECIAL_MAJORATION = 0
TARIF_SPECIAL_REDUCTION = 1
TARIF_SPECIAL_REMPLACEMENT = 2

# Unites des tarif spéciaux
TARIF_SPECIAL_UNITE_EUROS = 0
TARIF_SPECIAL_UNITE_POURCENTAGE = 1
TARIF_SPECIAL_UNITE_EUROS_PAR_HEURE = 2
TARIF_SPECIAL_UNITE_EUROS_PAR_JOUR = 3

# Mode de traitement des absences pour maladie
DEDUCTION_MALADIE_SANS_CARENCE = 0
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES = 1
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES = 2
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS = 3

# Mode de traitement des absences (congés / jours fériés)
ABSENCES_DEDUITES_EN_SEMAINES = 0
ABSENCES_DEDUITES_EN_JOURS = 1
ABSENCES_DEDUITES_SANS_LIMITE = 2

# Mode de gestion des congés à l'inscription
GESTION_CONGES_INSCRIPTION_SIMPLE = 1
GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT = 2

# Mode de facturation des activites
ACTIVITES_NON_FACTUREES = 0
ACTIVITES_FACTUREES_JOURNEE = 1
ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION = 3

# Options des conges
ACCUEIL_NON_FACTURE = 1  # jours de nettoyage par exemple
MOIS_SANS_FACTURE = 2  # si présence dans cette periode (mois d'août par exemple), elle est répartie sur les autres mois de l'année
MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP = 4  # si présence dans cette periode (mois d'août par exemple), le contrat réparti sur les autres mois de l'année, seules les suppléments / déductions sont facturés

ModeCongeItems = [
    ("Fermeture de l'établissement", 0),
    ("Accueil non facturé", ACCUEIL_NON_FACTURE),
    ("Pas de facture pendant ce mois", MOIS_SANS_FACTURE),
    ("Uniquement supplément/déduction", MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP)
]

# Modes d'arrondi des heures de presence
SANS_ARRONDI = 0
ARRONDI_HEURE = 1
ARRONDI_HEURE_ARRIVEE_DEPART = 2
ARRONDI_DEMI_HEURE = 3
ARRONDI_HEURE_MARGE_DEMI_HEURE = 4
ARRONDI_HEURE_PLUS_PROCHE = 5

# Modes d'arrondis des semaines
ARRONDI_SEMAINE_SUPERIEURE = 1
ARRONDI_SEMAINE_PLUS_PROCHE = 2

# Modes d'arrondis des factures
ARRONDI_EURO_PLUS_PROCHE = 2

# Modes de tri des enfants sur le planning
TRI_PRENOM = 0
TRI_NOM = 1
TRI_NOM_PARENTS = 3
TRI_GROUPE = 1024
TRI_SANS_SEPARATION = 256
TRI_LIGNES_CAHIER = 512

# Options affichage du planning
NO_ICONS = 1
READ_ONLY = 2
PRESENCES_ONLY = 4
NO_BOTTOM_LINE = 8
DRAW_NUMBERS = 16
COMMENTS = 32
TWO_PARTS = 64
ACTIVITES = 128
NO_LABELS = 256
DRAW_VALUES = 512
DEPASSEMENT_CAPACITE = 1024
NO_SCROLL = 2048
NO_SALARIES = 4096

# Types de lignes sur le planning (sert pour le Summary à séparer numérateur et dénominateur)
SUMMARY_NONE = 0
SUMMARY_ENFANT = 1
SUMMARY_SALARIE = 2

# Valeurs de présence
PRESENCE_SALARIE = -256
CONGES_PAYES = -8
CONGES_DEPASSEMENT = -7
ABSENCE_CONGE_SANS_PREAVIS = -6
MALADE_SANS_JUSTIFICATIF = -5 
ABSENCE_NON_PREVENUE = -4
HOPITAL = -3
MALADE = -2
VACANCES = -1
ABSENT = 0
PRESENT = 1 << 0  # activité 0
CLOTURE = 1 << 28  # pas d'activité > 27 !
SUPPLEMENT = 1 << 29
PREVISIONNEL = 1 << 30  # flag previsionnel

# Types des champs OpenOffice
FIELD_EUROS = 1
FIELD_SIGN = 2
FIELD_HEURES = 4

# IDs de boutons
ID_SYNCHRO = 10001
ID_UNDO = 10002

# Options
RESERVATAIRES = 1 << 0
HEURES_CONTRAT = 1 << 1
TABLETTE = 1 << 2
CATEGORIES = 1 << 3
DECLOTURE = 1 << 4
FACTURES_FAMILLES = 1 << 5
READONLY = 1 << 6
GROUPES_SITES = 1 << 7
NO_BACKUPS = 1 << 8
COMPATIBILITY_MODE_CONGES_2016 = 1 << 9
COMPATIBILITY_MODE_ADAPTATIONS_2016 = 1 << 10
PRELEVEMENTS_AUTOMATIQUES = 1 << 11
NEWSLETTERS = 1 << 12

# Atributs de plages horaires spéciales
PLAGE_FERMETURE = 0
PLAGE_INSECABLE = 1

# Paramètres pour les factures
NO_ADDRESS = 1 << 0
NO_NOM = 1 << 1
NO_REVENUS = 1 << 2
NO_PARENTS = 1 << 3
NO_NUMERO = 1 << 4
TRACES = 1 << 5
DEPART_ANTICIPE = 1 << 6

# Tranches PAJE
paje1 = 1
paje2 = 2
paje3 = 3

# Constantes tablette
TABLETTE_MARGE_ARRIVEE = 10

# Paramètres de clôture des factures
CLOTURE_FACTURES_OFF = 0
CLOTURE_FACTURES_SIMPLE = 1
CLOTURE_FACTURES_AVEC_CONTROLE = 2
