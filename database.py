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
import math
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import *
from sqlalchemy_utils import database_exists
from sqlalchemy.orm.collections import collection, attribute_mapped_collection
from version import VERSION
from helpers import *
from parameters import *
import bcrypt
from config import config

DB_VERSION = 130

Base = declarative_base()

KEY_VERSION = "VERSION"
KEY_RELEASE = "RELEASE"


class DBSettings(Base):
    __tablename__ = "data"
    key = Column(String, primary_key=True)
    value = Column(String)


class Timeslot(object):
    def __init__(self, debut, fin, activity, **kwargs):
        self.debut = debut
        self.fin = fin
        self.activity = activity
        self.value = None  # needed for TrancheCapacite compatibility
        if isinstance(activity, int):
            raise Exception("Not allowed integer activity")
        for key, value in kwargs.items():
            setattr(self, key, value)

    def is_checkbox(self):
        return self.activity.mode == MODE_SANS_HORAIRES

    def is_presence(self):
        return self.activity.mode == MODE_PRESENCE

    def get_duration(self, arrondi=SANS_ARRONDI):
        # TODO a utiliser partout
        return 0 if self.debut is None else 5 * GetDureeArrondie(arrondi, self.debut, self.fin)

    def __repr__(self):
        return "Timeslot %r %r-%r" % (self.activity.label if self.activity else None, self.debut, self.fin)


class Day(object):
    def __init__(self):
        self.timeslots = []

    def get_state(self):
        default = ABSENT
        for timeslot in self.timeslots:
            mode = timeslot.activity.mode
            if mode < 0:
                default = mode
            elif mode == MODE_SALARIE_RECUP_HEURES_SUPP:
                default = CONGES_RECUP_HEURES_SUPP
            elif mode == MODE_ABSENCE_NON_PREVENUE:
                default = ABSENCE_NON_PREVENUE
            elif mode not in (MODE_PLACE_SOUHAITEE, MODE_SANS_HORAIRES, MODE_SYSTEMATIQUE_SANS_HORAIRES):
                return PRESENT
        return default

    def get_activity_timeslots(self):
        return [timeslot for timeslot in self.timeslots if timeslot.debut is not None]

    def get_timeslots_per_activity_mode(self, activity_mode):
        return [timeslot for timeslot in self.timeslots if timeslot.activity.mode == activity_mode]

    def get_duration_per_activity_mode(self, activity_mode, mode_arrondi=SANS_ARRONDI):
        return sum([timeslot.get_duration(mode_arrondi) for timeslot in self.get_timeslots_per_activity_mode(activity_mode)]) / 60

    def get_duration_permanences(self):
        return self.get_duration_per_activity_mode(MODE_PERMANENCE)

    def get_duration(self, mode_arrondi=SANS_ARRONDI):
        return self.get_duration_per_activity_mode(0, mode_arrondi)

    def GetPlageHoraire(self):
        debut, fin = None, None
        for timeslot in self.timeslots:
            if timeslot.debut and timeslot.fin and timeslot.activity.mode == MODE_PRESENCE:
                if not debut or timeslot.debut < debut:
                    debut = timeslot.debut / 12
                if not fin or timeslot.fin > fin:
                    fin = timeslot.fin / 12
        return debut, fin

    def GetHeureArrivee(self):
        arrivee, depart = self.GetPlageHoraire()
        return "" if arrivee is None else GetHeureString(arrivee)

    def GetHeureDepart(self):
        arrivee, depart = self.GetPlageHoraire()
        return "" if depart is None else GetHeureString(depart)

    def GetHeureArriveeDepart(self):
        arrivee, depart = self.GetPlageHoraire()
        return "" if (arrivee is None and depart is None) else ("de %s à %s" % (GetHeureString(arrivee), GetHeureString(depart)))

    def GetActivity(self, heure):
        if not isinstance(heure, int):
            heure = int(round(heure * 12))
        for timeslot in self.timeslots:
            if timeslot.debut <= heure < timeslot.fin:
                return timeslot
        else:
            return None

    def __str__(self):
        return "Day timeslots=%r" % self.timeslots


class DayCollection(dict):
    def __init__(self, key):
        self.keyfunc = operator.attrgetter(key)

    @collection.iterator
    def __iter__(self):
        for day in self.values():
            for timeslot in day.timeslots:
                yield timeslot

    @collection.appender
    def add(self, timeslot):
        key = self.keyfunc(timeslot)
        if not self.get(key):
            dict.__setitem__(self, key, Day())
        self[key].timeslots.append(timeslot)

    @collection.remover
    def remove(self, timeslot):
        key = self.keyfunc(timeslot)
        timeslots = self[key].timeslots
        timeslots.remove(timeslot)
        if not timeslots:
            dict.__delitem__(self, key)


class PeriodeReference(object):
    def get_days_per_week(self):
        days = len(self.days)
        if self.duree_reference > 7:
            days //= (self.duree_reference // 7)
        return days

    def get_duration_per_week(self, mode_arrondi=SANS_ARRONDI):
        duration = 0
        for day in self.days.values():
            duration += day.get_duration(mode_arrondi)
        if self.duree_reference > 7:
            duration /= (self.duree_reference // 7)
        return duration

    def get_day_from_index(self, index):
        return self.days.get(index, Day())

    def get_day_from_date(self, date):
        if self.duree_reference > 7:
            weekday = ((date - self.debut).days + self.debut.weekday()) % self.duree_reference
        else:
            weekday = date.weekday()
        return self.days.get(weekday, Day())

    def GetFin(self):
        return self.fin if self.fin else datetime.date.max


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
    presences_supplementaires = Column(Boolean, default=True)
    modes_inscription = Column(Integer, default=TOUS_MODES_ACCUEIL)
    minimum_maladie = Column(Integer, default=3)
    email = Column(String)
    email_changements_planning = Column(String)
    type = Column(Integer, default=TYPE_PARENTAL)
    mode_saisie_planning = Column(Integer, default=SAISIE_HORAIRE)
    periode_revenus = Column(Integer, default=REVENUS_YM2)
    mode_facturation = Column(Integer, default=FACTURATION_PSU)
    temps_facturation = Column(Integer, default=FACTURATION_FIN_MOIS)
    repartition = Column(Integer, default=REPARTITION_MENSUALISATION_12MOIS)
    prorata = Column(Integer, default=PRORATA_JOURS_OUVRES)
    conges_inscription = Column(Integer, default=0)
    tarification_activites = Column(Integer, default=0)
    traitement_maladie = Column(Integer, default=DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES)
    facturation_jours_feries = Column(Integer, default=ABSENCES_DEDUITES_EN_SEMAINES)
    facturation_periode_adaptation = Column(Integer, default=PERIODE_ADAPTATION_FACTUREE_NORMALEMENT)
    _formule_taux_effort = Column(String, name="formule_taux_effort", default="None")
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
    gestion_conges_sans_solde = Column(Boolean, default=False)
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
    societe = Column(String)
    siret = Column(String)
    gestion_plannings_salaries = Column(Integer, default=0)
    delai_paiement_familles = Column(Integer)
    users = relationship("User", cascade="all, delete-orphan")
    sites = relationship("Site", cascade="all, delete-orphan")
    bureaux = relationship("Bureau", cascade="all, delete-orphan")
    professeurs = relationship("Professeur", cascade="all, delete-orphan")
    categories = relationship("Categorie", cascade="all, delete-orphan")
    groupes = relationship("Groupe", cascade="all, delete-orphan")
    reservataires = relationship("Reservataire", cascade="all, delete-orphan")
    tarifs_horaires = relationship("TarifHoraire", cascade="all, delete-orphan")
    tarifs_speciaux = relationship("TarifSpecial", cascade="all, delete-orphan")
    familles = relationship("Famille", cascade="all, delete-orphan")
    inscrits = relationship("Inscrit", cascade="all, delete-orphan")
    salaries = relationship("Salarie", cascade="all, delete-orphan")
    _activites = relationship("Activite", cascade="all, delete-orphan")
    plages_horaires = relationship("PlageHoraire", cascade="all, delete-orphan")
    _conges = relationship("CongeStructure", cascade="all, delete-orphan")
    baremes_caf = relationship("BaremeCAF", cascade="all, delete-orphan")
    numeros_facture = relationship("NumeroFacture", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")
    tranches_capacite = relationship("TrancheCapacite", collection_class=lambda: DayCollection("jour"), cascade="all, delete-orphan")
    charges = relationship("Charge", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")
    alertes = relationship("Alerte", collection_class=attribute_mapped_collection("texte"), cascade="all, delete-orphan")
    food_needs = relationship("FoodNeed", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.update()

    def update(self):
        self.periodes_fermeture = {}
        self.jours_fermeture = {}
        self.jours_fete = set()
        self.jours_weekend = []
        self.mois_sans_facture = {}
        self.mois_facture_uniquement_heures_supp = {}
        self.liste_conges = []
        self.conges = []
        self.feries = {}
        self.states = {}
        self.activites = []
        self.formule_taux_effort = None

    @reconstructor
    def init_on_load(self):
        self.update()
        # TODO split conges / feries
        self.formule_taux_effort = eval(self._formule_taux_effort)
        self.UpdateFormuleTauxEffort(changed=False)
        for activity in self._activites:
            if activity.mode <= 0:
                self.states[activity.mode] = activity
            else:
                self.activites.append(activity)
        for conge in self._conges:
            if conge.debut in [tmp[0] for tmp in jours_fermeture]:
                self.feries[conge.debut] = conge
            else:
                self.conges.append(conge)
        self.calcule_jours_conges()

    def get_activite_by_id(self, id):
        for activite in self._activites:
            if activite.idx == id:
                return activite
        else:
            return None

    def select_inscriptions(self, start, end):
        for inscrit in self.inscrits:
            for inscription in inscrit.get_inscriptions(start, end):
                yield inscription

    def select_inscrits(self, start, end, site=None, handicap=None, reservataire=None):
        for inscrit in self.inscrits:
            if inscrit.is_present(start, end, site, handicap, reservataire):
                yield inscrit

    def get_next_activity_value(self):
        values = self.activites.keys()
        return max(values) + 1

    def add_activite(self, activity):
        self._activites.append(activity)
        if activity.mode < 0:
            self.states[activity.mode] = activity
        else:
            self.activites.append(activity)

    def delete_activite(self, activity):
        self._activites.remove(activity)
        self.activites.remove(activity)

    def add_ferie(self, conge):
        self._conges.append(conge)
        self.feries[conge.debut] = conge
        self.calcule_jours_conges()

    def delete_ferie(self, conge):
        self._conges.remove(conge)
        del self.feries[conge.debut]
        self.calcule_jours_conges()

    def add_conge(self, conge):
        self._conges.append(conge)
        self.conges.append(conge)
        self.calcule_jours_conges()

    def delete_conge(self, conge):
        self._conges.remove(conge)
        self.conges.remove(conge)
        self.calcule_jours_conges()

    def calcule_jours_conges(self):
        self.periodes_fermeture = {}
        self.jours_fermeture = {}
        self.jours_fete = set()
        self.jours_weekend = []
        self.mois_sans_facture = {}
        self.mois_facture_uniquement_heures_supp = {}
        for year in range(config.first_date.year, config.last_date.year + 1):
            self.mois_sans_facture[year] = set()
            self.mois_facture_uniquement_heures_supp[year] = set()
            for label, func, enable in jours_fermeture:
                if label in self.feries:
                    tmp = func(year)
                    if isinstance(tmp, list):
                        for j in tmp:
                            self.jours_fermeture[j] = self.feries[label]
                            if label == "Week-end":
                                self.jours_weekend.append(j)
                    else:
                        self.jours_fermeture[tmp] = self.feries[label]

        self.jours_feries = self.jours_fermeture.keys()
        self.jours_fete = set(self.jours_feries) - set(self.jours_weekend)
        self.jours_conges = set()
        self.liste_conges = []

        def AddPeriode(debut, fin, conge):
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
                    except:
                        pass
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
                    except:
                        pass
            else:
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
                except:
                    pass

        self.jours_fete = list(self.jours_fete)
        self.jours_feries = list(self.jours_feries)
        self.jours_conges = list(self.jours_conges)

    def GetDateRevenus(self, date):
        if self.periode_revenus == REVENUS_CAFPRO:
            return date
        elif date >= datetime.date(2008, 9, 1):
            return IncrDate(date, years=-2)
        elif date < datetime.date(date.year, 9, 1):
            return datetime.date(date.year - 2, 1, 1)
        else:
            return datetime.date(date.year - 1, 1, 1)

    def GetHeuresAccueil(self, jour):
        result = 0
        for timeslot in self.tranches_capacite.get(jour, Day()).timeslots:
            result += timeslot.value * (timeslot.fin - timeslot.debut)
        return result / 12

    def get_factures_list(self):
        result = []
        date = config.get_first_monday()
        while date <= datetime.date.today():
            result.append(date)
            date = GetNextMonthStart(date)
        return result

    def get_capacite_max(self):
        capacite = 0
        for jour in range(7):
            if self.is_jour_semaine_travaille(jour):
                for timeslot in self.tranches_capacite.get(jour, Day()).timeslots:
                    capacite = max(timeslot.value, capacite)
        return capacite

    def get_capacite(self, jour=None, tranche=None):
        if jour is None:
            jours, result = 0, 0.0
            for jour in range(7):
                if self.is_jour_semaine_travaille(jour):
                    jours += 1
                    result += self.get_capacite(jour)
            return result / jours
        elif tranche is None:
            return self.GetHeuresAccueil(jour) / self.get_amplitude_horaire()
        else:
            for start, end, value in self.tranches_capacite[jour].activites:
                if start <= tranche < end:
                    return value
            else:
                return 0

    def is_jour_semaine_travaille(self, day):
        day %= 7
        if days[day] in self.feries:
            return False
        elif day == 5 or day == 6:
            return "Week-end" not in self.feries
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
            result = [(int(debut * (60 // BASE_GRANULARITY)), int(fin * (60 // BASE_GRANULARITY))) for debut, fin in
                      result]
        return result

    def GetPlagesArray(self, plage_type, conversion=True):
        result = []
        for plage in self.plages_horaires:
            if plage.flags == plage_type and plage.debut and plage.fin > plage.debut:
                result.append((plage.debut, plage.fin))
        if conversion:
            result = [(int(debut * (60 // BASE_GRANULARITY)), int(fin * (60 // BASE_GRANULARITY))) for debut, fin in
                      result]
        return result

    def get_activites_avec_horaires(self):
        return [activite for activite in self.activites if activite.has_horaires()]

    def get_activites_sans_horaires(self):
        return [activite for activite in self.activites if activite.mode == MODE_SANS_HORAIRES]

    def has_activites_avec_horaires(self):
        for activite in self.activites:
            if activite.has_horaires():
                return True
        return False

    def eval_formule_tarif(self, formule, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs, site, debut):
        # print 'eval_formule_tarif', 'mode=%d' % mode, handicap, 'revenus=%f' % revenus, 'enfants=%d' % enfants, 'jours=%d' % jours, 'heures=%f' % heures, reservataire, nom, 'parents=%d' % parents, chomage, conge_parental, 'heures_mois=%f' % heures_mois, heure_mois
        hg = MODE_HALTE_GARDERIE
        creche = MODE_CRECHE
        forfait = MODE_FORFAIT_MENSUEL
        urgence = MODE_ACCUEIL_URGENCE
        site = site.lower()
        debut = str(debut) if isinstance(debut, datetime.date) else ""
        for tarif in self.tarifs_speciaux:
            try:
                exec("%s = %r" % (tarif.label.lower().replace(" ", "_"), tarifs & (1 << tarif.idx)))
            except:
                pass
        try:
            for cas in formule:
                if heure_mois is None and "heure_mois" in cas[0]:
                    return None, None
                elif eval(cas[0]):
                    # print cas[0], cas[1]
                    return cas[1], cas[2]
            else:
                raise Exception("Aucune condition ne matche")
        except:
            raise Exception("Erreur dans la formule")

    def eval_formule_taux_effort(self, formule, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs):
        # print 'eval_formule_taux_effort', 'mode=%d' % mode, handicap, 'revenus=%f' % revenus, 'enfants=%d' % enfants, 'jours=%d' % jours, 'heures=%f' % heures, reservataire, nom, 'parents=%d' % parents, chomage, conge_parental, 'heures_mois=%f' % heures_mois, heure_mois
        hg = MODE_HALTE_GARDERIE
        creche = MODE_CRECHE
        forfait = MODE_FORFAIT_MENSUEL
        urgence = MODE_ACCUEIL_URGENCE
        for tarif in self.tarifs_speciaux:
            try:
                exec("%s = %r" % (tarif.label.lower().replace(" ", "_"), tarifs & (1 << tarif.idx)))
            except:
                pass
        try:
            for cas in formule:
                if heure_mois is None and "heure_mois" in cas[0]:
                    return None
                elif eval(cas[0]):
                    return cas[1]
            else:
                raise Exception("Aucune condition ne matche")
        except:
            raise Exception("Erreur dans la formule")

    def CheckFormule(self, formule, index):
        hg = MODE_HALTE_GARDERIE
        creche = MODE_CRECHE
        forfait = MODE_FORFAIT_MENSUEL
        urgence = MODE_ACCUEIL_URGENCE
        handicap = False
        chomage = 0
        conge_parental = 0
        mode = hg
        revenus = 20000
        jours = 5
        heures = 60
        heures_mois = 60 * 4.33
        heure_mois = heures_mois
        parents = 2
        enfants = 1
        reservataire = False
        nom = "gertrude"
        site = ""
        paje = paje1
        for tarif in self.tarifs_speciaux:
            try:
                exec("%s = False" % tarif.label.lower().replace(" ", "_"))
            except:
                pass
        try:
            test = eval(formule[index][0])
            return True
        except Exception as e:
            print(e)
            return False

    def get_formule_conversion_taux_effort(self, formule):
        if formule:
            result = []
            for cas in formule:
                condition = cas[0].strip()
                if condition == "":
                    condition = "True"
                else:
                    condition = condition.lower(). \
                        replace(" et ", " and "). \
                        replace(" ou ", " or "). \
                        replace("!=", "__<>"). \
                        replace("<=", "__<eq"). \
                        replace(">=", "__>eq"). \
                        replace("=", "=="). \
                        replace("__<>", "!="). \
                        replace("__<eq", "<="). \
                        replace("__>eq", ">=")
                result.append([condition, cas[1], cas[0]])
            return result
        else:
            return None

    def UpdateFormuleTauxEffort(self, changed=True):
        if changed:
            print('update formule_taux_effort', self.formule_taux_effort)
            self._formule_taux_effort = str(self.formule_taux_effort)
        self.conversion_formule_taux_effort = self.get_formule_conversion_taux_effort(self.formule_taux_effort)

    def EvalTauxEffort(self, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs):
        return self.eval_formule_taux_effort(self.conversion_formule_taux_effort, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs)

    def eval_tarif(self, date, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs, site, debut):
        conversion_formule = Select(self.tarifs_horaires, date).conversion_formule
        return self.eval_formule_tarif(conversion_formule, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs, site, debut)

    def GetAllergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",") if allergie.strip()]

    def GetObject(self, objects, idx):
        try:
            idx = int(idx)
            for o in objects:
                if o.idx == idx:
                    return o
        except:
            pass
        return None

    def GetSite(self, idx):
        return self.GetObject(self.sites, idx)

    def GetInscrit(self, idx):
        return self.GetObject(self.inscrits, idx)

    def GetReservataire(self, idx):
        return self.GetObject(self.reservataires, idx)

    def GetSalarie(self, idx):
        return self.GetObject(self.salaries, idx)


class Site(Base):
    __tablename__ = "sites"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    nom = Column(String)
    adresse = Column(String)
    code_postal = Column(Integer)
    ville = Column(String)
    telephone = Column(String)
    email = Column(String)
    societe = Column(String)
    siret = Column(String)
    capacite = Column(Integer)
    groupe = Column(Integer)

    def get_name(self):
        return self.nom if self.nom else "<sans nom>"

    def get_factures_list(self):
        return self.creche.get_factures_list()


class FoodNeed(Base):
    __tablename__ = "food_needs"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    label = Column(String)
    tranche_4_6 = Column(Integer)
    tranche_6_12 = Column(Integer)
    tranche_12_18 = Column(Integer)
    tranche_18_24 = Column(Integer)
    tranche_24_ = Column(Integer)


class Bureau(Base):
    __tablename__ = "bureaux"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
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

    def __init__(self, creche, **kwargs):
        Base.__init__(self, creche=creche, **kwargs)


class BaremeCAF(Base):
    __tablename__ = "baremescaf"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    debut = Column(Date)
    fin = Column(Date)
    plancher = Column(Integer)
    plafond = Column(Integer)

    def __init__(self, creche, **kwargs):
        Base.__init__(self, creche=creche, **kwargs)


class TarifHoraire(Base):
    __tablename__ = "tarifs_horaires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    debut = Column(Date)
    fin = Column(Date)
    _formule = Column(String, name="formule")

    def __init__(self, creche, formule=[], **kwargs):
        Base.__init__(self, creche=creche, **kwargs)
        self.formule = formule
        self.UpdateFormule(changed=True)

    @reconstructor
    def init_on_load(self):
        self.formule = eval(self._formule)
        self.conversion_formule = self.get_formule_conversion(self.formule)

    def UpdateFormule(self, changed=True):
        if changed:
            # print('update formule_taux_horaire', self.formule)
            self._formule = str(self.formule)
        self.conversion_formule = self.get_formule_conversion(self.formule)

    def get_formule_conversion(self, formule):
        if formule:
            result = []
            for cas in formule:
                condition = cas[0].strip()
                if condition == "":
                    condition = "True"
                else:
                    condition = condition.lower(). \
                        replace(" et ", " and "). \
                        replace(" ou ", " or "). \
                        replace("!=", "__<>"). \
                        replace("<=", "__<eq"). \
                        replace(">=", "__>eq"). \
                        replace("=", "=="). \
                        replace("__<>", "!="). \
                        replace("__<eq", "<="). \
                        replace("__>eq", ">=")
                result.append([condition, cas[1], cas[2], cas[0]])
            return result
        else:
            return None

    def CheckFormule(self, index):
        return self.creche.CheckFormule(self.conversion_formule, index)


class Reservataire(Base):
    __tablename__ = "reservataires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    debut = Column(Date)
    fin = Column(Date)
    nom = Column(String, default="")
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
    encaissements = relationship("EncaissementReservataire", cascade="all, delete-orphan")

    def __init__(self, creche, nom="", **kwargs):
        Base.__init__(self, creche=creche, nom=nom)

    @reconstructor
    def init_on_load(self):
        if self.nom is None:
            self.nom = ""

    def slug(self):
        return "reservataire-%d" % self.idx

    def get_delai_paiement(self):
        return self.delai_paiement

    def has_facture(self, date, site=None):
        return date in self.get_factures_list()

    def get_factures_list(self):
        result = []
        if self.debut:
            date = datetime.date(self.debut.year, 9, 1) if self.debut.month >= 9 else datetime.date(self.debut.year - 1, 9, 1)
            while date <= datetime.date.today() and (not self.fin or date < self.fin):
                next_date = date
                for i in range(self.periode_facturation):
                    next_date = GetNextMonthStart(next_date)
                if self.debut < next_date:
                    result.append(date)
                date = next_date
        return result


class Activite(Base):
    __tablename__ = "activities"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    label = Column(String)
    # value = Column(Integer)
    mode = Column(Integer)
    _couleur = Column(String, name="couleur")
    _couleur_supplement = Column(String, name="couleur_supplement", default="")
    formule_tarif = Column(String)
    owner = Column(Integer)
    flags = Column(Integer)
    timeslots_plannings_enfants = relationship("TimeslotInscription", cascade="all, delete-orphan")
    timeslots_enfants = relationship("TimeslotInscrit", cascade="all, delete-orphan")
    timeslots_plannings_salaries = relationship("TimeslotPlanningSalarie", cascade="all, delete-orphan")
    timeslots_salaries = relationship("TimeslotSalarie", cascade="all, delete-orphan")

    def __init__(self, creche, **kwargs):
        Base.__init__(self, creche=creche, **kwargs)
        self.couleur = self.get_color(self._couleur)
        self.couleur_supplement = self.get_color(self._couleur_supplement)

    @reconstructor
    def init_on_load(self):
        self.couleur = self.get_color(self._couleur)
        self.couleur_supplement = self.get_color(self._couleur_supplement)

    @staticmethod
    def get_color(color, default=[0, 0, 0, 255, 100]):
        if color:
            try:
                return eval(color)
            except Exception as e:
                print("Exception couleur '%s'" % color, e)
                return default
        else:
            return default

    def set_color(self, key, value):
        if key in ("couleur", "couleur_supplement"):
            setattr(self, key, value)
            setattr(self, "_%s" % key, str(value))

    def has_summary(self):
        return self.mode not in (MODE_CONGES, MODE_PLACE_SOUHAITEE, MODE_SYSTEMATIQUE_SANS_HORAIRES, MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE, MODE_ABSENCE_NON_PREVENUE, MODE_SALARIE_HEURES_SUPP, MODE_SALARIE_RECUP_HEURES_SUPP)

    def has_horaires(self):
        return self.mode in (MODE_PRESENCE, MODE_NORMAL, MODE_LIBERE_PLACE, MODE_PLACE_SOUHAITEE, MODE_PRESENCE_NON_FACTUREE, MODE_ABSENCE_NON_PREVENUE, MODE_PRESENCE_SUPPLEMENTAIRE, MODE_PERMANENCE, MODE_CONGES)

    def EvalTarif(self, inscrit, date, montant_heure_garde=0.0, reservataire=False):
        if self.formule_tarif and self.formule_tarif.strip():
            enfants, enfants_inscrits = inscrit.famille.GetEnfantsCount(date)[0:2]
            for tarif in self.creche.tarifs_speciaux:
                try:
                    exec("%s = %r" % (tarif.label.lower().replace(" ", "_"), inscrit.famille.tarifs & (1 << tarif.idx)))
                except Exception as e:
                    print("Exception tarif special", e)
            try:
                return eval(self.formule_tarif)
            except Exception as e:
                print("Exception tarif activite", e)
                return 0.0
        else:
            return 0.0


class ContratSalarie(Base):
    __tablename__ = "contrats_salaries"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship("Salarie")
    site_id = Column(Integer, ForeignKey("sites.idx"))
    site = relationship("Site")
    debut = Column(Date)
    fin = Column(Date)
    fonction = Column(String)
    plannings = relationship("PlanningSalarie", cascade="all, delete-orphan")

    def __init__(self, salarie, site=None, debut=None, fin=None, fonction=None):
        Base.__init__(self, salarie=salarie, site=site, debut=debut, fin=fin, fonction=fonction)
        self.plannings.append(PlanningSalarie(self))

    def __getattribute__(self, item):
        if item == "duree_reference":
            if not self.plannings:
                self.plannings.append(PlanningSalarie(self))
            return self.plannings[0].duree_reference
        elif item == "days":
            if not self.plannings:
                self.plannings.append(PlanningSalarie(self))
            return self.plannings[0].days
        else:
            return Base.__getattribute__(self, item)

    def __setattr__(self, key, value):
        if key == "duree_reference":
            if not self.plannings:
                self.plannings.append(PlanningSalarie(self))
            self.plannings[0].duree_reference = value
        else:
            Base.__setattr__(self, key, value)

    def GetFin(self):
        return self.fin if self.fin else datetime.date.max


class PlanningSalarie(Base, PeriodeReference):
    __tablename__ = "contrats"
    idx = Column(Integer, primary_key=True)
    contrat_id = Column(Integer, ForeignKey("contrats_salaries.idx"))
    contrat = relationship("ContratSalarie")
    debut = Column(Date)
    fin = Column(Date)
    duree_reference = Column(Integer)
    days = relationship("TimeslotPlanningSalarie", collection_class=lambda: DayCollection("day"), cascade="all, delete-orphan")

    def __init__(self, contrat, debut=None, fin=None, duree_reference=7):
        Base.__init__(self, contrat=contrat, debut=debut, fin=fin, duree_reference=duree_reference)


class Salarie(Base):
    __tablename__ = "employes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    prenom = Column(String)
    nom = Column(String)
    telephone_domicile = Column(String)
    telephone_domicile_notes = Column(String)
    telephone_portable = Column(String)
    telephone_portable_notes = Column(String)
    email = Column(String)
    notes = Column(String)
    diplomes = Column(String)
    combinaison = Column(String)
    contrats = relationship("ContratSalarie", cascade="all, delete-orphan")
    conges = relationship("CongeSalarie", cascade="all, delete-orphan")
    days = relationship("TimeslotSalarie", collection_class=lambda: DayCollection("date"), cascade="all, delete-orphan")
    commentaires = relationship("CommentaireSalarie", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")
    heures_supp = relationship("HeuresSupp", cascade="all, delete-orphan")
    credit_conges = relationship("CreditConges", cascade="all, delete-orphan")

    def __init__(self, prenom="", nom="", diplomes="", **kwargs):
        Base.__init__(self, prenom=prenom, nom=nom, diplomes=diplomes, **kwargs)
        self.jours_conges = {}

    @reconstructor
    def init_on_load(self):
        self.calcule_jours_conges()

    def slug(self):
        return "salarie-%d" % self.idx

    def label(self):
        return "%s %s" % (self.prenom, self.nom)

    def is_date_conge(self, date):
        return date in self.creche.jours_fermeture or date in self.jours_conges

    def GetJourneeReference(self, date):
        if date in self.jours_conges:
            return Day()
        else:
            planning = self.get_planning(date)
            if planning:
                return planning.get_day_from_date(date)
            else:
                return None

    def GetJournee(self, date):
        if self.is_date_conge(date):
            return None

        contrat = self.get_contrat(date)
        if contrat is None:
            return None

        day = self.days.get(date, None)
        if day:
            return day

        return self.GetJourneeReference(date)

    def get_planning(self, date):
        result = None
        contrat = self.get_contrat(date)
        if contrat and contrat.debut:
            if self.creche.gestion_plannings_salaries == GESTION_GLOBALE_PLANNINGS_SALARIES:
                for planning in contrat.plannings:
                    if planning.debut and date >= planning.debut and (not planning.fin or date <= planning.fin):
                        if result is None or result.debut < planning.debut:
                            result = planning
            else:
                if contrat.plannings:
                    result = contrat.plannings[0]
                    if result.debut != contrat.debut:
                        result.debut = contrat.debut
        return result

    def get_contrat(self, date):
        for contrat in self.contrats:
            if contrat.debut and date >= contrat.debut and (not contrat.fin or date <= contrat.fin):
                return contrat
        return None

    def GetCongesAcquis(self, annee):
        ratio = 0.0
        for contrat in self.contrats:
            if contrat.debut:
                debut = max(contrat.debut, datetime.date(annee, 1, 1))
                fin = datetime.date(annee, 12, 31)
                if contrat.fin and contrat.fin < fin:
                    fin = contrat.fin
                duree_contrat = (fin - debut).days
                duree_annee = (datetime.date(annee, 12, 31) - datetime.date(annee, 1, 1)).days
                ratio += float(
                    duree_contrat) / duree_annee * contrat.GetNombreJoursPresenceSemaine() / self.creche.get_nombre_jours_semaine_travailles()
        return round(self.creche.conges_payes_salaries * ratio), round(self.creche.conges_supplementaires_salaries * ratio)

    def GetDecompteHeuresEtConges(self, debut, fin):
        affiche, contractualise, realise, cp, cs = False, 0.0, 0.0, 0, 0
        date = debut
        while date <= fin:
            planning = self.get_planning(date)
            if planning:
                journee_reference = planning.get_day_from_date(date)
                affiche = True
                heures_reference = journee_reference.get_duration()
                if heures_reference > 0 and (date in self.jours_conges or date in self.creche.jours_conges):
                    cp += 1
                else:
                    if date in self.days:
                        journee = self.days[date]
                        state = journee.get_state()
                        if state < 0:
                            if state == CONGES_PAYES:
                                cp += 1
                            elif state == VACANCES:
                                cs += 1
                            heures_reference = 0
                            heures_realisees = 0
                        else:
                            heures_realisees = journee.get_duration()
                    else:
                        heures_realisees = heures_reference
                    contractualise += heures_reference
                    realise += heures_realisees
            date += datetime.timedelta(1)
        return affiche, contractualise, realise, cp, cs

    def GetContrats(self, date_debut, date_fin):
        result = []
        if not date_debut:
            date_debut = datetime.date.min
        if not date_fin:
            date_fin = datetime.date.max
        for contrat in self.contrats:
            if contrat.debut:
                try:
                    date_debut_periode = contrat.debut
                    if contrat.fin:
                        date_fin_periode = contrat.fin
                    else:
                        date_fin_periode = datetime.date.max
                    if date_fin_periode < date_debut_periode:
                        print("Periode incorrecte pour %s %s :" % (self.prenom, self.nom), date_debut_periode, date_fin_periode)
                        continue
                    if ((date_debut_periode <= date_debut <= date_fin_periode) or
                            (date_debut_periode <= date_fin <= date_fin_periode) or
                            (date_debut < date_debut_periode and date_fin > date_fin_periode)):
                        result.append(contrat)
                except:
                    pass
        return result

    def add_conge(self, conge):
        self.conges.append(conge)
        self.calcule_jours_conges()

    def delete_conge(self, conge):
        self.conges.remove(conge)
        self.calcule_jours_conges()

    def calcule_jours_conges(self):
        self.jours_conges = {}

        def AddPeriode(debut, fin, conge):
            date = debut
            while date <= fin:
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
                print("Exception congés", e)

    def get_state(self, date):
        contrat = self.get_contrat(date)
        if contrat is None:
            return ABSENT
        if date in self.jours_conges and self.jours_conges[date].type is not None:
            return self.jours_conges[date].type
        if date in self.creche.jours_fermeture:
            return ABSENT

        reference = self.GetJourneeReference(date)
        ref_state = reference.get_state()  # TODO on peut s'en passer ?

        if date in self.days:
            day = self.days[date]
            state = day.get_state()  # TODO on peut s'en passer ?
            if state in (MALADE, HOPITAL, ABSENCE_NON_PREVENUE, CONGES_RECUP_HEURES_SUPP):
                return state
            elif state in (ABSENT, VACANCES):
                if ref_state:
                    return VACANCES
                else:
                    return ABSENT
            else:
                return PRESENT
        else:
            if ref_state:
                return PRESENT
            else:
                return ABSENT


class Professeur(Base):
    __tablename__ = "professeurs"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    prenom = Column(String)
    nom = Column(String)
    entree = Column(Date)
    sortie = Column(Date)


class HeuresSupp(Base):
    __tablename__ = "heures_supp"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship(Salarie)
    date = Column(Date)
    label = Column(String)
    value = Column(Float)

    def __init__(self, salarie, **kwargs):
        Base.__init__(self, salarie=salarie, **kwargs)


class CreditConges(Base):
    __tablename__ = "credit_conges"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship(Salarie)
    date = Column(Date)
    label = Column(String)
    value = Column(Float)

    def __init__(self, salarie, **kwargs):
        Base.__init__(self, salarie=salarie, **kwargs)


class Famille(Base):
    __tablename__ = "familles"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    adresse = Column(String, default="")
    code_postal = Column(Integer, default="")
    ville = Column(String, default="")
    numero_securite_sociale = Column(String, default="")
    numero_allocataire_caf = Column(String, default="")
    medecin_traitant = Column(String, default="")
    telephone_medecin_traitant = Column(String, default="")
    assureur = Column(String, default="")
    numero_police_assurance = Column(String, default="")
    code_client = Column(String, default="")
    tarifs = Column(Integer, default="")
    notes = Column(String, default="")
    iban = Column(String, default="")
    bic = Column(String, default="")
    mandate_id = Column(String, default="")
    jour_prelevement_automatique = Column(Integer, default="")
    date_premier_prelevement_automatique = Column(Date)
    autorisation_attestation_paje = Column(Boolean, default=True)
    inscrits = relationship("Inscrit", cascade="all, delete-orphan")
    freres_soeurs = relationship("Fratrie", cascade="all, delete-orphan")
    parents = relationship("Parent", cascade="all, delete-orphan")
    referents = relationship("Referent", cascade="all, delete-orphan")
    encaissements = relationship("EncaissementFamille", cascade="all, delete-orphan")

    def __init__(self, adresse="", code_postal="", ville="", notes="", automatic=True, **kwargs):
        Base.__init__(self, adresse=adresse, code_postal=code_postal, ville=ville, notes=notes, **kwargs)
        if "code_client" not in kwargs:
            self.code_client = ""
        if "numero_securite_sociale" not in kwargs:
            self.numero_securite_sociale = ""
        if "numero_allocataire_caf" not in kwargs:
            self.numero_allocataire_caf = ""
        if "medecin_traitant" not in kwargs:
            self.medecin_traitant = ""
        if "telephone_medecin_traitant" not in kwargs:
            self.telephone_medecin_traitant = ""
        if "assureur" not in kwargs:
            self.assureur = ""
        if "numero_police_assurance" not in kwargs:
            self.numero_police_assurance = ""
        if "iban" not in kwargs:
            self.iban = ""
        if "bic" not in kwargs:
            self.bic = ""
        if "mandate_id" not in kwargs:
            self.mandate_id = ""
        if "jour_prelevement_automatique" not in kwargs:
            self.jour_prelevement_automatique = ""
        if "tarifs" not in kwargs:
            self.tarifs = 0
        if automatic:
            self.parents = [
                Parent(self, MASCULIN),
                Parent(self, FEMININ)
            ]

    def get_delai_paiement(self):
        return self.creche.delai_paiement_familles

    def get_parents_emails(self):
        result = []
        for parent in self.parents:
            if parent.email:
                result.append(parent.email)
        return ", ".join(result)

    def GetEnfantsCount(self, date):
        enfants_a_charge = 0
        enfants_en_creche = 0
        debut, fin = None, None
        for frere_soeur in self.freres_soeurs:
            if frere_soeur.naissance:
                if frere_soeur.naissance <= date:
                    if not debut or frere_soeur.naissance > debut:
                        debut = frere_soeur.naissance
                    enfants_a_charge += 1
                    if frere_soeur.entree and frere_soeur.entree <= date and (
                            frere_soeur.sortie is None or frere_soeur.sortie > date):
                        enfants_en_creche += 1
                else:
                    if not fin or frere_soeur.naissance < fin:
                        fin = frere_soeur.naissance
        for inscrit in self.inscrits:
            if inscrit.naissance:
                if inscrit.naissance <= date:
                    if not debut or inscrit.naissance > debut:
                        debut = inscrit.naissance
                    enfants_a_charge += 1
                    inscription = inscrit.get_inscription(date)
                    if inscription and inscription.debut and inscription.debut <= date and (inscription.fin is None or inscription.fin > date):
                        enfants_en_creche += 1
                else:
                    if not fin or inscrit.naissance < fin:
                        fin = inscrit.naissance
        return enfants_a_charge, enfants_en_creche, debut, fin

    def get_code_client(self):
        if self.code_client or config.codeclient == "custom":
            return self.code_client
        else:
            for inscrit in self.inscrits:
                return "411%s" % inscrit.nom.upper()[:5]
        return ""

    def get_prenoms(self):
        if len(self.inscrits) == 1:
            return self.inscrits[0].prenom
        else:
            return ", ".join([inscrit.prenom for inscrit in self.inscrits[:-1]]) + " et " + self.inscrits[-1].prenom


class State(object):
    def __init__(self, state, heures_contractualisees=.0, heures_realisees=.0, heures_facturees=.0):
        self.state = state
        self.heures_contractualisees = heures_contractualisees
        self.heures_realisees = heures_realisees
        self.heures_facturees = heures_facturees

    def __str__(self):
        return "state:%d, contrat:%f, realise:%f, facture:%f" % (
        self.state, self.heures_contractualisees, self.heures_realisees, self.heures_facturees)


def GetUnionTimeslots(timeslots, value=0):
    again = True
    while again:
        again = False
        backup = timeslots[:]
        timeslots = []
        for timeslot1 in backup:
            found = False
            for i, timeslot2 in enumerate(timeslots):
                if timeslot1.fin < timeslot2.debut or timeslot1.debut > timeslot2.fin:
                    pass
                elif timeslot1.debut >= timeslot2.debut and timeslot1.fin <= timeslot2.fin:
                    found = True
                elif timeslot1.debut <= timeslot2.debut or timeslot1.fin >= timeslot2.fin:
                    timeslots[i] = Timeslot(min(timeslot2.debut, timeslot1.debut), max(timeslot2.fin, timeslot1.fin), timeslot1.activity, value=value)
                    found = True
            if not found:
                timeslots.append(timeslot1)
            else:
                again = True
    return timeslots


def GetUnionHeures(journee, reference):
    timeslots = [timeslot for timeslot in journee.timeslots if timeslot.activity.mode == 0]
    timeslots += [timeslot for timeslot in reference.timeslots if timeslot.activity.mode == 0]
    return GetUnionTimeslots(timeslots)


class Inscrit(Base):
    __tablename__ = "inscrits"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    famille = relationship(Famille)
    prenom = Column(String, default="")
    nom = Column(String, default="")
    sexe = Column(Integer, default=MASCULIN)
    naissance = Column(Date)
    handicap = Column(Boolean, default=False)
    marche = Column(Boolean, default=False)
    photo = Column(String)
    notes = Column(String, default="")
    combinaison = Column(String, default="")
    categorie_id = Column(Integer, ForeignKey("categories.idx"))
    categorie = relationship("Categorie")
    allergies = Column(String, default="")
    garde_alternee = Column(Boolean, default=False)
    type_repas = Column(Integer, default=REPAS_PUREE)
    type_repas2 = Column(Integer, default=REPAS_ASSIETTE)
    date_premier_contact = Column(Date)
    date_entretien_directrice = Column(Date)
    date_envoi_devis = Column(Date)
    date_reponse_parents = Column(Date)
    preinscription_state = Column(Integer)
    inscriptions = relationship("Inscription", cascade="all, delete-orphan")
    days = relationship("TimeslotInscrit", collection_class=lambda: DayCollection("date"), cascade="all, delete-orphan")
    weekslots = relationship("WeekSlotInscrit", cascade="all, delete-orphan")
    commentaires = relationship("CommentaireInscrit", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")
    clotures = relationship("ClotureFacture", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")
    conges = relationship("CongeInscrit", cascade="all, delete-orphan")
    corrections = relationship("Correction", collection_class=attribute_mapped_collection("date"), cascade="all, delete-orphan")

    def __init__(self, prenom="", nom="", sexe=MASCULIN, handicap=False, allergies="", automatic=True, **kwargs):
        Base.__init__(self, prenom=prenom, nom=nom, sexe=sexe, handicap=handicap, allergies=allergies, **kwargs)
        self.famille = Famille(creche=self.creche, automatic=automatic)
        if automatic:
            self.inscriptions.append(Inscription(inscrit=self))
        self.jours_conges = {}

    @reconstructor
    def init_on_load(self):
        self.calcule_jours_conges()

    def slug(self):
        return "child-%d" % self.idx

    def get_preinscription_state(self):
        if self.preinscription_state >= STATE_ACCORD_PARENTS:
            pass
        elif not self.date_premier_contact:
            self.preinscription_state = STATE_PREINSCRIPTION_RECUE
        elif not self.date_entretien_directrice:
            self.preinscription_state = STATE_ATTENTE_ENTRETIEN
        elif self.date_entretien_directrice > datetime.date.today():
            self.preinscription_state = STATE_ENTRETIEN_PROGRAMME
        elif not self.date_envoi_devis:
            self.preinscription_state = STATE_DEVIS_A_ENVOYER
        elif not self.date_reponse_parents:
            self.preinscription_state = STATE_ATTENTE_REPONSE_PARENTS
        else:
            self.preinscription_state = STATE_ATTENTE_REPONSE_PARENTS
        return self.preinscription_state

    def get_groupe_order(self, date):
        inscription = self.get_inscription(date)
        return inscription.groupe.ordre if inscription and inscription.groupe else 255

    def get_groupe_auto(self):
        result = None
        age = GetAge(self.naissance)
        for groupe in self.creche.groupes:
            if not groupe.age_maximum or age <= groupe.age_maximum:
                if result is None or not result.age_maximum or (groupe.age_maximum and groupe.age_maximum < result.age_maximum):
                    result = groupe
        return result

    def get_facture_cloturee(self, date):
        if self.creche.temps_facturation == FACTURATION_FIN_MOIS:
            result = self.clotures.get(GetMonthEnd(date), None)
            if result:
                return result
        return self.clotures.get(GetMonthStart(date), None)

    def get_week_slots(self, monday):
        return [weekslot for weekslot in self.weekslots if weekslot.date == monday]

    def get_week_activity_slot(self, monday, value):
        for weekslot in self.weekslots:
            if weekslot.date == monday and weekslot.activity == value:
                return weekslot
        else:
            return None

    def add_conge(self, conge):
        self.conges.append(conge)
        self.calcule_jours_conges()

    def delete_conge(self, conge):
        self.conges.remove(conge)
        self.calcule_jours_conges()

    def calcule_jours_conges(self):
        self.jours_conges = {}

        def AddPeriode(debut, fin, conge):
            date = debut
            while date <= fin:
                if date not in self.creche.jours_fermeture:
                    self.jours_conges[date] = conge
                date += datetime.timedelta(1)

        for conge in self.conges:
            if conge.debut:
                try:
                    count = conge.debut.count('/')
                    if count == 2:
                        debut = str2date(conge.debut)
                        if not conge.fin or conge.fin.strip() == "":
                            fin = debut
                        else:
                            fin = str2date(conge.fin)
                        AddPeriode(debut, fin, conge)
                    elif count == 1:
                        for year in range(config.first_date.year, config.last_date.year + 1):
                            debut = str2date(conge.debut, year)
                            if not conge.fin or conge.fin.strip() == "":
                                fin = debut
                            else:
                                fin = str2date(conge.fin, year)
                            AddPeriode(debut, fin, conge)
                except Exception as e:
                    # print("Exception congé", e)
                    pass

    def is_present(self, debut, fin, site=None, handicap=None, reservataire=None):
        for inscription in self.inscriptions:
            if ((inscription.fin is None or inscription.fin >= debut) and
                    (not self.creche.preinscriptions or not inscription.preinscription) and
                    (site is None or inscription.site == site) and
                    (reservataire is None or inscription.reservataire == reservataire) and
                    (inscription.debut is not None) and
                    (not fin or inscription.debut <= fin) and
                    (handicap is None or self.handicap == handicap)):
                return True
        return False

    def get_mode_arrondi(self):
        return self.creche.arrondi_heures

    def get_allergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",")]

    def has_facture(self, date, site=None):
        if not date:  # or date.month in database.creche.mois_sans_facture:
            return False
        month_start = GetMonthStart(date)
        month_end = GetMonthEnd(date)
        if self.get_inscriptions(month_start, month_end, site):
            return True
        if self.creche.temps_facturation != FACTURATION_FIN_MOIS:
            previous_month_end = month_start - datetime.timedelta(1)
            previous_month_start = GetMonthStart(previous_month_end)
            if self.get_inscriptions(previous_month_start, previous_month_end, site):
                day = previous_month_start
                while day.month == previous_month_start.month:
                    state = self.GetState(day)
                    if state.heures_facturees != state.heures_contractualisees:
                        return True
                    day += datetime.timedelta(1)
        return False

    def get_factures_list(self):
        result = []
        date = config.get_first_monday()
        while date <= datetime.date.today():
            if self.has_facture(date):
                result.append(date)
            date = GetNextMonthStart(date)
        return result

    def GetPeriodeInscriptions(self):
        if len(self.inscriptions) == 0:
            return None, None
        else:
            debut, fin = self.inscriptions[0].debut, self.inscriptions[0].fin
            for inscription in self.inscriptions:
                if debut is None or (inscription.debut is not None and inscription.debut < debut):
                    debut = inscription.debut
                if fin is not None and (inscription.fin is None or inscription.fin > fin):
                    fin = inscription.fin
            return debut, fin

    def get_planning(self, date):
        return self.get_inscription(date)

    def get_contrat(self, date):
        return self.get_inscription(date)

    def get_inscription(self, date, preinscription=False, departanticipe=True, array=False):
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

    def get_inscriptions(self, date_debut=None, date_fin=None, site=None, preinscriptions=False):
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
        result.sort(key=lambda inscription: inscription.debut)
        return result

    def is_date_conge(self, date):
        if date in self.creche.jours_fermeture:
            return True
        if date in self.jours_conges:
            if self.creche.conges_inscription != GESTION_CONGES_INSCRIPTION_MENSUALISES_AVEC_POSSIBILITE_DE_SUPPLEMENT:
                return True
            if date in self.days:
                return self.days[date].get_state() == ABSENT
        return False

    def GetRattachement(self):
        result = None
        for inscrit in self.creche.inscrits:
            if inscrit is not self:
                if inscrit.famille is self.famille:
                    return True
                if inscrit.nom == self.nom:
                    result = False
        return result

    def ChangeRattachement(self, state):
        if state:
            for inscrit in self.creche.inscrits:
                if inscrit is not self and inscrit.nom == self.nom:
                    self.famille = inscrit.famille
                    break
        else:
            self.famille = Famille(creche=self.creche)

    def GetJournee(self, date):
        if self.is_date_conge(date):
            return None

        inscription = self.get_inscription(date)
        if inscription is None:
            return None

        result = self.days.get(date, None)
        if result:
            return result

        return self.GetJourneeReference(date)

    def GetJourneeReference(self, date):
        if date in self.jours_conges:
            return Day()
        else:
            inscription = self.get_inscription(date)
            if inscription:
                return inscription.get_day_from_date(date)
            else:
                return None

    def get_nombre_jours_maladie(self, date):
        # recherche du premier et du dernier jour
        premier_jour_maladie = tmp = date
        nombre_jours_ouvres_maladie = 0
        pile = 0
        while tmp > self.inscriptions[0].debut:
            tmp -= datetime.timedelta(1)
            state = self.get_state(tmp)
            if tmp not in self.creche.jours_fermeture:
                pile += 1
            if state == MALADE:
                premier_jour_maladie = tmp
                if self.creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS:
                    nombre_jours_ouvres_maladie += 1
                else:
                    nombre_jours_ouvres_maladie += pile
                pile = 0
            elif state != ABSENT:
                break
        if self.creche.traitement_maladie in (DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES, DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS):
            nombre_jours_maladie = nombre_jours_ouvres_maladie + 1
        elif self.creche.traitement_maladie == DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES:
            nombre_jours_maladie = (date - premier_jour_maladie).days + 1
        else:
            dernier_jour_maladie = tmp = date
            while not self.inscriptions[-1].fin or tmp < self.inscriptions[-1].fin:
                tmp += datetime.timedelta(1)
                state = self.get_state(tmp)
                if state == MALADE:
                    dernier_jour_maladie = tmp
                else:
                    break
            nombre_jours_maladie = (dernier_jour_maladie - premier_jour_maladie).days + 1
        return nombre_jours_maladie

    def GetState(self, date, mode_arrondi=SANS_ARRONDI):
        """Retourne les infos sur une journée
        :param date: la journée
        """

        if self.is_date_conge(date):
            return State(ABSENT)

        inscription = self.get_inscription(date)
        if inscription is None:
            return State(ABSENT)

        reference = self.GetJourneeReference(date)  # Attention pas depuis inscription à cause des congés inscription avec supplément
        heures_reference = reference.get_duration(mode_arrondi)
        ref_state = reference.get_state()

        if date in self.days:
            journee = self.days[date]
            state = journee.get_state()
            if state == ABSENCE_NON_PREVENUE:
                heures_facturees = heures_reference
                if heures_facturees == 0:
                    for timeslot in journee.timeslots:
                        if timeslot.activity.mode == MODE_ABSENCE_NON_PREVENUE:
                            heures_facturees += timeslot.get_duration()
                        heures_facturees = heures_facturees / 60
                return State(state, heures_reference, 0, heures_facturees)
            elif state == HOPITAL:
                return State(state, heures_reference, 0, 0)
            elif state == MALADE and self.get_nombre_jours_maladie(date) > self.creche.minimum_maladie:
                return State(state, heures_reference, 0, 0)
            elif state in (MALADE, MALADE_SANS_JUSTIFICATIF, ABSENCE_NON_PREVENUE, ABSENCE_CONGE_SANS_PREAVIS):
                return State(state, heures_reference, 0, heures_reference)
            elif state in (ABSENT, VACANCES):
                if inscription.mode == MODE_TEMPS_PLEIN or ref_state:
                    return State(VACANCES, heures_reference, 0, heures_reference)
                else:
                    return State(ABSENT, heures_reference, 0, heures_reference)
            else:  # PRESENT
                tranche = 5.0 / 60
                heures_realisees = 0.0
                heures_facturees = 0.0

                # TODO une petite fonction pour ce code duplique dans le test
                timeslots = GetUnionTimeslots([timeslot for timeslot in journee.timeslots if timeslot.activity.mode in (0, MODE_PRESENCE_NON_FACTUREE)])
                for timeslot in timeslots:
                    heures_realisees += tranche * GetDureeArrondie(self.creche.arrondi_heures, timeslot.debut, timeslot.fin)

                if self.creche.nom == "Le Nid Des Trésors" and not inscription.IsInPeriodeAdaptation(date):
                    # TODO ajouter un paramètre quand la branche SQLAlchemy sera mergée
                    for timeslot in journee.timeslots:
                        if timeslot.activity.mode == MODE_PRESENCE:
                            heures_facturees += tranche * GetDureeArrondie(self.creche.arrondi_facturation, timeslot.debut, timeslot.fin)
                    heures_facturees = max(heures_facturees, heures_reference)
                else:
                    union = GetUnionHeures(journee, reference)
                    if inscription.IsInPeriodeAdaptation(date):
                        if self.creche.facturation_periode_adaptation == FACTURATION_HORAIRES_REELS:
                            union = journee.timeslots
                        for timeslot in union:
                            heures_facturees += tranche * GetDureeArrondie(self.creche.arrondi_facturation_periode_adaptation, timeslot.debut, timeslot.fin)
                    else:
                        for timeslot in union:
                            heures_facturees += tranche * GetDureeArrondie(self.creche.arrondi_facturation, timeslot.debut, timeslot.fin)

                return State(PRESENT, heures_reference, heures_realisees, heures_facturees)
        else:
            if ref_state:
                return State(PRESENT, heures_reference, heures_reference, heures_reference)
            else:
                return State(ABSENT)

    def label(self):
        return "%s %s" % (self.prenom, self.nom)

    def get_state(self, date):
        if self.is_date_conge(date):
            return ABSENT
        elif date in self.days:
            return self.days[date].get_state()
        else:
            inscription = self.get_inscription(date)
            return inscription.get_day_from_date(date).get_state() if inscription else ABSENT

    def GetExtraActivites(self, date):
        # TODO il y a un problème avec les CONGES_AVEC_POSSIBILITE_DE_SUPPLEMENT parce que la journée retournée est la journée de référence et donc les activités sont comptées à tort
        day = self.GetJournee(date)
        if day is None:
            return []
        result = set()
        for timeslot in day.timeslots:
            if timeslot.activity.mode > 0:
                result.add(timeslot)
        if result:
            for activity in self.creche.activites:
                if activity.mode == MODE_SYSTEMATIQUE_SANS_HORAIRES:
                    result.add(Timeslot(debut=None, fin=None, activity=activity))
        return result

    def GetTotalActivitesPresenceNonFacturee(self, date):
        day = self.GetJournee(date)
        return 0 if day is None else day.get_duration_per_activity_mode(MODE_PRESENCE_NON_FACTUREE)

    def GetTotalActivitesPresenceFactureesEnSupplement(self, date):
        day = self.GetJournee(date)
        return 0 if day is None else day.get_duration_per_activity_mode(MODE_PRESENCE_SUPPLEMENTAIRE)

    def GetTotalActivitesConges(self, date):
        day = self.GetJournee(date)
        return 0 if day is None else day.get_duration_per_activity_mode(MODE_CONGES)

    def GetDecomptePermanences(self):
        today = datetime.date.today()
        total, effectue = 0.0, 0.0
        date = self.creche.date_raz_permanences
        if date:
            while date < today:
                journee = self.GetJournee(date)
                if journee:
                    effectue += journee.get_duration_permanences()
                date += datetime.timedelta(1)
            anniversaire = GetDateAnniversaire(self.creche.date_raz_permanences)
            for inscription in self.inscriptions:
                if inscription.debut is not None and self.creche.date_raz_permanences <= inscription.debut < today:
                    fin = inscription.fin if inscription.fin else anniversaire
                    if fin < today:
                        total += inscription.heures_permanences
                    else:
                        total += inscription.heures_permanences * (today - inscription.debut).days / (fin - inscription.debut).days
        return total, effectue

    def get_regime(self, date):
        for parent in self.famille.parents:
            if parent:
                revenu = Select(parent.revenus, date)
                if revenu and revenu.regime:
                    return revenu.regime
        return 0


class Parent(Base):
    __tablename__ = "parents"
    idx = Column(Integer, primary_key=True)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    famille = relation(Famille)
    sexe = Column(Integer, default=MASCULIN)
    prenom = Column(String, default="")
    nom = Column(String, default="")
    adresse = Column(String, default="")
    code_postal = Column(Integer, default="")
    ville = Column(String, default="")
    telephone_domicile = Column(String, default="")
    telephone_domicile_notes = Column(String, default="")
    telephone_portable = Column(String, default="")
    telephone_portable_notes = Column(String, default="")
    telephone_travail = Column(String, default="")
    telephone_travail_notes = Column(String, default="")
    profession = Column(String, default="")
    email = Column(String, default="")
    revenus = relationship("Revenu", cascade="all, delete-orphan")

    def __init__(self, famille, sexe=FEMININ, prenom="", nom="", adresse="", code_postal="", ville="",
                 telephone_domicile="", telephone_domicile_notes="", telephone_portable="", telephone_portable_notes="", telephone_travail="", telephone_travail_notes="",
                 profession="", email="", add_revenus=True, **kwargs):
        Base.__init__(self,
                      famille=famille,
                      sexe=sexe,
                      prenom=prenom,
                      nom=nom,
                      adresse=adresse,
                      code_postal=code_postal,
                      ville=ville,
                      telephone_domicile=telephone_domicile,
                      telephone_domicile_notes=telephone_domicile_notes,
                      telephone_portable=telephone_portable,
                      telephone_portable_notes=telephone_portable_notes,
                      telephone_travail=telephone_travail,
                      telephone_travail_notes=telephone_travail_notes,
                      profession=profession,
                      email=email,
                      **kwargs)
        if add_revenus:
            date_revenus = famille.creche.GetDateRevenus(datetime.date.today())
            self.revenus.append(Revenu(self, GetYearStart(date_revenus), GetYearEnd(date_revenus)))


class Fratrie(Base):
    __tablename__ = "fratries"
    idx = Column(Integer, primary_key=True)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    famille = relationship(Famille)
    prenom = Column(String)
    naissance = Column(Date)
    entree = Column(Date)
    sortie = Column(Date)

    def __init__(self, famille, prenom=None, naissance=None, entree=None, sortie=None):
        Base.__init__(self, famille=famille, prenom=prenom, naissance=naissance, entree=entree, sortie=sortie)


class Referent(Base):
    __tablename__ = "referents"
    idx = Column(Integer, primary_key=True)
    famille_id = Column(Integer, ForeignKey("familles.idx"))
    famille = relationship(Famille)
    prenom = Column(String)
    nom = Column(String)
    telephone = Column(String)

    def __init__(self, famille, prenom=None, nom=None, telephone=None):
        Base.__init__(self, famille=famille, prenom=prenom, nom=nom, telephone=telephone)


class Inscription(Base, PeriodeReference):
    __tablename__ = "inscriptions"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    preinscription = Column(Boolean)
    reservataire_id = Column(Integer, ForeignKey("reservataires.idx"))
    reservataire = relationship(Reservataire)
    groupe_id = Column(Integer, ForeignKey("groupes.idx"))
    groupe = relationship("Groupe")
    forfait_mensuel = Column(Float, default=0)
    frais_inscription = Column(Float, default=0)
    allocation_mensuelle_caf = Column(Float)
    site_id = Column(Integer, ForeignKey("sites.idx"))
    site = relationship(Site)
    _sites_preinscription = Column(String, name="sites_preinscription")
    professeur_id = Column(Integer, ForeignKey("professeurs.idx"))
    professeur = relationship(Professeur)
    debut_asap = Column(Boolean)
    debut = Column(Date)
    fin = Column(Date)
    depart = Column(Date)
    mode = Column(Integer)
    fin_periode_adaptation = Column(Date)
    duree_reference = Column(Integer, default=7)
    forfait_mensuel_heures = Column(Float, default=0)
    semaines_conges = Column(Integer, default=0)
    heures_permanences = Column(Float, default=0)
    newsletters = Column(Integer, default="")
    tarifs = Column(Integer, default=0)
    days = relationship("TimeslotInscription", collection_class=lambda: DayCollection("day"), cascade="all, delete-orphan")

    def __init__(self, inscrit, mode=MODE_TEMPS_PARTIEL, duree_reference=7, debut=datetime.date.today(), forfait_mensuel_heures=0, forfait_mensuel=0, frais_inscription=0, semaines_conges=0, heures_permanences=0, tarifs=0, allocation_mensuelle_caf=0, **kwargs):
        Base.__init__(self, inscrit=inscrit, mode=mode, duree_reference=duree_reference, debut=debut, forfait_mensuel_heures=forfait_mensuel_heures, forfait_mensuel=forfait_mensuel, frais_inscription=frais_inscription, semaines_conges=semaines_conges, heures_permanences=heures_permanences, tarifs=tarifs, allocation_mensuelle_caf=allocation_mensuelle_caf, **kwargs)
        if is_power_of_two(inscrit.creche.modes_inscription):
            self.mode = int(math.log(inscrit.creche.modes_inscription, 2))
        self.__dict__["sites_preinscription"] = []

    @reconstructor
    def init_on_load(self):
        self.__dict__["sites_preinscription"] = []
        if self._sites_preinscription:
            sites_list = [int(index) for index in self._sites_preinscription.split()]
            for site in self.inscrit.creche.sites:
                if site.idx in sites_list:
                    self.sites_preinscription.append(site)

    def __setattr__(self, name, value):
        Base.__setattr__(self, name, value)
        # TODO remove this in next conversions
        if name == "sites_preinscription":
            self._sites_preinscription = " ".join([str(value.idx) for value in value])

    def GetNombreJoursCongesPeriode(self):
        if self.preinscription:
            return 0
        elif self.semaines_conges:
            if self.mode == MODE_FORFAIT_HEBDOMADAIRE:
                return self.semaines_conges * 7
            else:
                return self.semaines_conges * self.get_days_per_week()
        else:
            return 0

    def GetJoursCongesPris(self, debut, fin):
        result = []
        date = debut
        # print "GetJoursCongesPris(%s - %s)" % (debut, fin)
        while date <= fin:
            if self.mode in (MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_MENSUEL):
                if date in self.inscrit.creche.periodes_fermeture or date in self.inscrit.jours_conges:
                    result.append(date)
            else:
                reference = self.get_day_from_date(date)
                if reference.get_duration() > 0:
                    state = self.inscrit.get_state(date)
                    if state in (ABSENT, VACANCES):
                        result.append(date)
                # TODO pour Nid des tresors le 24/05/2018 test non reg ?
                # state = self.inscrit.get_state(date)
                # if self.inscrit.creche.facturation_jours_feries == ABSENCES_DEDUITES_EN_JOURS:
                #     if state == VACANCES:
                #
                #         result.append(date)
                # else:
                #     if state in (ABSENT, VACANCES):
                #         reference = self.get_day_from_date(date)
                #         if reference.get_duration() > 0:
                #             result.append(date)
            date += datetime.timedelta(1)
        return result

    def GetNombreHeuresConsommeesForfait(self):
        if self.mode == MODE_FORFAIT_GLOBAL_CONTRAT and self.debut and self.fin:
            compteur = self.forfait_mensuel_heures
            date = self.debut
            while date <= self.fin:
                day = self.inscrit.GetJournee(date)
                if day:
                    compteur -= day.get_duration()
                date += datetime.timedelta(1)
            return compteur
        else:
            return None

    def GetDebutDecompteJoursConges(self):
        if self.fin_periode_adaptation:
            return self.fin_periode_adaptation + datetime.timedelta(1)
        else:
            return self.debut

    def GetFin(self):
        return self.depart if (self.inscrit.creche.gestion_depart_anticipe and self.depart) else (self.fin if self.fin else datetime.date.max)

    def GetFinDecompteJoursConges(self):
        if self.inscrit.creche.gestion_depart_anticipe and self.depart:
            return self.depart
        else:
            return self.fin

    def GetJoursCongesPoses(self):
        if self.debut and self.fin and not self.preinscription:
            return self.GetJoursCongesPris(self.GetDebutDecompteJoursConges(), self.GetFinDecompteJoursConges())
        else:
            return []

    def GetNombreJoursCongesPoses(self):
        return len(self.GetJoursCongesPoses())

    def IsNombreSemainesCongesDepasse(self, jalon):
        if self.inscrit.creche.facturation_jours_feries == ABSENCES_DEDUITES_SANS_LIMITE:
            return False
        if self.mode == MODE_FORFAIT_GLOBAL_CONTRAT:
            return False
        if self.debut:
            if not self.semaines_conges:
                return True
            debut = self.GetDebutDecompteJoursConges()
            pris = len(self.GetJoursCongesPris(debut, jalon))
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

    def GetListeActivites(self):
        result = []
        for i in range(self.duree_reference):
            jour = self.get_day_from_index(i)
            s = jour.GetHeureArriveeDepart()
            if s:
                if self.duree_reference <= 7:
                    s = days[i] + " " + s
                else:
                    s = days[i % 7] + " semaine %d" % (1 + (i / 7)) + s
                result.append(s)
        return ', '.join(result)


class TrancheCapacite(Base, Timeslot):
    __tablename__ = "capacite"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    jour = Column(Integer)
    debut = Column(Integer)
    fin = Column(Integer)
    value = Column(Integer)

    def __init__(self, **kwargs):
        Base.__init__(self, **kwargs)
        self.activity = self.creche.states[0]

    @reconstructor
    def init_on_load(self):
        self.activity = self.creche.states[0]


class TimeslotInscription(Base, Timeslot):
    __tablename__ = "ref_activities"
    idx = Column(Integer, primary_key=True)
    inscription_id = Column(Integer, ForeignKey("inscriptions.idx"))
    inscription = relationship(Inscription)
    day = Column(Integer)
    activity_id = Column(Integer, ForeignKey("activities.idx"), name="activity")
    activity = relationship(Activite)
    debut = Column(Integer)
    fin = Column(Integer)

    def get_inscrit(self):
        return self.inscription.inscrit


class TimeslotPlanningSalarie(Base, Timeslot):
    __tablename__ = "ref_journees_salaries"
    idx = Column(Integer, primary_key=True)
    reference = Column(Integer, ForeignKey("contrats.idx"))
    planning = relationship("PlanningSalarie")
    day = Column(Integer)
    activity_id = Column(Integer, ForeignKey("activities.idx"), name="activity")
    activity = relationship(Activite)
    debut = Column(Integer)
    fin = Column(Integer)


class Revenu(Base):
    __tablename__ = "revenus"
    idx = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("parents.idx"))
    parent = relationship(Parent)
    debut = Column(Date)
    fin = Column(Date)
    revenu = Column(Integer, default="")
    chomage = Column(Boolean, default=False)
    conge_parental = Column(Boolean, default=False)
    regime = Column(Integer, default=0)

    def __init__(self, parent, debut=None, fin=None, revenu="", chomage=False, conge_parental=False, regime=0, **kwargs):
        Base.__init__(self, parent=parent, debut=debut, fin=fin, revenu=revenu, chomage=chomage, conge_parental=conge_parental, regime=regime, **kwargs)


class CommentaireInscrit(Base):
    __tablename__ = "commentaires"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    date = Column(Date)
    commentaire = Column(String)


class TimeslotInscrit(Base, Timeslot):
    __tablename__ = "activites"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    date = Column(Date)
    activity_id = Column(Integer, ForeignKey("activities.idx"), name="activity")
    activity = relationship(Activite)
    debut = Column(Integer)
    fin = Column(Integer)

    def get_inscrit(self):
        return self.inscrit


class WeekSlotInscrit(Base):
    __tablename__ = "planning_hebdomadaire"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    date = Column(Date)
    activity = Column(Integer)
    value = Column(Float)


class TimeslotSalarie(Base, Timeslot):
    __tablename__ = "activites_salaries"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship(Salarie)
    date = Column(Date)
    activity_id = Column(Integer, ForeignKey("activities.idx"), name="activity")
    activity = relationship(Activite)
    debut = Column(Integer)
    fin = Column(Integer)


class CommentaireSalarie(Base):
    __tablename__ = "commentaires_salaries"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship(Salarie)
    date = Column(Date)
    commentaire = Column(String)


class User(Base):
    __tablename__ = "users"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    login = Column(String)
    password = Column(String)
    email = Column(String)
    flags = Column(Integer)
    profile = Column(Integer, default=PROFIL_ALL | PROFIL_ADMIN)

    def __init__(self, creche, profile=PROFIL_ALL, **kwargs):
        Base.__init__(self, creche=creche, profile=profile, **kwargs)


class CongeStructure(Base):
    __tablename__ = "conges"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    debut = Column(String)
    fin = Column(String)
    label = Column(String)
    options = Column(Integer)

    def __init__(self, creche, debut=None, fin=None, label=None, options=0):
        Base.__init__(self, creche=creche, debut=debut, fin=fin, label=label, options=options)

    def __setattr__(self, name, value):
        # Call the parent class method first.
        super(CongeStructure, self).__setattr__(name, value)
        if self.creche and name in ("debut", "fin"):
            self.creche.calcule_jours_conges()

    def is_jour_ferie(self):
        if "/" in self.debut:
            return False
        else:
            return self.debut in [tmp[0] for tmp in jours_fermeture]


class CongeInscrit(Base):
    __tablename__ = "conges_inscrits"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    debut = Column(String)
    fin = Column(String)
    label = Column(String)

    def __init__(self, inscrit, **kwargs):
        Base.__init__(self, inscrit=inscrit, **kwargs)

    def __setattr__(self, name, value):
        # Call the parent class method first.
        super(CongeInscrit, self).__setattr__(name, value)
        if self.inscrit and name in ("debut", "fin"):
            self.inscrit.calcule_jours_conges()


class CongeSalarie(Base):
    __tablename__ = "conges_salaries"
    idx = Column(Integer, primary_key=True)
    salarie_id = Column(Integer, ForeignKey("employes.idx"))
    salarie = relationship(Salarie)
    debut = Column(String)
    fin = Column(String)
    label = Column(String)
    type = Column(Integer)

    def __init__(self, salarie, debut=None, fin=None, label=None):
        Base.__init__(self, salarie=salarie, debut=debut, fin=fin, label=label)

    def __setattr__(self, name, value):
        # Call the parent class method first.
        super(CongeSalarie, self).__setattr__(name, value)
        if self.salarie and name in ("debut", "fin"):
            self.salarie.calcule_jours_conges()


class Alerte(Base):
    __tablename__ = "alertes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    texte = Column(String)
    date = Column(Date)
    acquittement = Column(Boolean)


class Charge(Base):
    __tablename__ = "charges"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    date = Column(Date)
    charges = Column(Float)


class ClotureFacture(Base):
    __tablename__ = "factures"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    date = Column(Date)
    cotisation_mensuelle = Column(Float)
    total_contractualise = Column(Float)
    total_realise = Column(Float)
    total_facture = Column(Float)
    supplement_activites = Column(Float)
    supplement = Column(Float)
    deduction = Column(Float)

    def __getattribute__(self, item):
        if item == "total":
            return self.total_facture
        else:
            return Base.__getattribute__(self, item)


class EncaissementFamille(Base):
    __tablename__ = "encaissements"
    idx = Column(Integer, primary_key=True)
    famille_idx = Column(Integer, ForeignKey("familles.idx"), name="famille")
    famille = relationship(Famille)
    date = Column(Date)
    valeur = Column(Float)
    moyen_paiement = Column(Integer)
    label = Column(String)

    def __init__(self, famille, **kwargs):
        Base.__init__(self, famille=famille, **kwargs)


class EncaissementReservataire(Base):
    __tablename__ = "encaissements_reservataires"
    idx = Column(Integer, primary_key=True)
    reservataire_idx = Column(Integer, ForeignKey("reservataires.idx"), name="reservataire")
    reservataire = relationship(Reservataire)
    date = Column(Date)
    valeur = Column(Float)
    moyen_paiement = Column(Integer)
    label = Column(String)

    def __init__(self, reservataire, **kwargs):
        Base.__init__(self, reservataire=reservataire, **kwargs)


class NumeroFacture(Base):
    __tablename__ = "numeros_facture"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    date = Column(Date)
    valeur = Column(Integer)


class Correction(Base):
    __tablename__ = "corrections"
    idx = Column(Integer, primary_key=True)
    inscrit_id = Column(Integer, ForeignKey("inscrits.idx"))
    inscrit = relationship(Inscrit)
    date = Column(Date)
    valeur = Column(Float)
    libelle = Column(String)

    def __init__(self, inscrit, date, **kwargs):
        Base.__init__(self, inscrit=inscrit, date=date, **kwargs)


class Groupe(Base):
    __tablename__ = "groupes"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    nom = Column(String)
    ordre = Column(Integer)
    age_maximum = Column(Integer)

    def __init__(self, creche, **kwargs):
        Base.__init__(self, creche=creche, **kwargs)


class Categorie(Base):
    __tablename__ = "categories"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    nom = Column(String)


class TarifSpecial(Base):
    __tablename__ = "tarifsspeciaux"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    label = Column(String)
    type = Column(Integer)
    unite = Column(Integer)
    valeur = Column(Float)
    portee = Column(Integer)

    def __init__(self, creche, **kwargs):
        Base.__init__(self, creche=creche, **kwargs)


class PlageHoraire(Base):
    __tablename__ = "plageshoraires"
    idx = Column(Integer, primary_key=True)
    creche_id = Column(Integer, ForeignKey("creche.idx"))
    creche = relationship(Creche)
    debut = Column(Float)
    fin = Column(Float)
    flags = Column(Integer)


class Database(object):
    def __init__(self, filename=None):
        self.uri = None
        self.engine = None
        self.session = None
        self.query = None
        self.add = None
        self.delete = None
        self.rollback = None
        self.flush = None
        self.creche = None
        if filename:
            self.init(filename)

    def init(self, filename=None):
        self.creche = None
        if filename:
            self.uri = "sqlite:///%s" % filename
        self.engine = create_engine(self.uri, echo=False)
        self.session = sessionmaker(bind=self.engine)()
        self.query = self.session.query
        self.add = self.session.add
        self.delete = self.session.delete
        self.rollback = self.session.rollback
        self.flush = self.session.flush

    def close(self):
        self.session.close()

    def commit(self):
        if self.session:
            release_query = self.query(DBSettings).filter_by(key=KEY_RELEASE)
            if release_query.count() == 0:
                self.session.add(DBSettings(key=KEY_RELEASE, value=VERSION))
            else:
                release_entry = release_query.one()
                release = release_entry.value
                if release != VERSION:
                    release_entry.value = VERSION
            self.session.commit()

    def load(self):
        if self.exists():
            self.translate()
        else:
            self.create()
        self.reload()

    def remove_incompatible_saas_options(self):
        self.creche.tri_planning &= ~TRI_GROUPE
        self.creche.smtp_server = ""

    def reload(self):
        print("Chargement de la base de données %s..." % self.uri)
        self.sanitize()
        self.creche = self.query(Creche).first()

    def sanitize(self):
        self.query(TimeslotInscrit).filter_by(activity=None).delete()
        self.query(TimeslotInscription).filter_by(activity=None).delete()

    def exists(self):
        return database_exists(self.uri) and self.engine.dialect.has_table(self.engine.connect(), DBSettings.__tablename__)

    def get_inscrit(self, inscrit_id):
        inscrit_id = int(inscrit_id)
        for inscrit in self.inscrits:
            if inscrit.id == inscrit_id:
                return inscrit
        else:
            return None

    def translate(self):
        version_entry = self.query(DBSettings).filter_by(key=KEY_VERSION).one()
        version = int(version_entry.value)
        if version > DB_VERSION:
            raise Exception("Version de base de données plus récente que votre version du logiciel.")
        elif version < DB_VERSION:
            print("Database translation from version %d to version %d..." % (version, DB_VERSION))

            if version < 65:
                raise NotImplementedError("Database conversions < 65 are not anymore supported")

            if version < 66:
                self.engine.execute("""
                  CREATE TABLE ref_journees_salaries(
                    idx INTEGER PRIMARY KEY,
                    reference INTEGER REFERENCES contrats(idx),
                    day INTEGER,
                    value INTEGER,
                    debut INTEGER,
                    fin INTEGER
                  )""")

                self.engine.execute("""
                  CREATE TABLE conges_salaries(
                    idx INTEGER PRIMARY KEY,
                    salarie INTEGER REFERENCES employes(idx),
                    debut VARCHAR,
                    fin VARCHAR,
                    label VARCHAR
                  )""")

                self.engine.execute("""
                  CREATE TABLE activites_salaries(
                    idx INTEGER PRIMARY KEY,
                    salarie INTEGER REFERENCES employes(idx),
                    date DATE,
                    value INTEGER,
                    debut INTEGER,
                    fin INTEGER
                  )""")

            if version < 67:
                self.engine.execute("ALTER TABLE contrats ADD duree_reference INTEGER")
                self.engine.execute("UPDATE contrats SET duree_reference=?", (7,))
                self.engine.execute("DELETE FROM ref_journees_salaries where day>6")

            if version < 68:
                capacite, ouverture, fermeture, debut_pause, fin_pause = self.engine.execute(
                    "SELECT capacite, ouverture, fermeture, debut_pause, fin_pause FROM creche").first()
                self.engine.execute("""
                  CREATE TABLE capacite(
                    idx INTEGER PRIMARY KEY,
                    value INTEGER,
                    debut INTEGER,
                    fin INTEGER
                  )""")
                if ouverture < debut_pause < fin_pause < fermeture:
                    start, end = int(ouverture * 12), int(debut_pause * 12)
                    self.engine.execute("INSERT INTO capacite (idx, value, debut, fin) VALUES (NULL,?,?,?)",
                                           (capacite, start, end))
                    start, end = int(fin_pause * 12), int(fermeture * 12)
                    self.engine.execute("INSERT INTO capacite (idx, value, debut, fin) VALUES (NULL,?,?,?)",
                                           (capacite, start, end))
                else:
                    start, end = int(ouverture * 12), int(fermeture * 12)
                    self.engine.execute("INSERT INTO capacite (idx, value, debut, fin) VALUES (NULL,?,?,?)",
                                           (capacite, start, end))

            if version < 69:
                self.engine.execute("""  
                  CREATE TABLE reservataires (
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
                  )""")
                self.engine.execute(
                    "ALTER TABLE inscriptions ADD reservataire INTEGER REFERENCES reservataires(idx)")

            if version < 70:
                self.engine.execute("ALTER TABLE creche ADD arrondi_heures_salaries INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_heures_salaries=?", (0,))
                self.engine.execute("ALTER TABLE creche ADD periode_revenus INTEGER")
                self.engine.execute("UPDATE creche SET periode_revenus=?", (0,))

            if version < 71:
                arrondi_heures = self.engine.execute("SELECT arrondi_heures FROM creche").first()[0]
                self.engine.execute("ALTER TABLE creche ADD arrondi_facturation INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_facturation=?", (arrondi_heures,))

            if version < 72:
                self.engine.execute("ALTER TABLE tarifsspeciaux ADD type INTEGER")
                self.engine.execute("ALTER TABLE tarifsspeciaux ADD unite INTEGER")
                self.engine.execute("UPDATE tarifsspeciaux SET type=?", (0,))
                self.engine.execute("UPDATE tarifsspeciaux SET unite=?", (0,))
                self.engine.execute("UPDATE tarifsspeciaux SET type=? WHERE reduction=?", (1, True))
                self.engine.execute("UPDATE tarifsspeciaux SET unite=? WHERE pourcentage=?", (1, True))

            if version < 73:
                self.engine.execute("ALTER TABLE inscrits ADD combinaison VARCHAR")
                self.engine.execute("UPDATE inscrits SET combinaison=?", ("",))

            if version < 74:
                self.engine.execute("ALTER TABLE bureaux ADD gerant VARCHAR")
                self.engine.execute("ALTER TABLE bureaux ADD directeur_adjoint VARCHAR")
                self.engine.execute("ALTER TABLE bureaux ADD comptable VARCHAR")
                self.engine.execute("ALTER TABLE activities ADD owner INTEGER")
                self.engine.execute("UPDATE activities SET owner=0")
                self.engine.execute("ALTER TABLE creche ADD age_maximum INTEGER")
                self.engine.execute("UPDATE creche SET age_maximum=3")

            if version < 75:
                self.engine.execute("""
                  CREATE TABLE categories (
                    idx INTEGER PRIMARY KEY,
                    nom VARCHAR
                  )""")
                self.engine.execute("ALTER TABLE inscrits ADD categorie INTEGER REFERENCES categories(idx)")

            if version < 76:
                self.engine.execute("ALTER TABLE creche ADD alerte_depassement_planning BOOLEAN")
                self.engine.execute("UPDATE creche SET alerte_depassement_planning=?", (False,))

            if version < 77:
                self.engine.execute("ALTER TABLE creche ADD gestion_maladie_sans_justificatif BOOLEAN")
                self.engine.execute("ALTER TABLE creche ADD gestion_preavis_conges BOOLEAN")
                self.engine.execute("UPDATE creche SET gestion_maladie_sans_justificatif=?", (False,))
                self.engine.execute("UPDATE creche SET gestion_preavis_conges=?", (False,))

            if version < 78:
                debut_pause, fin_pause = self.engine.execute("SELECT debut_pause, fin_pause FROM creche").first()
                self.engine.execute("""
                  CREATE TABLE plageshoraires (
                    idx INTEGER PRIMARY KEY,
                    debut FLOAT,
                    fin FLOAT,
                    flags INTEGER
                  )""")
                if debut_pause != 0 and fin_pause != 0:
                    self.engine.execute("INSERT INTO plageshoraires (idx, debut, fin, flags) VALUES (NULL,?,?,?)",
                                           (debut_pause, fin_pause, 0))

            if version < 79:
                self.engine.execute("ALTER TABLE creche ADD last_tablette_synchro VARCHAR")
                self.engine.execute("UPDATE creche SET last_tablette_synchro=''")

            if version < 80:
                self.engine.execute("ALTER TABLE revenus ADD conge_parental BOOLEAN")
                self.engine.execute("UPDATE revenus SET conge_parental=?", (False,))

            if version < 81:
                self.engine.execute("ALTER TABLE creche ADD repartition INTEGER")
                self.engine.execute("UPDATE creche SET repartition=0")

            if version < 82:
                self.engine.execute("""
                  CREATE TABLE NUMEROS_FACTURE (
                    idx INTEGER PRIMARY KEY,
                    date DATE,
                    valeur INTEGER
                  )""")

            if version < 83:
                result = list(self.engine.execute("SELECT value, debut, fin, idx FROM capacite"))
                self.engine.execute("DELETE FROM capacite")
                self.engine.execute("ALTER TABLE capacite ADD jour INTEGER")
                for value, debut, fin, idx in result:
                    for jour in range(7):
                        self.engine.execute(
                            "INSERT INTO capacite (idx, value, debut, fin, jour) VALUES (NULL,?,?,?,?)",
                            (value, debut, fin, jour))
                self.engine.execute("ALTER TABLE inscrits ADD medecin_traitant VARCHAR")
                self.engine.execute("UPDATE inscrits SET medecin_traitant=?", ("",))
                self.engine.execute("ALTER TABLE inscrits ADD telephone_medecin_traitant VARCHAR")
                self.engine.execute("UPDATE inscrits SET telephone_medecin_traitant=?", ("",))
                self.engine.execute("ALTER TABLE inscrits ADD assureur VARCHAR")
                self.engine.execute("UPDATE inscrits SET assureur=?", ("",))
                self.engine.execute("ALTER TABLE inscrits ADD numero_police_assurance VARCHAR")
                self.engine.execute("UPDATE inscrits SET numero_police_assurance=?", ("",))

            if version < 84:
                self.engine.execute("ALTER TABLE creche ADD seuil_alerte_inscription INTEGER")
                self.engine.execute("UPDATE creche SET seuil_alerte_inscription=?", (3,))

            if version < 85:
                self.engine.execute("ALTER TABLE creche ADD changement_groupe_auto BOOLEAN")
                self.engine.execute("UPDATE creche SET changement_groupe_auto=?", (False,))
                self.engine.execute("ALTER TABLE groupes ADD age_maximum INTEGER")
                self.engine.execute("UPDATE groupes SET age_maximum=?", (0,))
                self.engine.execute("ALTER TABLE creche ADD allergies VARCHAR")
                self.engine.execute("UPDATE creche SET allergies=?", ("",))
                self.engine.execute("ALTER TABLE inscrits ADD allergies VARCHAR")
                self.engine.execute("UPDATE inscrits SET allergies=?", ("",))

            if version < 86:
                self.engine.execute("ALTER TABLE inscriptions ADD allocation_mensuelle_caf FLOAT")
                self.engine.execute("UPDATE inscriptions SET allocation_mensuelle_caf=?", (.0,))

            if version < 87:
                self.engine.execute("ALTER TABLE creche ADD regularisation_fin_contrat BOOLEAN")
                self.engine.execute("UPDATE creche SET regularisation_fin_contrat=?", (True,))

            if version < 88:
                # TODO notes_parents marche ?
                self.engine.execute("""
                  CREATE TABLE familles(
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
                  )""")
                self.engine.execute("ALTER TABLE inscrits ADD famille INTEGER REFERENCES familles(idx)")
                self.engine.execute("ALTER TABLE parents ADD famille INTEGER REFERENCES familles(idx)")
                self.engine.execute("ALTER TABLE fratries ADD famille INTEGER REFERENCES familles(idx)")
                self.engine.execute("ALTER TABLE referents ADD famille INTEGER REFERENCES familles(idx)")
                result = list(self.engine.execute(
                    "SELECT idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes_parents FROM inscrits"))
                for idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes in result:
                    row = self.engine.execute(
                        "INSERT INTO familles (idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?)",
                        (adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, medecin_traitant,
                         telephone_medecin_traitant, assureur, numero_police_assurance, tarifs, notes))
                    self.engine.execute("UPDATE inscrits SET famille=? WHERE idx=?", (row.lastrowid, idx))
                    self.engine.execute("UPDATE parents SET famille=? WHERE inscrit=?", (row.lastrowid, idx))
                    self.engine.execute("UPDATE fratries SET famille=? WHERE inscrit=?", (row.lastrowid, idx))
                    self.engine.execute("UPDATE referents SET famille=? WHERE inscrit=?", (row.lastrowid, idx))

            if version < 89:
                self.engine.execute("ALTER TABLE employes ADD combinaison VARCHAR")
                self.engine.execute("UPDATE employes SET combinaison=''")

            if version < 90:
                self.engine.execute("ALTER TABLE familles ADD code_client VARCHAR")
                self.engine.execute("UPDATE familles SET code_client=''")
                self.engine.execute("ALTER TABLE creche ADD tri_factures INTEGER")
                self.engine.execute("UPDATE creche SET tri_factures=1")

            if version < 91:
                self.engine.execute("""
                  CREATE TABLE encaissements (
                    idx INTEGER PRIMARY KEY,
                    famille INTEGER REFERENCES familles(idx),
                    date DATE,
                    valeur FLOAT,
                    moyen_paiement INTEGER
                  )""")

            if version < 92:
                self.engine.execute("ALTER TABLE sites ADD groupe INTEGER")
                self.engine.execute("UPDATE sites SET groupe=0")

            if version < 93:
                self.engine.execute("ALTER TABLE creche ADD arrondi_mensualisation_euros INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_mensualisation_euros=0")
                self.engine.execute("ALTER TABLE creche ADD arrondi_semaines INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_semaines=1")

            if version < 94:
                self.engine.execute("ALTER TABLE inscriptions ADD forfait_mensuel_heures FLOAT")
                result = list(self.engine.execute("SELECT idx, forfait_heures_presence FROM inscriptions"))
                for idx, forfait_heures_presence in result:
                    self.engine.execute("UPDATE inscriptions SET forfait_mensuel_heures=? WHERE idx=?",
                                           (forfait_heures_presence, idx))

            if version < 95:
                self.engine.execute("ALTER TABLE creche ADD tri_inscriptions INTEGER")
                self.engine.execute("UPDATE creche SET tri_inscriptions=1")

            if version < 96:
                self.engine.execute("ALTER TABLE creche ADD mode_saisie_planning INTEGER")
                self.engine.execute("UPDATE creche SET mode_saisie_planning=0")
                self.engine.execute("""
                  CREATE TABLE PLANNING_HEBDOMADAIRE(
                    idx INTEGER PRIMARY KEY,
                    inscrit INTEGER REFERENCES inscrits(idx),
                    date DATE,
                    activity INTEGER,
                    value FLOAT
                  )""")
                self.engine.execute("ALTER TABLE activities ADD formule_tarif VARCHAR")
                result = list(self.engine.execute('SELECT idx, tarif FROM activities'))
                for idx, tarif in result:
                    self.engine.execute("UPDATE activities SET formule_tarif=? WHERE idx=?", (str(tarif), idx))
                self.engine.execute("ALTER TABLE inscriptions ADD heures_permanences FLOAT")
                self.engine.execute("UPDATE inscriptions SET heures_permanences=?", (0,))
                self.engine.execute("ALTER TABLE creche ADD date_raz_permanences")
                self.engine.execute("UPDATE creche SET date_raz_permanences=?", (None,))

            if version < 97:
                self.engine.execute("ALTER TABLE creche ADD conges_payes_salaries INTEGER")
                self.engine.execute("UPDATE creche SET conges_payes_salaries=?", (25,))
                self.engine.execute("ALTER TABLE creche ADD conges_supplementaires_salaries INTEGER")
                self.engine.execute("UPDATE creche SET conges_supplementaires_salaries=?", (0,))
                self.engine.execute("""
                    CREATE TABLE commentaires_salaries(
                      idx INTEGER PRIMARY KEY,
                      salarie INTEGER REFERENCES salaries(idx),
                      date DATE,
                      commentaire VARCHAR
                    )""")
                self.engine.execute("ALTER TABLE creche ADD cout_journalier FLOAT")
                self.engine.execute("UPDATE creche SET cout_journalier=?", (.0,))

            if version < 98:
                arrondi_facturation = self.engine.execute("SELECT arrondi_facturation FROM creche").first()[0]
                self.engine.execute("ALTER TABLE creche ADD arrondi_facturation_periode_adaptation INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_facturation_periode_adaptation=?", (arrondi_facturation,))

            if version < 99:
                self.engine.execute("ALTER TABLE creche ADD arrondi_mensualisation INTEGER")
                self.engine.execute("UPDATE creche SET arrondi_mensualisation=5")

            if version < 100:
                self.engine.execute("ALTER TABLE parents ADD adresse VARCHAR")
                self.engine.execute("ALTER TABLE parents ADD code_postal INTEGER")
                self.engine.execute("ALTER TABLE parents ADD ville VARCHAR")
                result = list(self.engine.execute("SELECT adresse, code_postal, ville, idx FROM familles"))
                for adresse, code_postal, ville, famille in result:
                    self.engine.execute("UPDATE parents SET adresse=?, code_postal=?, ville=? WHERE famille=?",
                                           (adresse, code_postal, ville, famille))

            if version < 101:
                result = list(self.engine.execute("SELECT login, password, idx FROM users"))
                for login, password, idx in result:
                    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    self.engine.execute("UPDATE users SET password=? WHERE idx=?", (hashed, idx))

            if version < 102:
                result = list(self.engine.execute("SELECT profile, idx FROM users"))
                for old_profile, idx in result:
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
                    self.engine.execute("UPDATE users SET profile=? WHERE idx=?", (profile, idx))

            if version < 103:
                self.engine.execute("ALTER TABLE creche ADD cloture_facturation INTEGER")
                cloture_facturation = self.engine.execute("SELECT cloture_factures FROM creche").first()[0]
                self.engine.execute("UPDATE creche SET cloture_facturation=?", (2 if cloture_facturation else 0,))

            if version < 104:
                self.engine.execute("ALTER TABLE creche ADD iban VARCHAR")
                self.engine.execute("ALTER TABLE creche ADD bic VARCHAR")
                self.engine.execute("ALTER TABLE familles ADD iban VARCHAR")
                self.engine.execute("ALTER TABLE familles ADD bic VARCHAR")
                self.engine.execute("ALTER TABLE familles ADD jour_prelevement_automatique INTEGER")
                self.engine.execute("ALTER TABLE familles ADD date_premier_prelevement_automatique DATE")

            if version < 105:
                self.engine.execute("ALTER TABLE reservataires ADD periode_facturation INTEGER")
                self.engine.execute("ALTER TABLE reservataires ADD delai_paiement INTEGER")
                self.engine.execute("ALTER TABLE reservataires ADD tarif FLOAT")
                self.engine.execute("ALTER TABLE inscriptions ADD newsletters INTEGER")
                self.engine.execute("UPDATE reservataires SET periode_facturation=1, delai_paiement=30")
                self.engine.execute("UPDATE inscriptions SET newsletters=0")

            if version < 106:
                self.engine.execute("ALTER TABLE creche ADD masque_alertes INTEGER")
                gestion_alertes = self.engine.execute("SELECT gestion_alertes FROM creche").first()[0]
                self.engine.execute("UPDATE creche SET masque_alertes=?", (7 if gestion_alertes else 0,))

            if version < 107:
                self.engine.execute("ALTER TABLE creche ADD creditor_id VARCHAR")
                self.engine.execute("ALTER TABLE familles ADD mandate_id VARCHAR")

            if version < 108:
                formule_taux_horaire = self.engine.execute("SELECT formule_taux_horaire FROM creche").first()[0]
                self.engine.execute("""
                  CREATE TABLE tarifs_horaires(
                    idx INTEGER PRIMARY KEY,
                    debut DATE,
                    fin DATE,
                    formule VARCHAR
                  )""")
                self.engine.execute("INSERT INTO tarifs_horaires (idx, debut, fin, formule) VALUES (NULL, ?, ?, ?)", (None, None, formule_taux_horaire))

            if version < 109:
                self.engine.execute("ALTER TABLE parents ADD profession VARCHAR")
                self.engine.execute("UPDATE parents SET profession=''")

            if version < 110:
                self.engine.execute("""
                  CREATE TABLE encaissements_reservataires (
                    idx INTEGER PRIMARY KEY,
                    reservataire INTEGER REFERENCES RESERVATAIRE(idx),
                    date DATE,
                    valeur FLOAT,
                    moyen_paiement INTEGER
                  )""")

            if version < 111:
                self.engine.execute("ALTER TABLE tarifsspeciaux ADD portee INTEGER")
                self.engine.execute("UPDATE tarifsspeciaux SET portee=0")
                self.engine.execute("ALTER TABLE inscriptions ADD tarifs INTEGER")
                self.engine.execute("UPDATE inscriptions SET tarifs=0")

            if version < 112:
                self.engine.execute("ALTER TABLE creche ADD siret VARCHAR")
                self.engine.execute("UPDATE creche SET siret=''")

            if version < 113:
                self.engine.execute("ALTER TABLE creche ADD regularisation_conges_non_pris BOOLEAN")
                self.engine.execute("UPDATE creche SET regularisation_conges_non_pris=regularisation_fin_contrat")

            if version < 114:
                self.engine.execute("ALTER TABLE inscrits ADD garde_alternee BOOLEAN")
                self.engine.execute("UPDATE inscrits SET garde_alternee=?", (False,))

            if version < 115:
                idx = self.engine.execute('SELECT idx FROM CRECHE').first()[0]
                for table in ("alertes", "bureaux", "charges", "professeurs", "capacite", "numeros_facture", "plageshoraires", "activities", "familles", "users", "inscrits", "employes", "categories", "groupes", "sites", "reservataires", "tarifsspeciaux", "tarifs_horaires", "conges", "baremescaf"):
                    self.engine.execute("ALTER TABLE %s ADD creche_id INGEGER REFERENCES creche(idx)" % table)
                    self.engine.execute("UPDATE %s SET creche_id=?" % table, (idx,))

                self.engine.execute("ALTER TABLE revenus ADD parent_id INGEGER REFERENCES PARENT(idx);")
                self.engine.execute("UPDATE revenus SET parent_id=parent")

                self.engine.execute("ALTER TABLE parents ADD sexe INTEGER")
                self.engine.execute("UPDATE parents SET sexe=1 WHERE relation='papa'")
                self.engine.execute("UPDATE parents SET sexe=2 WHERE relation='maman'")

                for column in ("inscrit", "reservataire", "groupe", "site", "professeur"):
                    self.engine.execute("ALTER TABLE inscriptions ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                    self.engine.execute("UPDATE inscriptions SET %s_id=%s" % (column, column))

                self.engine.execute("ALTER TABLE contrats ADD site_id INTEGER REFERENCES site(idx)")
                self.engine.execute("UPDATE contrats SET site_id=site")

                self.engine.execute("ALTER TABLE ref_activities ADD inscription_id INTEGER REFERENCES inscriptions(idx)")
                self.engine.execute("UPDATE ref_activities SET inscription_id=reference")

                for column in ("famille", "categorie"):
                    self.engine.execute("ALTER TABLE inscrits ADD %s_id INTEGER REFERENCES %s(idx)" % (column, column))
                    self.engine.execute("UPDATE inscrits SET %s_id=%s" % (column, column))

                for table in ("fratries", "parents", "referents"):
                    self.engine.execute("ALTER TABLE %s ADD famille_id INTEGER REFERENCES familles(idx)" % table)
                    self.engine.execute("UPDATE %s SET famille_id=famille" % table)

                for table in ("conges_inscrits", "activites", "planning_hebdomadaire", "commentaires", "factures", "corrections"):
                    self.engine.execute("ALTER TABLE %s ADD inscrit_id INGEGER REFERENCES inscrits(idx)" % table)
                    self.engine.execute("UPDATE %s SET inscrit_id=inscrit" % table)

                self.engine.execute("ALTER TABLE contrats ADD salarie_id INGEGER REFERENCES employes(idx)")
                self.engine.execute("UPDATE contrats SET salarie_id=employe")

                for table in ("conges_salaries", "activites_salaries", "commentaires_salaries"):
                    self.engine.execute("ALTER TABLE %s ADD salarie_id INGEGER REFERENCES employes(idx)" % table)
                    self.engine.execute("UPDATE %s SET salarie_id=salarie" % table)

                self.engine.execute("""
                    CREATE TABLE contrats_salaries(
                        idx INTEGER PRIMARY KEY,
                        salarie_id INTEGER REFERENCES employes(idx),
                        debut DATE,
                        fin DATE,
                        site_id INTEGER REFERENCES sites(idx),
                        fonction VARCHAR
                      )""")
                self.engine.execute("ALTER TABLE contrats ADD contrat_id INGEGER REFERENCES contrats_salaries(idx)")
                rows = list(self.engine.execute("SELECT idx, salarie_id, debut, fin, site_id, fonction FROM contrats"))
                for planning_id, salarie_id, debut, fin, site_id, fonction in rows:
                    result = self.engine.execute("INSERT INTO contrats_salaries (idx, salarie_id, debut, fin, site_id, fonction) VALUES(NULL,?,?,?,?,?)", (salarie_id, debut, fin, site_id, fonction))
                    self.engine.execute("UPDATE contrats set contrat_id=? WHERE idx=?", (result.lastrowid, planning_id))

                self.engine.execute("ALTER TABLE creche ADD gestion_plannings_salaries INTEGER")
                self.engine.execute("UPDATE creche SET gestion_plannings_salaries=0")

                values = (1 << 28), (1 << 30), (1 << 28) | (1 << 30)
                self.engine.execute("UPDATE ref_activities SET value=0 WHERE value=? OR value=? OR value=?", values)
                self.engine.execute("UPDATE activites SET value=0 WHERE value=? OR value=? OR value=?", values)
                self.engine.execute("UPDATE ref_journees_salaries SET value=0 WHERE value=? OR value=? OR value=?", values)
                self.engine.execute("UPDATE activites_salaries SET value=0 WHERE value=? OR value=? OR value=?", values)

                rows = list(self.engine.execute("SELECT idx, debut FROM conges"))
                trash = []
                for i, row1 in enumerate(rows):
                    for j, row2 in enumerate(rows[i+1:]):
                        if row1.debut == row2.debut and row1.debut in [jour[0] for jour in jours_fermeture]:
                            trash.append(row2)
                for idx, _ in trash:
                    self.engine.execute("DELETE FROM conges WHERE idx=?", idx)

                rows = list(self.engine.execute("SELECT debut, fin, idx FROM reservataires"))
                for debut, fin, idx in rows:
                    if isinstance(debut, str):
                        self.engine.execute("UPDATE reservataires SET debut=? WHERE idx=?", (str2date(debut), idx))
                    if isinstance(fin, str):
                        self.engine.execute("UPDATE reservataires SET fin=? WHERE idx=?", (str2date(fin), idx))

            if version < 116:
                creche_id = self.engine.execute('SELECT idx FROM CRECHE').first()[0]
                self.engine.execute("""
                    CREATE TABLE food_needs (
                        idx INTEGER PRIMARY KEY,
                        creche_id INTEGER REFERENCES creche(idx),
                        label VARCHAR,
                        tranche_4_6 INTEGER,
                        tranche_6_12 INTEGER,
                        tranche_12_18 INTEGER,
                        tranche_18_24 INTEGER,
                        tranche_24_ INTEGER
                    )""")
                for label in ("Protéines", "Féculents", "Légumes"):
                    self.engine.execute("INSERT INTO food_needs(idx, creche_id, label, tranche_4_6, tranche_6_12, tranche_12_18, tranche_18_24, tranche_24_) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, label, 0, 0, 0, 0, 0)
                self.engine.execute("ALTER TABLE inscrits ADD type_repas INGEGER")
                self.engine.execute("UPDATE inscrits SET type_repas=0")

            if version < 117:
                self.engine.execute("ALTER TABLE creche ADD delai_paiement_familles INGEGER")

            if version < 118:
                self.engine.execute("ALTER TABLE familles ADD autorisation_attestation_paje BOOLEAN")
                self.engine.execute("UPDATE familles SET autorisation_attestation_paje=?", True)

            if version < 119:
                self.engine.execute("ALTER TABLE employes ADD notes VARCHAR")

            if version < 120:
                self.engine.execute("ALTER TABLE inscrits ADD type_repas2 INGEGER")
                self.engine.execute("UPDATE inscrits SET type_repas2=0")

            if version < 121:
                rows = list(self.engine.execute("SELECT formule, idx FROM tarifs_horaires"))
                for row in rows:
                    formule, idx = row
                    formule = eval(formule)
                    if formule:
                        for i, cas in enumerate(formule):
                            formule[i] = (cas[0], cas[1], 0)
                    self.engine.execute("UPDATE tarifs_horaires SET formule=? WHERE idx=?", (str(formule), idx))

            if version < 122:
                self.engine.execute("ALTER TABLE conges_salaries ADD type INGEGER")
                self.engine.execute("UPDATE conges_salaries SET type=0")
                self.engine.execute("ALTER TABLE creche ADD gestion_conges_sans_solde BOOLEAN")
                self.engine.execute("UPDATE creche SET gestion_conges_sans_solde=?", False)
                self.engine.execute("""
                    CREATE TABLE heures_supp (
                        idx INTEGER PRIMARY KEY,
                        salarie_id INTEGER REFERENCES employes(idx),
                        date DATE,
                        label VARCHAR,
                        value FLOAT
                    )""")
                self.engine.execute("""
                    CREATE TABLE credit_conges (
                        idx INTEGER PRIMARY KEY,
                        salarie_id INTEGER REFERENCES employes(idx),
                        date DATE,
                        label VARCHAR,
                        value FLOAT
                    )""")

            if version < 123:
                creche_id = self.engine.execute('SELECT idx FROM CRECHE').first()[0]
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Maladie avec hospitalisation", -3, -3, "[190, 35, 29, 150, 100]", "[190, 35, 29, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Absence non prévenue", -4, -4, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Maladie sans justificatif", -5, -5, "[190, 35, 29, 150, 100]", "[190, 35, 29, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Congés sans préavis", -6, -6, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Absence non déductible (dépassement)", -7, -7, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Congés payés", -8, -8, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Congés sans solde", -9, -9, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Congés maternité", -10, -10, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Récupération heures supp.", -11, -11, "[0, 0, 255, 150, 100]", "[0, 0, 255, 150, 100]", "")
                self.engine.execute("INSERT INTO activities(idx, creche_id, label, value, mode, couleur, couleur_supplement, formule_tarif) VALUES(NULL,?,?,?,?,?,?,?)", creche_id, "Présence salariés", -256, -256, "[5, 203, 28, 150, 100]", "[5, 203, 28, 250, 100]", "")
                self.engine.execute("UPDATE activities SET mode=value WHERE value<0")
                self.engine.execute("UPDATE activities SET mode=10 WHERE mode=2")
                self.engine.execute("UPDATE activities SET mode=2 WHERE mode=1")
                self.engine.execute("UPDATE activities SET mode=1 WHERE mode=0 AND value>0")
                activities = [row for row in self.engine.execute("SELECT value, idx FROM activities")]
                for table in ("ref_activities", "ref_journees_salaries", "activites", "activites_salaries"):
                    try:
                        self.engine.execute("ALTER TABLE %s ADD activity INGEGER REFERENCES activities(idx)" % table)
                    except:
                        pass
                    for value, activity in activities:
                        self.engine.execute("UPDATE %s SET activity=? WHERE value=?" % table, (activity, value))
                    self.engine.execute("DELETE FROM %s WHERE activity IS NULL" % table)

            if version < 124:
                for column in "date_premier_contact", "date_entretien_directrice", "date_envoi_devis", "date_reponse_parents":
                    self.engine.execute("ALTER TABLE inscrits ADD %s DATE" % column)
                self.engine.execute("ALTER TABLE inscrits ADD preinscription_state INTEGER")
                self.engine.execute("ALTER TABLE inscriptions ADD debut_asap BOOLEAN")

            if version < 125:
                self.engine.execute("ALTER TABLE sites ADD societe STRING")
                self.engine.execute("ALTER TABLE sites ADD email STRING")
                self.engine.execute("ALTER TABLE activities ADD flags INTEGER")
                self.engine.execute("ALTER TABLE users ADD email STRING")
                self.engine.execute("ALTER TABLE users ADD flags INTEGER")

            if version < 126:
                self.engine.execute("ALTER TABLE creche ADD societe STRING")
                self.engine.execute("ALTER TABLE sites ADD siret STRING")

            if version < 127:
                self.engine.execute("UPDATE inscrits SET preinscription_state=preinscription_state+1 WHERE preinscription_state>=2")

            if version < 128:
                self.engine.execute("ALTER TABLE creche ADD prorata INTEGER")
                self.engine.execute("UPDATE creche SET prorata=1")
                self.engine.execute("UPDATE creche SET prorata=0 WHERE repartition==2")
                self.engine.execute("UPDATE creche SET repartition=3 WHERE repartition==2")

            if version < 129:
                self.engine.execute("ALTER TABLE encaissements ADD label STRING")
                self.engine.execute("ALTER TABLE encaissements_reservataires ADD label STRING")

            if version < 130:
                self.engine.execute("ALTER TABLE creche ADD email_changements_planning STRING")

            # update database version
            version_entry.value = DB_VERSION
            self.commit()

    def create(self, populate=True):
        print("Database creation...")
        Base.metadata.create_all(self.engine)
        self.add(DBSettings(key=KEY_VERSION, value=DB_VERSION))
        creche = Creche(allergies="")
        self.add(creche)
        if populate:
            for label in ("Week-end", "1er janvier", "1er mai", "8 mai", "14 juillet", "15 août", "1er novembre", "11 novembre", "25 décembre", "Lundi de Pâques", "Jeudi de l'Ascension"):
                creche.add_ferie(CongeStructure(creche=creche, debut=label))
            for debut, fin, plancher, plafond in [
                (datetime.date(2006, 9, 1), datetime.date(2007, 8, 31), 6547.92, 51723.60),
                (datetime.date(2007, 9, 1), datetime.date(2008, 12, 31), 6660.00, 52608.00),
                (datetime.date(2009, 1, 1), datetime.date(2009, 12, 31), 6876.00, 53400.00),
                (datetime.date(2010, 1, 1), datetime.date(2010, 12, 31), 6956.64, 54895.20),
                (datetime.date(2011, 1, 1), datetime.date(2011, 12, 31), 7060.92, 85740.00),
                (datetime.date(2012, 1, 1), datetime.date(2012, 12, 31), 7181.04, 85740.00),
                (datetime.date(2013, 1, 1), datetime.date(2013, 12, 31), 7306.56, 85740.00),
            ]:
                creche.baremes_caf.append(BaremeCAF(creche=creche, debut=debut, fin=fin, plancher=plancher, plafond=plafond))
        for mode in 0, PRESENCE_SALARIE:
            creche.add_activite(Activite(creche=creche, label=STATE_LABELS[mode], mode=mode, _couleur="[5, 203, 28, 150, 100]", _couleur_supplement="[5, 203, 28, 250, 100]", formule_tarif=""))
        for mode in MALADE, HOPITAL, MALADE_SANS_JUSTIFICATIF:
            creche.add_activite(Activite(creche=creche, label=STATE_LABELS[mode], mode=mode, _couleur="[190, 35, 29, 150, 100]", _couleur_supplement="[190, 35, 29, 150, 100]", formule_tarif=""))
        for mode in VACANCES, ABSENCE_NON_PREVENUE, ABSENCE_CONGE_SANS_PREAVIS, CONGES_DEPASSEMENT, CONGES_PAYES, CONGES_SANS_SOLDE, CONGES_MATERNITE, CONGES_RECUP_HEURES_SUPP:
            creche.add_activite(Activite(creche=creche, label=STATE_LABELS[mode], mode=mode, _couleur="[0, 0, 255, 150, 100]", _couleur_supplement="[0, 0, 255, 150, 100]", formule_tarif=""))
        self.commit()

    def delete_all_inscriptions(self):
        for item in self.creche.familles + self.creche.inscrits + self.creche.salaries + self.creche.professeurs + \
                    self.creche.alertes.values() + self.creche.numeros_facture.values() + self.creche.charges.values():
            self.delete(item)
        self.commit()

    def dump(self):
        print("Inscrits :")
        for inscrit in self.creche.inscrits:
            print(" ", inscrit.prenom, inscrit.nom)
            for parent in inscrit.famille.parents:
                print("   ", parent.prenom, parent.nom, parent.sexe)
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
        database.create()
        database.dump()
