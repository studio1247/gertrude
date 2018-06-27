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

import sys
import os


days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
months_abbrev = ["Janv", "Fév", "Mars", "Avril", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]
ordinaux = ["1er", "2ème", "3ème", "4ème"]

# Sexe
MASCULIN = 1
FEMININ = 2

RelationsItems = [
    ("Parent manquant", None),
    ("Papa", MASCULIN),
    ("Maman", FEMININ),
    ]

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
    ("Bureau / direction", PROFIL_ALL),
    ("Equipe", PROFIL_ALL - PROFIL_FACTURATION),
    ("Inscriptions, planning et salariés", PROFIL_INSCRIPTIONS | PROFIL_PLANNING | PROFIL_SALARIES),
    ("Inscriptions et planning", PROFIL_INSCRIPTIONS | PROFIL_PLANNING),
    ("Planning et salariés", PROFIL_PLANNING | PROFIL_SALARIES),
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

# Propriétaires des activités
ACTIVITY_OWNER_ALL = 0
ACTIVITY_OWNER_ENFANTS = 1
ACTIVITY_OWNER_SALARIES = 2

# Granularité du planning dans la base
BASE_GRANULARITY = 5  # 5 minutes
DAY_SIZE = 24 * 60 // BASE_GRANULARITY

# Modes d'inscription
MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1
MODE_TEMPS_PLEIN = 2
MODE_FORFAIT_MENSUEL = 16
MODE_TEMPS_PARTIEL = 32
MODE_ACCUEIL_URGENCE = 64
MODE_FORFAIT_HEBDOMADAIRE = 128
MODE_FORFAIT_GLOBAL_CONTRAT = 256
MODE_MAX = MODE_FORFAIT_GLOBAL_CONTRAT
TOUS_MODES_ACCUEIL = 1023

ModeAccueilItems = [
    ("Temps plein", MODE_TEMPS_PLEIN),
    ("Temps partiel", MODE_TEMPS_PARTIEL),
    ("Forfait horaire mensuel", MODE_FORFAIT_MENSUEL),
    ("Forfait horaire hebdomadaire", MODE_FORFAIT_HEBDOMADAIRE),
    ("Forfait horaire global sur la durée du contrat", MODE_FORFAIT_GLOBAL_CONTRAT),
    ("Halte-garderie", MODE_HALTE_GARDERIE),
    ("Accueil urgence", MODE_ACCUEIL_URGENCE)
]

PeriodiciteFacturationItems = [
    ("Mensuelle", 1),
    ("Trimestrielle", 3),
    ("Quadrimestrielle", 4),
    ("Semestrielle", 6),
    ("Annuelle", 12)
]

# Régimes CAF
REGIME_CAF_NONE = 0
REGIME_CAF_GENERAL = 1
REGIME_CAF_FONCTION_PUBLIQUE = 2
REGIME_CAF_MSA = 3
REGIME_CAF_EDF_GDF = 4
REGIME_CAF_RATP = 5
REGIME_CAF_PECHE_MARITIME = 6
REGIME_CAF_MARINS_DU_COMMERCE = 7
REGIME_CAF_RSI = 8
REGIME_CAF_SNCF = 9

RegimesCAF = [
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
FACTURATION_PAJE_10H = 6

# Modes de facturation de la période d'adaptation
PERIODE_ADAPTATION_FACTUREE_NORMALEMENT = 0
PERIODE_ADAPTATION_HORAIRES_REELS = 3
PERIODE_ADAPTATION_GRATUITE = 4
PERIODE_ADAPTATION_FACTUREE_NORMALEMENT_SANS_HEURES_SUPPLEMENTAIRES = 5

TypeModesFacturationItems = [
    ("Facturation normale", PERIODE_ADAPTATION_FACTUREE_NORMALEMENT),
    ("Facturation aux horaires réels", PERIODE_ADAPTATION_HORAIRES_REELS),
    ("Période d'adaptation gratuite", PERIODE_ADAPTATION_GRATUITE),
    ("Facturation normale, mais sans heures supplémentaires", PERIODE_ADAPTATION_FACTUREE_NORMALEMENT_SANS_HEURES_SUPPLEMENTAIRES)
]

# Facturation début/fin de mois
FACTURATION_FIN_MOIS = 0
FACTURATION_DEBUT_MOIS_CONTRAT = 1
FACTURATION_DEBUT_MOIS_PREVISIONNEL = 2

# Modes de répartition
REPARTITION_MENSUALISATION_12MOIS = 0
REPARTITION_SANS_MENSUALISATION = 1
REPARTITION_SPARE = 2
REPARTITION_MENSUALISATION_CONTRAT = 3

# Modes de prorata
PRORATA_NONE = 0
PRORATA_JOURS_OUVRES = 1
PRORATA_MOIS_COMPLET = 2

# Periode de revenus
REVENUS_YM2 = 0
REVENUS_CAFPRO = 1

# Types des tarifs spéciaux
TARIF_SPECIAL_MAJORATION = 0
TARIF_SPECIAL_REDUCTION = 1
TARIF_SPECIAL_REMPLACEMENT = 2

TypeTarifsSpeciauxItems = [
    ("Majoration", TARIF_SPECIAL_MAJORATION),
    ("Réduction", TARIF_SPECIAL_REDUCTION),
    ("Tarif de remplacement", TARIF_SPECIAL_REMPLACEMENT)
]

# Portée des tarifs spéciaux
PORTEE_INSCRIPTION = 0
PORTEE_CONTRAT = 1

PorteeTarifsSpeciauxItems = [
    ("Inscription (tous les contrats)", PORTEE_INSCRIPTION),
    ("Contrat", PORTEE_CONTRAT)
]

# Unités des tarifs horaires
TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE = 0
TARIF_HORAIRE_UNITE_EUROS_PAR_MOIS = 1

UniteTarifsHorairesItems = [
    ("€/heure", TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE),
    ("€/mois", TARIF_HORAIRE_UNITE_EUROS_PAR_MOIS),
]

# Unités des tarifs spéciaux
TARIF_SPECIAL_UNITE_EUROS = 0
TARIF_SPECIAL_UNITE_POURCENTAGE = 1
TARIF_SPECIAL_UNITE_EUROS_PAR_HEURE = 2
TARIF_SPECIAL_UNITE_EUROS_PAR_JOUR = 3

UniteTarifsSpeciauxItems = [
    ("€", TARIF_SPECIAL_UNITE_EUROS),
    ("%", TARIF_SPECIAL_UNITE_POURCENTAGE),
    ("€/heure", TARIF_SPECIAL_UNITE_EUROS_PAR_HEURE),
    ("€/jour de présence", TARIF_SPECIAL_UNITE_EUROS_PAR_JOUR)
]

# Mode de traitement des absences pour maladie
DEDUCTION_MALADIE_SANS_CARENCE = 0
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES = 1
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES = 2
DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS = 3

# Mode de traitement des absences (congés / jours fériés)
ABSENCES_DEDUITES_EN_SEMAINES = 0
ABSENCES_DEDUITES_EN_JOURS = 1
ABSENCES_DEDUITES_SANS_LIMITE = 2

# Modes d'absences prévues au contrat
ABSENCES_PREVUES_AU_CONTRAT_AUCUNE = 0
ABSENCES_PREVUES_AU_CONTRAT_MENSUALISEES = 1
ABSENCES_PREVUES_AU_CONTRAT_MENSUALISEES_AVEC_POSSIBILITE_HEURES_SUPPLEMENTAIRES = 2

# Mode de gestion des congés à l'inscription
GESTION_CONGES_INSCRIPTION_AUCUNE = 0
GESTION_CONGES_INSCRIPTION_MENSUALISES = 1
GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT = 2
GESTION_CONGES_INSCRIPTION_NON_MENSUALISES = 3
modes_absences_prevues_au_contrat = [
    ("Non", GESTION_CONGES_INSCRIPTION_AUCUNE),
    ("Oui, avec mensualisation", GESTION_CONGES_INSCRIPTION_MENSUALISES),
    ("Oui, avec mensualisation, et possibilité d'heures supplémentaires", GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT),
    ("Oui, sans mensualisation", GESTION_CONGES_INSCRIPTION_NON_MENSUALISES),
]

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
ARRONDI_SEMAINE_AVEC_LIMITE_52_SEMAINES = 3

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
CONGES_RECUP_HEURES_SUPP = -11
CONGES_MATERNITE = -10
CONGES_SANS_SOLDE = -9
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
SUPPLEMENT = 1 << 30

# Modes des activités
MODE_PRESENCE = 0
MODE_NORMAL = 1
MODE_LIBERE_PLACE = 2
MODE_PRESENCE_SUPPLEMENTAIRE = 3
MODE_PRESENCE_NON_FACTUREE = 4
MODE_SYSTEMATIQUE_SANS_HORAIRES = 5
MODE_PERMANENCE = 6
MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE = 7
MODE_SALARIE_HEURES_SUPP = 8
MODE_SALARIE_RECUP_HEURES_SUPP = 9
MODE_SANS_HORAIRES = 10
MODE_CONGES = 11
MODE_PLACE_SOUHAITEE = 12
MODE_ABSENCE_NON_PREVENUE = 13

ActivityModes = [
    ("Normal", MODE_NORMAL),
    ("Présence non facturée", MODE_PRESENCE_NON_FACTUREE),
    ("Présence facturée en temps supplémentaire", MODE_PRESENCE_SUPPLEMENTAIRE),
    ("Libère une place", MODE_LIBERE_PLACE),
    ("Place souhaitée", MODE_PLACE_SOUHAITEE),
    ("Permanence", MODE_PERMANENCE),
    ("Congés", MODE_CONGES),
    ("Absence non prévenue", MODE_ABSENCE_NON_PREVENUE),
    ("Heures supp. (salariés)", MODE_SALARIE_HEURES_SUPP),
    ("Récup heures supp. (salariés)", MODE_SALARIE_RECUP_HEURES_SUPP),
    ("Sans horaires", MODE_SANS_HORAIRES),
    ("Sans horaire, systématique", MODE_SYSTEMATIQUE_SANS_HORAIRES),
    ("Sans horaire, systématique et mensualisé", MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE),
]

# Libellés par défaut
STATE_LABELS = {
    MODE_PRESENCE: "Présences",
    PRESENCE_SALARIE: "Présences salariés",
    VACANCES: "Vacances",
    MALADE: "Malade",
    HOPITAL: "Maladie avec hospitalisation",
    ABSENCE_NON_PREVENUE: "Absence non prévenue",
    MALADE_SANS_JUSTIFICATIF: "Maladie sans justificatif",
    ABSENCE_CONGE_SANS_PREAVIS: "Congés sans préavis",
    CONGES_DEPASSEMENT: "Absence non déductible (dépassement)",
    CONGES_PAYES: "Congés payés",
    CONGES_SANS_SOLDE: "Congés sans solde",
    CONGES_MATERNITE: "Congés maternité",
    CONGES_RECUP_HEURES_SUPP: "Récupération heures supp."
}

# Equivalences
PRESENCE_CAROUSSEL = {
    PRESENT: PRESENT,
    PRESENCE_SALARIE: PRESENT,
    VACANCES: VACANCES,
    CONGES_PAYES: CONGES_PAYES,
    CONGES_DEPASSEMENT: VACANCES,
    ABSENT: ABSENT,
    ABSENCE_CONGE_SANS_PREAVIS: ABSENCE_CONGE_SANS_PREAVIS,
    ABSENCE_NON_PREVENUE: ABSENCE_NON_PREVENUE,
    MALADE: MALADE,
    MALADE_SANS_JUSTIFICATIF: MALADE_SANS_JUSTIFICATIF,
    HOPITAL: HOPITAL
}

# Types des champs OpenOffice
FIELD_EUROS = 1
FIELD_HEURES = 2
FIELD_DATE = 4
FIELD_SIGN = 256

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
REGLEMENTS = 1 << 13
COMPATIBILITY_MODE_DECOMPTE_SEMAINES_2017 = 1 << 14
FRAIS_INSCRIPTION_RESERVATAIRES = 1 << 15
TARIFS_SPECIAUX = 1 << 16
NO_PASSWORD = 1 << 17
ALERTES_NON_PAIEMENT = 1 << 18
GESTION_REPAS = 1 << 19
TARIFS_SPECIAUX_LABELS = 1 << 20
PREINSCRIPTIONS_ONLY = 1 << 21
NOTIFICATION_PLACES_DISPONIBLES = 1 << 22
COMPATIBILITY_MODE_HEURES_FACTUREES_2017 = 1 << 23

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
NO_RESTORE_CLOTURE = 1 << 7

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

# Alertes
ALERTE_3MOIS_AVANT_AGE_MAXIMUM = 1
ALERTE_1AN_APRES_INSCRIPTION = 2
ALERTE_2MOIS_AVANT_FIN_INSCRIPTION = 4

AlertesItems = [
    ("3 mois avant l'âge maximum", ALERTE_3MOIS_AVANT_AGE_MAXIMUM),
    ("1 an après l'arrivée", ALERTE_1AN_APRES_INSCRIPTION),
    ("2 mois avant le départ", ALERTE_2MOIS_AVANT_FIN_INSCRIPTION)
]

OrdreAffichageItems = [
    ("Par prénom", TRI_PRENOM),
    ("Par nom", TRI_NOM)
]

# Types de connection
CONNECTION_TYPE_FILE = 0
CONNECTION_TYPE_SHARED_FILE = 1
CONNECTION_TYPE_HTTP = 2

# Types de gestion salariés
GESTION_SIMPLE_PLANNINGS_SALARIES = 0
GESTION_GLOBALE_PLANNINGS_SALARIES = 1

modes_gestion_plannings_salaries = [
    ("Planning spécifique à chaque salarié", GESTION_SIMPLE_PLANNINGS_SALARIES),
    ("Planning global pour l'équipe", GESTION_GLOBALE_PLANNINGS_SALARIES),
]

# Type de repas
REPAS_PUREE = 0
REPAS_MORCEAUX = 1

types_repas_1 = [
    ("Purée", REPAS_PUREE),
    ("Morceaux", REPAS_MORCEAUX)
]

# Type de repas (2ème choix)
REPAS_ASSIETTE = 0
REPAS_PETIT_POT = 1
REPAS_BIBERON = 2

types_repas_2 = [
    ("Assiette", REPAS_ASSIETTE),
    ("Petit pot", REPAS_PETIT_POT),
    ("Biberon", REPAS_BIBERON)
]

# Type de congés des salariés
types_conges_salaries = [
    ("Congés payés", CONGES_PAYES),
    ("Congés sans solde", CONGES_SANS_SOLDE),
    ("Congés maladie", MALADE),
    ("Congés maternité", CONGES_MATERNITE)
]

# Type d'export de coordonnées des parents
EXPORT_FAMILLES_PRESENTES = 1
EXPORT_FAMILLES_FUTURES = 2
EXPORT_FAMILLES_PARTIES = 4
type_export_coordonnees_parents = [
    ("Familles présentes", EXPORT_FAMILLES_PRESENTES),
    ("Familles présentes et futures", EXPORT_FAMILLES_PRESENTES + EXPORT_FAMILLES_FUTURES),
    ("Familles parties", EXPORT_FAMILLES_PARTIES)
]

# Etats de préinscription
STATE_PREINSCRIPTION_RECUE = 0
STATE_ATTENTE_ENTRETIEN = 1
STATE_ENTRETIEN_PROGRAMME = 2
STATE_DEVIS_A_ENVOYER = 3
STATE_ATTENTE_REPONSE_PARENTS = 4
STATE_ACCORD_PARENTS = 5
STATE_REFUS_PARENTS = 6
STATE_EN_LISTE_ATTENTE = 7
STATE_DOSSIER_ACCEPTE = 8
STATE_DOSSIER_REFUSE = 9

# Types d'envoi email
ENVOI_CAF = "Envoi CAF"
ENVOI_PARENTS = "Envoi aux parents"
ENVOI_SALARIES = "Envoi aux salariés"
ENVOI_RESERVATAIRES = "Envoi aux réservataires"