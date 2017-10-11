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
from __future__ import print_function
from __future__ import division

import operator
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *
from sqlalchemy_utils import database_exists
from sqlalchemy.orm.collections import MappedCollection, collection, attribute_mapped_collection, InstrumentedList
from helpers import *
from parameters import *
from config import config

DB_VERSION = 115

Base = declarative_base()

KEY_VERSION = "VERSION"


class DBSettings(Base):
    __tablename__ = "data"
    key = Column(String, primary_key=True)
    value = Column(String)


class Creche(Base):
    __tablename__ = "creche"
    idx = Column(Integer, primary_key=True)
    nom = Column(String)
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    telephone = Column(String)
    ouverture = Column(Float, default=7.5)
    fermeture = Column(Float, default=18.5)
    affichage_min = Column(Float, default=7)
    affichage_max = Column(Float, default=19)
    granularite = Column(Integer, default=15)
    preinscriptions = Column(Boolean, default=False)
    presences_previsionnelles = Column(Boolean, default=False)
    presences_supplementaires = Column(Boolean, default=True)
    modes_inscription = Column(Integer, default=MODE_HALTE_GARDERIE + MODE_4_5 + MODE_3_5)
    minimum_maladie = Column(Integer, default=3)
    email = Column(String)
    type = Column(Integer, default=TYPE_PARENTAL)
    mode_saisie_planning = Column(Integer, default=SAISIE_HORAIRE)
    periode_revenus = Column(Integer, default=REVENUS_YM2)
    mode_facturation = Column(Integer, default=FACTURATION_PSU)
    temps_facturation = Column(Integer, default=FACTURATION_FIN_MOIS)
    repartition = Column(Integer, default=REPARTITION_MENSUALISATION_12MOIS)
    conges_inscription = Column(Integer, default=0)
    tarification_activites = Column(Integer, default=0)
    traitement_maladie = Column(Integer, default=DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES)
    facturation_jours_feries = Column(Integer, default=ABSENCES_DEDUITES_EN_SEMAINES)
    facturation_periode_adaptation = Column(Integer, default=PERIODE_ADAPTATION_FACTUREE_NORMALEMENT)
    formule_taux_effort = Column(String, default="None")
    masque_alertes = Column(Integer, default=0)
    age_maximum = Column(Integer, default=3)
    seuil_alerte_inscription = Column(Integer, default=3)
    cloture_facturation = Column(Integer, default=0)
    arrondi_heures = Column(Integer, default=SANS_ARRONDI)
    arrondi_facturation = Column(Integer, default=SANS_ARRONDI)
    arrondi_facturation_periode_adaptation = Column(Integer, default=SANS_ARRONDI)
    arrondi_mensualisation = Column(Integer, default=ARRONDI_HEURE_PLUS_PROCHE)
    arrondi_heures_salaries = Column(Integer, default=SANS_ARRONDI)
    arrondi_mensualisation_euros = Column(Integer, default=SANS_ARRONDI)
    arrondi_semaines = Column(Integer, default=ARRONDI_SEMAINE_SUPERIEURE)
    gestion_maladie_hospitalisation = Column(Boolean, default=False)
    tri_inscriptions = Column(Integer, default=TRI_NOM)
    tri_planning = Column(Integer, default=TRI_NOM)
    tri_factures = Column(Integer, default=TRI_NOM)
    smtp_server = Column(String)
    caf_email = Column(String)
    mode_accueil_defaut = Column(Integer, default=MODE_TEMPS_PARTIEL)
    gestion_absences_non_prevenues = Column(Boolean, default=False)
    gestion_maladie_sans_justificatif = Column(Boolean, default=False)
    gestion_preavis_conges = Column(Boolean, default=False)
    gestion_depart_anticipe = Column(Boolean)
    alerte_depassement_planning = Column(Boolean, default=False)
    last_tablette_synchro = Column(String)
    changement_groupe_auto = Column(Boolean, default=False)
    allergies = Column(String)
    regularisation_fin_contrat = Column(Boolean, default=True)
    regularisation_conges_non_pris = Column(Boolean, default=True)
    date_raz_permanences = Column(Date)
    conges_payes_salaries = Column(Integer, default=25)
    conges_supplementaires_salaries = Column(Integer, default=0)
    cout_journalier = Column(Float, default=0)
    iban = Column(String)
    bic = Column(String)
    creditor_id = Column(String)
    siret = Column(String)
    users = relationship("User", backref="creche", cascade="all, delete-orphan")
    sites = relationship("Site", backref="creche", cascade="all, delete-orphan")
    categories = relationship("Categorie", backref="creche", cascade="all, delete-orphan")
    groupes = relationship("Groupe", backref="creche", cascade="all, delete-orphan")
    reservataires = relationship("Reservataire", backref="creche", cascade="all, delete-orphan")
    tarifs_horaires = relationship("TarifHoraire", backref="creche", cascade="all, delete-orphan")
    tarifs_speciaux = relationship("TarifSpecial", backref="creche", cascade="all, delete-orphan")
    inscrits = relationship("Inscrit", backref="creche", cascade="all, delete-orphan")
    salaries = relationship("Salarie", backref="creche", cascade="all, delete-orphan")
    activites = relationship("Activite", collection_class=attribute_mapped_collection("value"), backref="creche", cascade="all, delete-orphan")
    plages_horaires = relationship("PlageHoraire", backref="creche", cascade="all, delete-orphan")
    conges = relationship("CongeStructure", backref="creche", cascade="all, delete-orphan")
    baremes_caf = relationship("BaremeCAF", backref="creche", cascade="all, delete-orphan")

    def __init__(self):
        self.periodes_fermeture = {}
        self.jours_fermeture = {}
        self.jours_fete = set()
        self.jours_weekend = []
        self.mois_sans_facture = {}
        self.mois_facture_uniquement_heures_supp = {}
        self.liste_conges = []

    @reconstructor
    def init_on_load(self):
        self.periodes_fermeture = {}
        self.jours_fermeture = {}
        self.jours_fete = set()
        self.jours_weekend = []
        self.mois_sans_facture = {}
        self.mois_facture_uniquement_heures_supp = {}
        jours_feries_creche = self.get_jours_feries()
        for year in range(config.first_date.year, config.last_date.year + 1):
            self.mois_sans_facture[year] = set()
            self.mois_facture_uniquement_heures_supp[year] = set()
            for label, func, enable in jours_fermeture:
                if label in jours_feries_creche:
                    for j in func(year):
                        self.jours_fermeture[j] = jours_feries_creche[label]
                        if label == "Week-end":
                            self.jours_weekend.append(j)
        self.jours_feries = self.jours_fermeture.keys()
        self.jours_fete = set(self.jours_feries) - set(self.jours_weekend)
        self.jours_conges = set()
        self.liste_conges = []

        def add_periode(debut, fin, conge):
            date = debut
            while date <= fin:
                self.periodes_fermeture[date] = conge
                self.jours_fermeture[date] = conge
                if date not in self.jours_feries:
                    self.jours_conges.add(date)
                date += datetime.timedelta(1)
            self.liste_conges.append((debut, fin))

        for conge in self.conges:
            if conge.options == MOIS_SANS_FACTURE:
                date = str2date(conge.debut, day=1)
                if date and date.year in self.mois_sans_facture.keys():
                    self.mois_sans_facture[date.year].add(date.month)
                elif conge.debut in months:
                    mois = months.index(conge.debut) + 1
                    for key in self.mois_sans_facture:
                        self.mois_sans_facture[key].add(mois)
                else:
                    try:
                        mois = int(conge.debut)
                        for key in self.mois_sans_facture:
                            self.mois_sans_facture[key].add(mois)
                    except Exception as e:
                        print("Exception dans les périodes de congé", e)
            elif conge.options == MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP:
                date = str2date(conge.debut, day=1)
                if date and date.year in self.mois_facture_uniquement_heures_supp.keys():
                    self.mois_facture_uniquement_heures_supp[date.year].add(date.month)
                elif conge.debut in months:
                    mois = months.index(conge.debut) + 1
                    for key in self.mois_facture_uniquement_heures_supp:
                        self.mois_facture_uniquement_heures_supp[key].add(mois)
                else:
                    try:
                        mois = int(conge.debut)
                        for key in self.mois_facture_uniquement_heures_supp:
                            self.mois_facture_uniquement_heures_supp[key].add(mois)
                    except Exception as e:
                        print("Exception dans les périodes de congé", e)
            else:
                try:
                    count = conge.debut.count('/')
                    if count == 2:
                        debut = str2date(conge.debut)
                        if conge.fin.strip() == "":
                            fin = debut
                        else:
                            fin = str2date(conge.fin)
                        add_periode(debut, fin, conge)
                    elif count == 1:
                        for year in range(config.first_date.year, config.last_date.year + 1):
                            debut = str2date(conge.debut, year)
                            if conge.fin.strip() == "":
                                fin = debut
                            else:
                                fin = str2date(conge.fin, year)
                            add_periode(debut, fin, conge)
                except Exception as e:
                    print("Exception dans les périodes de congé", e)

        self.jours_fete = list(self.jours_fete)
        self.jours_feries = list(self.jours_feries)
        self.jours_conges = list(self.jours_conges)

    def GetHeuresAccueil(self, jour):
        result = 0.0
        print("TODO GetHeuresAccueil")
        return result
        for start, end, value in self.tranches_capacite[jour].activites:
            result += value * (end - start)
        return result / 12

    def GetCapacite(self, jour=None, tranche=None):
        if jour is None:
            jours, result = 0, 0.0
            for jour in range(7):
                if self.is_jour_semaine_travaille(jour):
                    jours += 1
                    result += self.GetCapacite(jour)
            return result / jours
        elif tranche is None:
            return self.GetHeuresAccueil(jour) / self.get_amplitude_horaire()
        else:
            for start, end, value in self.tranches_capacite[jour].activites:
                if start <= tranche < end:
                    return value
            else:
                return 0

    def get_jours_feries(self):
        # TODO separer les jours fériés des périodes de congés
        result = {}
        for conge in self.conges:
            if conge.is_jour_ferie():
                result[conge.debut] = conge
        return result

    def is_jour_semaine_travaille(self, day):
        # TODO optimisation
        day %= 7
        jours_feries_creche = self.get_jours_feries()
        if days[day] in jours_feries_creche:
            return False
        elif day == 5 or day == 6:
            return "Week-end" not in jours_feries_creche
        else:
            return True

    def get_nombre_jours_semaine_travailles(self):
        result = 0
        for day in range(7):
            if self.is_jour_semaine_travaille(day):
                result += 1
        return result

    def get_amplitude_horaire(self):
        return self.fermeture - self.ouverture

    def get_allergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",") if allergie.strip()]

    def are_revenus_needed(self):
        if self.mode_facturation in (FACTURATION_FORFAIT_10H, FACTURATION_PSU, FACTURATION_PSU_TAUX_PERSONNALISES):
            return True
        elif self.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            return False
        for tarif in self.tarifs_horaires:
            if tarif.formule:
                for cas in tarif.formule:
                    if "revenus" in cas[0] or "paje" in cas[0]:
                        return True
        return False

    def GetPlagesOuvertureArray(self, affichage=False, conversion=True):
        if affichage:
            result = [(self.affichage_min, self.affichage_max)]
        else:
            result = [(self.ouverture, self.fermeture)]
        for plage in self.plages_horaires:
            if plage.flags == PLAGE_FERMETURE and plage.debut and plage.fin > plage.debut:
                for i, (debut, fin) in enumerate(result):
                    if plage.debut > debut and plage.fin < fin:
                        result[i] = (debut, plage.debut)
                        result.insert(i + 1, (plage.fin, fin))
                        break
        if conversion:
            result = [(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))) for debut, fin in
                      result]
        return result

    def GetPlagesArray(self, plage_type, conversion=True):
        result = []
        for plage in self.plages_horaires:
            if plage.flags == plage_type and plage.debut and plage.fin > plage.debut:
                result.append((plage.debut, plage.fin))
        if conversion:
            result = [(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))) for debut, fin in
                      result]
        return result

    def get_activites_avec_horaires(self):
        return [activite for activite in self.activites.values() if activite.has_horaires()]

    def get_activites_sans_horaires(self):
        return [activite for activite in self.activites.values() if activite.mode == MODE_SANS_HORAIRES]

    def has_activites_avec_horaires(self):
        return len(self.get_activites_avec_horaires()) > 1


class Site(Base):
    __tablename__ = "sites"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    nom = Column(String)
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    telephone = Column(String)
    capacite = Column(Integer)
    groupe = Column(Integer)


class Bureau(Base):
    __tablename__ = "bureaux"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(Date)
    fin = Column(Date)
    president = Column(String)
    vice_president = Column(String)
    tresorier = Column(String)
    secretaire = Column(String)
    directeur = Column(String)
    gerant = Column(String)
    directeur_adjoint = Column(String)
    comptable = Column(String)


class BaremeCAF(Base):
    __tablename__ = "baremescaf"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(Date)
    fin = Column(Date)
    plancher = Column(Integer)
    plafond = Column(Integer)


class TarifHoraire(Base):
    __tablename__ = "tarifs_horaires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(Date)
    fin = Column(Date)
    formule = Column(String)


class Reservataire(Base):
    __tablename__ = "reservataires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(Date)
    fin = Column(Date)
    nom = Column(String)
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    telephone = Column(String)
    email = Column(String)
    places = Column(Integer)
    heures_jour = Column(Float)
    heures_semaine = Column(Float)
    options = Column(Integer)
    periode_facturation = Column(Integer)
    delai_paiement = Column(Integer)
    tarif = Column(Float)


class Activite(Base):
    __tablename__ = "activities"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    label = Column(String)
    value = Column(Integer)
    mode = Column(Integer)
    couleur = Column(String)
    couleur_supplement = Column(String)
    couleur_previsionnel = Column(String)
    formule_tarif = Column(String)
    owner = Column(Integer)

    def has_horaires(self):
        return self.mode in (MODE_NORMAL, MODE_LIBERE_PLACE, MODE_PRESENCE_NON_FACTUREE, MODE_PERMANENCE)


class ContratSalarie(Base):
    __tablename__ = "contrats"
    idx = Column(Integer, primary_key=True)
    employe_id = Column(Integer, ForeignKey("employes.idx"))
    site_id = Column(Integer, ForeignKey("sites.idx"))
    site = relationship("Site")
    debut = Column(Date)
    fin = Column(Date)
    fonction = Column(String)
    duree_reference = Column(Integer)
    timeslots = relationship("TimeslotContratSalarie", backref="contrat", cascade="all, delete-orphan")


class Salarie(Base):
    __tablename__ = "employes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    prenom = Column(String)
    nom = Column(String)
    telephone_domicile = Column(String)
    telephone_domicile_notes = Column(String)
    telephone_portable = Column(String)
    telephone_portable_notes = Column(String)
    email = Column(String)
    diplomes = Column(String)
    combinaison = Column(String)
    contrats = relationship("ContratSalarie", backref="salarie", cascade="all, delete-orphan")
    conges = relationship("CongeSalarie", backref="_salarie", cascade="all, delete-orphan")
    timeslots = relationship("DaySlotSalarie", backref="_salarie", cascade="all, delete-orphan")
    commentaires = relationship("CommentaireSalarie", backref="_salarie", cascade="all, delete-orphan")


class Professeur(Base):
    __tablename__ = "professeurs"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    prenom = Column(String)
    nom = Column(String)
    entree = Column(Date)
    sortie = Column(Date)


class Famille(Base):
    __tablename__ = "familles"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    numero_securite_sociale = Column(String)
    numero_allocataire_caf = Column(String)
    medecin_traitant = Column(String)
    telephone_medecin_traitant = Column(String)
    assureur = Column(String)
    numero_police_assurance = Column(String)
    code_client = Column(String)
    tarifs = Column(Integer)
    notes = Column(String)
    iban = Column(String)
    bic = Column(String)
    mandate_id = Column(String)
    jour_prelevement_automatique = Column(Integer)
    date_premier_prelevement_automatique = Column(Date)
    inscrits = relationship("Inscrit", backref="famille", cascade="all, delete-orphan")
    freres_soeurs = relationship("Fratrie", backref="famille", cascade="all, delete-orphan")
    parents = relationship("Parent", backref="_famille", cascade="all, delete-orphan")
    referents = relationship("Referent", backref="famille", cascade="all, delete-orphan")
    encaissements = relationship("EncaissementFamille", backref="_famille", cascade="all, delete-orphan")


class Inscrit(Base):
    __tablename__ = "inscrits"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    prenom = Column(String)
    nom = Column(String)
    sexe = Column(Integer)
    naissance = Column(Date)
    handicap = Column(Boolean)
    marche = Column(Boolean)
    photo = Column(String)
    notes = Column(String)
    combinaison = Column(String)
    categorie_id = Column(Integer, ForeignKey("categories.idx"))
    categorie = relationship("Categorie")
    allergies = Column(String)
    garde_alternee = Column(Boolean)
    inscriptions = relationship("Inscription", cascade="all, delete-orphan")
    days = relationship("TimeslotInscrit", collection_class=lambda: DayCollection("date"), backref="inscrit", cascade="all, delete-orphan")
    weekslots = relationship("WeekSlotInscrit", backref="inscrit", cascade="all, delete-orphan")
    commentaires = relationship("CommentaireInscrit", backref="inscrit", cascade="all, delete-orphan")
    factures = relationship("Facture", backref="inscrit", cascade="all, delete-orphan")
    conges = relationship("CongeInscrit", backref="_inscrit", cascade="all, delete-orphan")
    corrections = relationship("Correction", backref="inscrit", cascade="all, delete-orphan")

    @reconstructor
    def init_on_load(self):
        self.jours_conges = {}

        def AddPeriode(debut, fin, conge):
            date = debut
            while date <= fin:
                if date not in self.creche.jours_fermeture:
                    self.jours_conges[date] = conge
                date += datetime.timedelta(1)

        for conge in self.conges:
            try:
                count = conge.debut.count('/')
                if count == 2:
                    debut = str2date(conge.debut)
                    if conge.fin.strip() == "":
                        fin = debut
                    else:
                        fin = str2date(conge.fin)
                    AddPeriode(debut, fin, conge)
                elif count == 1:
                    for year in range(config.first_date.year, config.last_date.year + 1):
                        debut = str2date(conge.debut, year)
                        if conge.fin.strip() == "":
                            fin = debut
                        else:
                            fin = str2date(conge.fin, year)
                        AddPeriode(debut, fin, conge)
            except Exception as e:
                print("Exception congés inscription de %s %s" % (self.prenom, self.nom), e)

    def get_mode_arrondi(self):
        return self.creche.arrondi_heures

    def get_allergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",")]

    def GetInscription(self, date, preinscription=False, departanticipe=True, array=False):
        result = []
        for inscription in self.inscriptions:
            if (preinscription or not self.creche.preinscriptions or not inscription.preinscription) and \
                    inscription.debut and date >= inscription.debut and (not inscription.fin or date <= inscription.fin) \
                    and (not departanticipe or not inscription.depart or date <= inscription.depart):
                if array:
                    result.append(inscription)
                else:
                    return inscription
        if array:
            return result
        else:
            return None

    def GetInscriptions(self, date_debut=None, date_fin=None, site=None, preinscriptions=False):
        result = []
        if not date_debut:
            date_debut = datetime.date.min
        if not date_fin:
            date_fin = datetime.date.max
        for inscription in self.inscriptions:
            if (site is None or site == inscription.site) and (preinscriptions or not self.creche.preinscriptions or not inscription.preinscription) and inscription.debut:
                try:
                    date_debut_periode = inscription.debut
                    if inscription.fin:
                        date_fin_periode = inscription.fin
                    else:
                        date_fin_periode = datetime.date.max
                    if date_fin_periode < date_debut_periode:
                        print("Période incorrecte pour %s %s :" % (self.prenom, self.nom), date_debut_periode, date_fin_periode)
                        continue
                    if (date_debut_periode <= date_debut <= date_fin_periode) or (date_debut_periode <= date_fin <= date_fin_periode) or (date_debut < date_debut_periode and date_fin > date_fin_periode):
                        result.append(inscription)
                except Exception as e:
                    print("Exception inscriptions", e)
        result.sort(key=lambda i: i.debut)
        return result

    def is_date_conge(self, date):
        return date in self.creche.jours_fermeture or date in self.jours_conges

    def get_state(self, date):
        if self.is_date_conge(date):
            return ABSENT
        elif date in self.days:
            return self.days[date].get_state()
        else:
            inscription = self.GetInscription(date)
            return inscription.get_day_from_date(date).get_state() if inscription else ABSENT


class Parent(Base):
    __tablename__ = "parents"
    idx = Column(Integer, primary_key=True)
    famille = Column(Integer, ForeignKey("familles.idx"))
    relation = Column(String)
    prenom = Column(String)
    nom = Column(String)
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    telephone_domicile = Column(String)
    telephone_domicile_notes = Column(String)
    telephone_portable = Column(String)
    telephone_portable_notes = Column(String)
    telephone_travail = Column(String)
    telephone_travail_notes = Column(String)
    profession = Column(String)
    email = Column(String)
    revenus = relationship("Revenu", backref="parent", cascade="all, delete-orphan")


class Fratrie(Base):
    __tablename__ = "fratries"
    idx = Column(Integer, primary_key=True)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    prenom = Column(String)
    naissance = Column(Date)
    entree = Column(Date)
    sortie = Column(Date)


class Referent(Base):
    __tablename__ = "referents"
    idx = Column(Integer, primary_key=True)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    prenom = Column(String)
    nom = Column(String)
    telephone = Column(String)


class Timeslot(object):
    def __init__(self, debut, fin, value):
        self.debut = debut
        self.fin = fin
        self.value = value

    def is_checkbox(self):
        return self.debut is None

    def is_presence(self):
        return self.value in (0, PREVISIONNEL)


class Day(object):
    def __init__(self):
        self.timeslots = InstrumentedList()

    def get_state(self):
        for timeslot in self.timeslots:
            if timeslot.value < 0:
                return timeslot.value
            elif timeslot.value == 0:
                return PRESENT
        return ABSENT

    def get_duration(self, mode_arrondi=SANS_ARRONDI):
        duration = 0
        for timeslot in self.timeslots:
            if timeslot.debut is not None and timeslot.value in (0, PREVISIONNEL):
                duration += 5 * GetDureeArrondie(mode_arrondi, timeslot.debut, timeslot.fin)
        return duration


class DayCollection(dict):
    def __init__(self, key):
        self.keyfunc = operator.attrgetter(key)

    @collection.appender
    @collection.internally_instrumented
    def add(self, timeslot, _sa_initiator=None):
        key = self.keyfunc(timeslot)
        if not self.get(key):
            dict.__setitem__(self, key, Day())
        dict.__getitem__(self, key).timeslots.append(timeslot)

    @collection.remover
    @collection.internally_instrumented
    def remove(self, timeslot, _sa_initiator=None):
        key = self.keyfunc(timeslot)
        timeslots = self.__getitem__(key).timeslots
        timeslots.remove(timeslot)
        if not timeslots:
            dict.__delitem__(self, key)


class PeriodeReference(object):
    def __init__(self, parent):
        self.parent = parent

    def get_days_per_week(self):
        days = len(self.days)
        if self.duree_reference > 7:
            days /= (self.duree_reference // 7)
        return days

    def get_duration_per_week(self):
        duration = 0
        for day in self.days.values():
            duration += day.get_duration(self.parent.get_mode_arrondi())
        if self.duree_reference > 7:
            duration /= (self.duree_reference // 7)
        return duration / 60

    def get_day_from_index(self, index):
        return self.days.get(index, Day())

    def get_day_from_date(self, date):
        weekday = date.weekday()
        if self.duree_reference > 7:
            weekday = ((date - self.debut).days + weekday) % self.duree_reference
        return self.days.get(weekday, Day())


class Inscription(Base, PeriodeReference):
    __tablename__ = "inscriptions"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship("Inscrit")
    preinscription = Column(Boolean)
    reservataire_id = Column(Integer, ForeignKey("reservataires.idx"))
    reservataire = relationship("Reservataire")
    groupe_id = Column(Integer, ForeignKey("groupes.idx"))
    groupe = relationship("Groupe")
    forfait_mensuel = Column(Float)
    frais_inscription = Column(Float)
    allocation_mensuelle_caf = Column(Float)
    site_id = Column(Integer, ForeignKey("sites.idx"))
    site = relationship("Site")
    sites_preinscription = Column(String)
    professeur_id = Column(Integer, ForeignKey("professeurs.idx"))
    professeur = relationship("Professeur")
    debut = Column(Date)
    fin = Column(Date)
    depart = Column(Date)
    mode = Column(Integer)
    fin_periode_adaptation = Column(Date)
    duree_reference = Column(Integer)
    forfait_mensuel_heures = Column(Float)
    semaines_conges = Column(Integer)
    heures_permanences = Column(Float)
    newsletters = Column(Integer)
    tarifs = Column(Integer)
    days = relationship("TimeslotInscription", collection_class=lambda: DayCollection("day"), backref="inscription", cascade="all, delete-orphan")

    @reconstructor
    def init_on_load(self):
        PeriodeReference.__init__(self, self.inscrit)

    def GetJourneeReferenceCopy(self, date):
        reference = self.GetJourneeReference(date)
        result = Journee(self.inscrit, date, reference)
        result.reference = reference
        return result

    def GetNombreJoursCongesPeriode(self):
        if self.semaines_conges:
            if self.mode == MODE_FORFAIT_HEBDOMADAIRE:
                return self.semaines_conges * 7
            else:
                return self.semaines_conges * self.get_days_per_week()
        else:
            return 0

    def GetNombreJoursCongesPris(self, debut, fin):
        jours = 0
        date = debut
        # print "GetNombreJoursCongesPris(%s - %s)" % (debut, fin)
        while date <= fin:
            if self.mode in (MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_MENSUEL):
                if date in self.parent.creche.periodes_fermeture or date in self.inscrit.jours_conges:
                    # print date
                    jours += 1
            else:
                state = self.inscrit.get_state(date)
                if self.parent.creche.facturation_jours_feries == ABSENCES_DEDUITES_EN_JOURS:
                    if state == VACANCES:
                        # print "VACANCES", date
                        jours += 1
                else:
                    if state in (ABSENT, VACANCES):
                        reference = self.get_day_from_date(date)
                        if reference.get_duration() > 0:
                            # print date
                            jours += 1
            date += datetime.timedelta(1)
        return jours

    def GetDebutDecompteJoursConges(self):
        if self.fin_periode_adaptation:
            return self.fin_periode_adaptation + datetime.timedelta(1)
        else:
            return self.debut

    def GetFin(self):
        return self.depart if (self.parent.creche.gestion_depart_anticipe and self.depart) else (self.fin if self.fin else datetime.date.max)

    def GetFinDecompteJoursConges(self):
        if self.parent.creche.gestion_depart_anticipe and self.depart:
            return self.depart
        else:
            return self.fin

    def GetNombreJoursCongesPoses(self):
        if self.debut and self.fin:
            return self.GetNombreJoursCongesPris(self.GetDebutDecompteJoursConges(), self.GetFinDecompteJoursConges())
        else:
            return 0

    def IsNombreSemainesCongesDepasse(self, jalon):
        if self.parent.creche.facturation_jours_feries == ABSENCES_DEDUITES_SANS_LIMITE:
            return False
        if self.debut:
            if not self.semaines_conges:
                return True
            debut = self.GetDebutDecompteJoursConges()
            pris = self.GetNombreJoursCongesPris(debut, jalon)
            total = self.GetNombreJoursCongesPeriode()
            return pris > total
        else:
            return False

    def GetDatesFromReference(self, index):
        if self.debut is not None:
            fin = self.fin if self.fin else datetime.date(self.debut.year + 1, self.debut.month, self.debut.day)
            date = self.debut + datetime.timedelta(index + 7 - self.debut.weekday())
            while date < fin:
                yield date
                date += datetime.timedelta(self.duree_reference)

    def IsInPeriodeAdaptation(self, date):
        if self.debut is None or self.fin_periode_adaptation is None:
            return False
        return self.debut <= date <= self.fin_periode_adaptation

    def GetListeActivites(self, activite=0):
        result = []
        for i, jourReference in enumerate(self.reference):
            s = jourReference.GetHeureArriveeDepart(activite)
            if s:
                if len(self.reference) <= 7:
                    s = days[i] + " " + s
                else:
                    s = days[i % 7] + " semaine %d" % (1 + (i / 7)) + s
                result.append(s)
        return ', '.join(result)


class Capacite(Base):
    __tablename__ = "capacite"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    value = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)
    jour = Column(Integer)


class TimeslotInscription(Base, Timeslot):
    __tablename__ = "ref_activities"
    idx = Column(Integer, primary_key=True)
    reference = Column(Integer, ForeignKey("inscriptions.idx"))
    day = Column(Integer)
    value = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)


class TimeslotContratSalarie(Base, Timeslot):
    __tablename__ = "ref_journees_salaries"
    idx = Column(Integer, primary_key=True)
    reference = Column(Integer, ForeignKey("contrats.idx"))
    day = Column(Integer)
    value = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)


class Revenu(Base):
    __tablename__ = "revenus"
    idx = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.idx"))
    debut = Column(Date)
    fin = Column(Date)
    revenu = Column(Integer)
    chomage = Column(Boolean)
    conge_parental = Column(Boolean)
    regime = Column(Integer)


class CommentaireInscrit(Base):
    __tablename__ = "commentaires"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    date = Column(Date)
    commentaire = Column(String)


class TimeslotInscrit(Base, Timeslot):
    __tablename__ = "activites"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    date = Column(Date)
    value = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)


class WeekSlotInscrit(Base):
    __tablename__ = "planning_hebdomadaire"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    date = Column(Date)
    activity = Column(Integer)
    value = Column(Float)


class DaySlotSalarie(Base, Timeslot):
    __tablename__ = "activites_salaries"
    idx = Column(Integer, primary_key=True)
    salarie = Column(Integer, ForeignKey("employes.idx"))
    date = Column(Date)
    value = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)

    @reconstructor
    def init_on_load(self):
        Timeslot.__init__(self)


class CommentaireSalarie(Base):
    __tablename__ = "commentaires_salaries"
    idx = Column(Integer, primary_key=True)
    salarie = Column(Integer, ForeignKey("employes.idx"))
    date = Column(Date)
    commentaire = Column(String)


class User(Base):
    __tablename__ = "users"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    login = Column(String)
    password = Column(String)
    profile = Column(Integer)


class CongeStructure(Base):
    __tablename__ = "conges"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(String)
    fin = Column(String)
    label = Column(String)
    options = Column(Integer)

    def is_jour_ferie(self):
        if "/" in self.debut:
            return False
        else:
            return self.debut in [tmp[0] for tmp in jours_fermeture]


class CongeInscrit(Base):
    __tablename__ = "conges_inscrits"
    idx = Column(Integer, primary_key=True)
    inscrit = Column(Integer, ForeignKey("inscrits.idx"))
    debut = Column(String)
    fin = Column(String)
    label = Column(String)


class CongeSalarie(Base):
    __tablename__ = "conges_salaries"
    idx = Column(Integer, primary_key=True)
    salarie = Column(Integer, ForeignKey("employes.idx"))
    debut = Column(String)
    fin = Column(String)
    label = Column(String)


class Alerte(Base):
    __tablename__ = "alertes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    texte = Column(String)
    date = Column(Date)
    acquittement = Column(Boolean)


class Charge(Base):
    __tablename__ = "charges"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    date = Column(Date)
    charges = Column(Float)


class Facture(Base):
    __tablename__ = "factures"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    date = Column(Date)
    cotisation_mensuelle = Column(Float)
    total_contractualise = Column(Float)
    total_realise = Column(Float)
    total_facture = Column(Float)
    supplement_activites = Column(Float)
    supplement = Column(Float)
    deduction = Column(Float)


class EncaissementFamille(Base):
    __tablename__ = "encaissements"
    idx = Column(Integer, primary_key=True)
    famille = Column(Integer, ForeignKey("familles.idx"))
    date = Column(Date)
    valeur = Column(Float)
    moyen_paiement = Column(Integer)


class EncaissementReservataire(Base):
    __tablename__ = "encaissements_reservataires"
    idx = Column(Integer, primary_key=True)
    reservataire_idx = Column(Integer, ForeignKey("reservataires.idx"))
    date = Column(Date)
    valeur = Column(Float)
    moyen_paiement = Column(Integer)


class NumeroFacture(Base):
    __tablename__ = "numeros_facture"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    date = Column(Date)
    valeur = Column(Integer)


class Correction(Base):
    __tablename__ = "corrections"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    date = Column(Date)
    valeur = Column(Float)
    libelle = Column(String)


class Groupe(Base):
    __tablename__ = "groupes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    nom = Column(String)
    ordre = Column(Integer)
    age_maximum = Column(Integer)


class Categorie(Base):
    __tablename__ = "categories"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    nom = Column(String)


class TarifSpecial(Base):
    __tablename__ = "tarifsspeciaux"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    label = Column(String)
    type = Column(Integer)
    unite = Column(Integer)
    valeur = Column(Float)
    portee = Column(Integer)


class PlageHoraire(Base):
    __tablename__ = "plageshoraires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    debut = Column(Float)
    fin = Column(Float)
    flags = Column(Integer)


class Database(object):
    def __init__(self):
        self.uri = None
        self.engine = None
        self.session = None
        self.query = None
        self.add = None
        self.delete = None
        self.commit = None
        self.flush = None
        self.creche = None

    def init(self, filename=None):
        if filename:
            self.uri = "sqlite:///%s" % filename
        self.engine = create_engine(self.uri, echo=True)
        self.session = sessionmaker(bind=self.engine)()
        self.query = self.session.query
        self.add = self.session.add
        self.delete = self.session.delete
        self.commit = self.session.commit
        self.flush = self.session.flush

    def load(self):
        self.translate()
        self.reload()

    def reload(self):
        print("Chargement de la base de données...")
        self.creche = self.query(Creche).first()

    def exists(self):
        return database_exists(self.uri) and self.engine.dialect.has_table(self.engine.connect(), DBSettings.__tablename__)

    def get_inscrit(self, inscrit_id):
        inscrit_id = int(inscrit_id)
        for inscrit in self.inscrits:
            if inscrit.id == inscrit_id:
                return inscrit
        else:
            return None

    def create(self):
        print("Database creation...")
        self.commit()

    def translate(self):
        version_entry = self.query(DBSettings).filter_by(key=KEY_VERSION).one()
        version = int(version_entry.value)
        version = 114
        if version != DB_VERSION:
            print("Database translation from version %s to version %d..." % (version, DB_VERSION))
            print("TODO other translations")
            if version < 113:
                self.engine.execute("ALTER TABLE CRECHE ADD regularisation_conges_non_pris BOOLEAN;")
                self.engine.execute("UPDATE CRECHE SET regularisation_conges_non_pris=regularisation_fin_contrat;")
            if version < 114:
                self.engine.execute("ALTER TABLE INSCRITS ADD garde_alternee BOOLEAN;")
                self.engine.execute("UPDATE INSCRITS SET garde_alternee=?", (False,))
            if version < 115:
                idx = self.engine.execute('SELECT idx FROM CRECHE').first()[0]
                for table in ("plageshoraires", "activities", "familles", "users", "inscrits", "employes", "categories", "groupes", "sites", "reservataires", "tarifsspeciaux", "tarifs_horaires", "conges", "baremescaf"):
                    try:
                        self.engine.execute("ALTER TABLE %s ADD creche_id INGEGER REFERENCES creche(idx)" % table)
                        self.engine.execute("UPDATE %s SET creche_id=?" % table, (idx,))
                    except:
                        pass

                try:
                    self.engine.execute("ALTER TABLE revenus ADD parent_id INGEGER REFERENCES PARENT(idx);")
                    self.engine.execute("UPDATE revenus SET parent_id=parent")
                except:
                    pass

                for column in ("inscrit", "reservataire", "groupe", "site", "professeur"):
                    try:
                        self.engine.execute("ALTER TABLE inscriptions ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                        self.engine.execute("UPDATE inscriptions SET %s_id=%s" % (column, column))
                    except:
                        pass

                for column in ("famille", "categorie"):
                    try:
                        self.engine.execute("ALTER TABLE inscrits ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                        self.engine.execute("UPDATE inscrits SET %s_id=%s" % (column, column))
                    except:
                        pass

                for column in ("famille", ):
                    try:
                        self.engine.execute("ALTER TABLE fratries ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                        self.engine.execute("UPDATE fratries SET %s_id=%s" % (column, column))
                        self.engine.execute("ALTER TABLE referents ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                        self.engine.execute("UPDATE referents SET %s_id=%s" % (column, column))
                    except:
                        pass

                for table in ("activites", "planning_hebdomadaire", "commentaires", "factures", "corrections"):
                    try:
                        self.engine.execute("ALTER TABLE %s ADD inscrit_id INGEGER REFERENCES inscrits(idx)" % table)
                        self.engine.execute("UPDATE %s SET inscrit_id=inscrit" % table)
                    except:
                        pass

            version_entry.value = DB_VERSION
            self.commit()

    def populate(self):
        print("Database population...")
        Base.metadata.create_all(self.engine)
        self.add(DBSettings(key=KEY_VERSION, value=DB_VERSION))
        for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
            self.add(CongeStructure(debut=label))
        self.add(Creche())
        for debut, fin, plancher, plafond in [
            (datetime.date(2006, 9, 1), datetime.date(2007, 8, 31), 6547.92, 51723.60),
            (datetime.date(2007, 9, 1), datetime.date(2008, 12, 31), 6660.00, 52608.00),
            (datetime.date(2009, 1, 1), datetime.date(2009, 12, 31), 6876.00, 53400.00),
            (datetime.date(2010, 1, 1), datetime.date(2010, 12, 31), 6956.64, 54895.20),
            (datetime.date(2011, 1, 1), datetime.date(2011, 12, 31), 7060.92, 85740.00),
            (datetime.date(2012, 1, 1), datetime.date(2012, 12, 31), 7181.04, 85740.00),
            (datetime.date(2013, 1, 1), datetime.date(2013, 12, 31), 7306.56, 85740.00),
        ]:
            self.add(BaremeCAF(debut=debut, fin=fin, plancher=plancher, plafond=plafond))
        self.add(Activite(label="Présences", value=0, mode=0, couleur="[5, 203, 28, 150, 100]",
                          couleur_supplement="[5, 203, 28, 250, 100]", couleur_previsionnel="[5, 203, 28, 50, 100]",
                          formule_tarif=""))
        self.add(Activite(label="Vacances", value=VACANCES, mode=0, couleur="[0, 0, 255, 150, 100]",
                          couleur_supplement="[0, 0, 255, 150, 100]", couleur_previsionnel="[0, 0, 255, 150, 100]",
                          formule_tarif=""))
        self.add(Activite(label="Malade", value=MALADE, mode=0, couleur="[190, 35, 29, 150, 100]",
                          couleur_supplement="[190, 35, 29, 150, 100]", couleur_previsionnel="[190, 35, 29, 150, 100]",
                          formule_tarif=""))
        self.commit()

    def delete_all_inscriptions(self):
        self.delete(self.query(Famille()))
        self.delete(self.query(Salarie()))
        self.delete(self.query(Professeur()))
        self.delete(self.query(Alerte()))
        self.delete(self.query(NumeroFacture()))
        self.commit()

    def dump(self):
        print("Inscrits :")
        for inscrit in self.creche.inscrits:
            print(" ", inscrit.prenom, inscrit.nom)
        print("Salariés :")
        for salarie in self.creche.salaries:
            print(" ", salarie.prenom, salarie.nom)


if __name__ == "__main__":
    database = Database()
    database.init("databases/gertrude.db")
    if database.exists():
        database.load()
        database.dump()
    else:
        print("Base non existante, création")
        database.populate()
        database.dump()
