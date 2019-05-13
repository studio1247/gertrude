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
import collections
from builtins import str
import time
import os.path
from database import Timeslot, TimeslotInscrit, Activite, Reservataire
from parameters import *
from globals import *
from config import config
from helpers import *


def GetCurrentMonday(date):
    return date - datetime.timedelta(date.weekday())


def GetNextMonday(date):
    return date + datetime.timedelta(7 - date.weekday())


def IsPresentDuringTranche(journee, debut, fin):
    for timeslot in journee.timeslots:
        if timeslot.activity.mode == MODE_PRESENCE and timeslot.debut < fin and timeslot.fin > debut:
            return True
    return False


def HeuresTranche(journee, debut, fin):
    result = [0] * (24 * 60 // BASE_GRANULARITY)
    for timeslot in journee.timeslots:
        if timeslot.debut < fin and timeslot.fin > debut:
            for i in range(max(timeslot.debut, debut), min(timeslot.fin, fin)):
                result[i] = 1
    return float(sum(result) * BASE_GRANULARITY) // 60


def GetJoursOuvres(annee, mois):
    jours_ouvres = 0
    date = datetime.date(annee, mois, 1)
    while date.month == mois:
        if not date in database.creche.jours_fermeture:
            jours_ouvres += 1
        date += datetime.timedelta(1)
    return jours_ouvres        


def GetHeuresAccueil(annee, mois, site=None):
    if site is not None:
        capacite = 0 if site.capacite is None else site.capacite
        return GetJoursOuvres(annee, mois) * (database.creche.fermeture - database.creche.ouverture) * capacite
    result = 0.0
    date = datetime.date(annee, mois, 1)
    while date.month == mois:
        if not date in database.creche.jours_fermeture:
            result += database.creche.GetHeuresAccueil(date.weekday())
        date += datetime.timedelta(1)
    return result        


def GetInitialesPrenom(person):
    if person.prenom:
        for char in ('-', ' '):
            if char in person.prenom:
                parts = person.prenom.split(char)
                return ''.join([part[0] for part in parts if len(part) > 0])
        return person.prenom[0]
    else:
        return '?'


def GetNom(person):
    if person:
        return person.nom
    else:
        return ""


def GetNom4P1(inscrit, inscrits):
    if inscrit:
        result = inscrit.nom[:4].upper()
        noms = [p.nom[:4].upper() for p in inscrits]
        if noms.count(result) > 1 and len(inscrit.prenom) > 0:
            for parent in inscrit.famille.parents:
                if parent and len(parent.prenom) > 0:
                    result += parent.prenom[0].upper()
        return result
    else:
        return ""


def GetPrenom(person):
    if person:
        return person.prenom
    else:
        return ""


def Civilite(who):
    return "Monsieur" if who.sexe == MASCULIN else "Madame"


def GetPrenomNom(person, maj_nom=False, tri=None, monsieur_madame=False):
    if not person:
        return ""
    nom = person.nom
    if isinstance(person, Reservataire):
        return nom
    if tri is None:
        tri = database.creche.tri_planning
    if maj_nom:
        nom = nom.upper()
    intro = (Civilite(person) + " ") if monsieur_madame else ""
    if (tri & 255) == TRI_NOM:
        return intro + "%s %s" % (nom, person.prenom)
    else:
        return intro + "%s %s" % (person.prenom, nom)


def GetInscritsFamille(famille):
    result = []
    for inscrit in database.creche.inscrits:
        if inscrit.famille is famille:
            result.append(inscrit)
    return result


def GetInscritsFrereSoeurs(inscrit):
    result = []
    for candidat in database.creche.inscrits:
        if candidat is not inscrit and candidat.famille == inscrit.famille:
            result.append(candidat)
    return result


def GetTranche(valeur, tranches):
    result = 0
    for tranche in tranches:
        if valeur < tranche:
            return result
        result += 1
    return result


def GetDepartement(cp):
    if cp:
        return int(cp/1000)
    else:
        return ""


def GetFile(filename, site, path, path_dist):
    paths = []
    if site and site.nom:
        paths.append("%s/[%s] %s" % (path, site.nom.replace('"', ''), filename))
    try:
        paths.append("%s/[%s] %s" % (path, database.creche.nom.replace('"', ''), filename))
        paths.append("%s/[%s] %s" % (path, database.creche.nom.lower().replace('"', ''), filename))
    except:
        pass
    paths.append("%s/%s" % (path, filename))
    paths.append("%s/%s" % (path_dist, filename))
    if sys.platform == "darwin":
        paths.append("../Resources/%s" % filename)
    for directory in ["", "~/.gertrude/", "/usr/share/gertrude/", os.path.dirname(os.path.realpath(__file__)) + "/"]:
        for path in paths:
            # print("Test path %s" % path)
            if os.path.isfile(directory + path):
                return directory + path
    return None


def GetBitmapFile(filename, site=None):
    return GetFile(filename, site, "bitmaps", "bitmaps_dist")


def GetTemplateFile(filename, site=None):
    return GetFile(filename, site, config.templates_directory, "templates_dist")


def IsCustomTemplateFile(filename):
    if os.path.isfile("%s/%s" % (config.templates_directory, filename)):
        return True
    elif os.path.isfile("%s/[%s] %s" % (config.templates_directory, database.creche.nom, filename)):
        return True
    else:
        return False


def IsTemplateFile(filename):
    if IsCustomTemplateFile(filename):
        return True
    elif os.path.isfile("templates_dist/%s" % filename):
        return True
    else:
        return False


def GetParentsString(famille, version_longue=False):
    parent1 = famille.parents[0] if len(famille.parents) > 0 else None
    parent2 = famille.parents[1] if len(famille.parents) > 1 else None
    if not parent1 and not parent2:
        return "Pas de parents"
    elif not parent2 or not GetPrenomNom(parent2):
        return GetPrenomNom(parent1, monsieur_madame=version_longue)
    elif not parent1 or not GetPrenomNom(parent1):
        return GetPrenomNom(parent2, monsieur_madame=version_longue)
    elif version_longue or parent1.nom != parent2.nom:
        return " et ".join([GetPrenomNom(parent1, monsieur_madame=version_longue), GetPrenomNom(parent2, monsieur_madame=version_longue)])
    elif parent2.prenom:
        return '%s et %s %s' % (parent2.prenom, parent1.prenom, parent1.nom)
    else:
        return '%s %s' % (parent1.prenom, parent1.nom)


def GetParentsPrenomsString(famille):
    parent1 = famille.parents[0] if len(famille.parents) > 0 else None
    parent2 = famille.parents[1] if len(famille.parents) > 1 else None
    if parent1:
        if parent2:
            return '%s/%s' % (parent1.prenom, parent2.prenom)
        else:
            return parent1.prenom
    elif parent2:
        return parent2.prenom
    else:
        return ""


def GetParentsNomsString(famille):
    parent1 = famille.parents[0] if len(famille.parents) > 0 else None
    parent2 = famille.parents[1] if len(famille.parents) > 1 else None
    if parent1:
        if parent2 and parent1.nom != parent2.nom:
            return '%s-%s' % (parent1.nom, parent2.nom)
        else:
            return parent1.nom
    elif parent2:
        return parent2.nom
    else:
        return ""


def GetParentsCivilitesString(famille):
    messieurs = []
    mesdames = []
    for parent in famille.parents:
        if parent is not None:
            if parent.sexe == MASCULIN:
                messieurs.append("M.")
            elif parent.sexe == FEMININ:
                mesdames.append("Mme")
    return "/".join(mesdames + messieurs)


def GetInscritsByMode(start, end, mode, site=None):  # TODO pourquoi retourner les index
    result = []
    for i, inscrit in enumerate(database.creche.inscrits):
        for inscription in inscrit.get_inscriptions(start, end):
            if inscription.mode & mode and (site is None or inscription.site == site):
                result.append(i)
                break
    return result


def GetSalaries(start, end, site=None):
    result = []
    for salarie in database.creche.salaries:
        for contrat in salarie.GetContrats(start, end):
            if site is None or contrat.site == site:
                result.append(salarie)
                break
    return result


def GetTriParCommuneEtNomIndexes(indexes):
    # Tri par commune (Rennes en premier) + ordre alphabetique des noms
    def sort_key(x):
        inscrit = database.creche.inscrits[x]
        key = "%s %s %s" % (inscrit.famille.ville, inscrit.nom, inscrit.prenom)
        return key.lower()
    return list(indexes).sort(key=sort_key)


def GetTriParPrenomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def sort_key(x):
        inscrit = database.creche.inscrits[x]
        return inscrit.prenom
    indexes.sort(key=sort_key)
    return indexes


def GetTriParNomIndexes(indexes):
    def sort_key(x):
        inscrit = database.creche.inscrits[x]
        return inscrit.nom
    indexes.sort(key=sort_key)
    return indexes


def GetEnfantsTries(enfants, sort_key):
    if enfants is None:
        enfants = database.creche.inscrits[:]
    else:
        enfants = enfants[:]
    enfants.sort(key=sort_key)
    return enfants


def GetEnfantsTriesParNom(enfants=None):
    def sort_key(x):
        return GetPrenomNom(x, tri=TRI_NOM)
    return GetEnfantsTries(enfants, sort_key)


def GetEnfantsTriesParPrenom(enfants=None):
    def sort_key(x):
        return GetPrenomNom(x)
    return GetEnfantsTries(enfants, sort_key)


def GetEnfantsTriesParNomParents(enfants=None):
    def sort_key(x):
        return GetParentsNomsString(x.famille)
    return GetEnfantsTries(enfants, sort_key)


def GetGroupesEnfants(lines):
    groupes = {}
    for line in lines:
        groupe = line.inscription.groupe
        if groupe not in groupes:
            groupes[groupe] = []
        groupes[groupe].append(line)

    keys = groupes.keys()

    def sort_key(x):
        return x.ordre if x else -1

    keys.sort(key=sort_key)

    result = []
    for key in keys:
        groupe = groupes[key]
        groupe.sort(key=lambda element: element.label)
        result.append({"groupe": key, "enfants": groupe})
    return result


def GetEnfantsTriesParGroupe(lines):
    result = []
    groupes = GetGroupesEnfants(lines)
    for groupe in groupes:
        result.extend(groupe["enfants"])
    return result


def GetEnfantsTriesSelonParametreTriPlanning(enfants):
    if database.creche.tri_planning & TRI_GROUPE:
        return GetEnfantsTriesParGroupe(enfants)
    elif database.creche.tri_planning == TRI_NOM:
        return GetEnfantsTriesParNom(enfants)
    else:
        return GetEnfantsTriesParPrenom(enfants)


def GetEnfantsTriesSelonParametreTriFacture(enfants):
    if database.creche.tri_factures == TRI_NOM:
        return GetEnfantsTriesParNom(enfants)
    elif database.creche.tri_factures == TRI_NOM_PARENTS:
        return GetEnfantsTriesParNomParents(enfants)
    elif database.creche.tri_factures == TRI_PRENOM:
        return GetEnfantsTriesParPrenom(enfants)
    else:
        return enfants


def GetPresentsIndexes(indexes, periode, site=None):
    debut, fin = periode
    if indexes is None:
        indexes = range(len(database.creche.inscrits))
    result = []
    if debut is None:
        return result
    for i in range(len(indexes)):
        inscrit = database.creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if (inscription.fin is None or inscription.fin >= debut) and \
                    (not database.creche.preinscriptions or not inscription.preinscription) and \
                    (site is None or inscription.site == site) and \
                    (inscription.debut is not None) and \
                    (not fin or inscription.debut <= fin):
                result.append(indexes[i])
                break
    return result


def GetLines(date, inscrits, presence=False, site=None, groupe=None, summary=SUMMARY_ENFANT):
    lines = []
    for inscrit in inscrits:
        contrat = inscrit.get_contrat(date)
        if contrat and (site is None or contrat.site == site) and (groupe is None or contrat.groupe == groupe):
            if presence:
                state = inscrit.get_state(date)
                if state < 0 or not state & PRESENT:
                    continue
            if date in inscrit.jours_conges or inscrit.get_state(date) < 0:
                continue
            line = inscrit.GetJournee(date)
            line.nom = inscrit.nom
            line.prenom = inscrit.prenom
            line.label = GetPrenomNom(inscrit)
            line.sublabel = ""
            line.inscription = contrat
            line.reference = inscrit.GetJourneeReference(date)
            line.summary = summary
            lines.append(line)
    return lines


def GetEnfantsTriesParReservataire(inscrits):
    reservataires = {}
    for inscrit in inscrits:
        if len(inscrit.inscriptions):
            reservataire = inscrit.inscriptions[0].reservataire
        else:
            reservataire = None
        if reservataire not in reservataires:
            reservataires[reservataire] = []
        reservataires[reservataire].append(inscrit)
        
    keys = reservataires.keys()
    
    def tri(one, two):
        if one is None:
            return -1
        elif two is None:
            return 1
        else:
            return cmp(one.nom, two.nom)
        
    keys.sort(tri)
    lines = []
    for key in keys:
        reservataires[key].sort(key=lambda inscrit: GetPrenomNom(inscrit))
        if key:
            reservataires[key].insert(0, key.nom)
        else:
            reservataires[key].insert(0, "Pas de réservataire")
        lines.extend(reservataires[key])

    return lines


def GetNombreSemainesPeriode(debut, fin):
    jours = (fin - debut).days
    if not (config.options & COMPATIBILITY_MODE_DECOMPTE_SEMAINES_2017):
        jours += 1
    if database.creche.arrondi_semaines in (ARRONDI_SEMAINE_SUPERIEURE, ARRONDI_SEMAINE_AVEC_LIMITE_52_SEMAINES):
        result = (jours + 6) // 7
        if database.creche.arrondi_semaines == ARRONDI_SEMAINE_AVEC_LIMITE_52_SEMAINES and GetDateAnniversaire(debut) > fin:
            return min(52, result)
        else:
            return result
    elif database.creche.arrondi_semaines == ARRONDI_SEMAINE_PLUS_PROCHE:
        return round(float(jours) / 7)
    else:
        return jours / 7


class Summary(object):
    def __init__(self, label):
        self.label = label
        self.array = list()
        for i in range(DAY_SIZE):
            self.array.append([0, 0])


def GetSiteFields(site):
    return [('site', GetNom(site)),
            ('nom-site', GetNom(site)),
            ('adresse-site', site.adresse if site else database.creche.adresse),
            ('code-postal-site', GetCodePostal(site) if site else GetCodePostal(database.creche)),
            ('ville-site', site.ville if site else database.creche.ville),
            ('telephone-site', site.telephone if site else database.creche.telephone),
            ('capacite-site', site.capacite if site else database.creche.get_capacite()),
            ('siret-site', site.siret if site else database.creche.siret),
            ('societe-site', site.societe if site else database.creche.societe),
            ]


def GetBureauFields(bureau):
    return [("directeur", bureau.directeur),
            ("president", bureau.president),
            ("vice-president", bureau.vice_president),
            ("tresorier", bureau.tresorier),
            ("secretaire", bureau.secretaire),
            ("gerant", bureau.gerant),
            ("directeur-adjoint", bureau.directeur_adjoint),
            ("comptable", bureau.comptable)
            ]


def GetCrecheFields(creche):
    return [('nom-creche', database.creche.nom),
            ('adresse-creche', database.creche.adresse),
            ('code-postal-creche', GetCodePostal(creche)),
            ('departement-creche', GetDepartement(creche.code_postal)),
            ('ville-creche', database.creche.ville),
            ('telephone-creche', database.creche.telephone),
            ('email-creche', database.creche.email),
            ('capacite', database.creche.get_capacite()),
            ('capacite-creche', database.creche.get_capacite()),
            ('amplitude-horaire', database.creche.get_amplitude_horaire()),
            ('sepa-creditor-id', database.creche.creditor_id),
            ('siret-creche', database.creche.siret),
            ('societe-creche', database.creche.societe),
            ]


def GetReservataireFields(reservataire):
    return [('nom-reservataire', reservataire.nom),
            ('tarif-reservataire', reservataire.tarif),
            ('periodicite-reservataire', reservataire.periode_facturation),
            ('adresse-reservataire', reservataire.adresse),
            ('code-postal-reservataire', GetCodePostal(reservataire)),
            ('ville-reservataire', reservataire.ville),
            ('telephone-reservataire', reservataire.telephone),
            ]


def GetTarifsHorairesFields(creche, date):
    tarif = Select(creche.tarifs_horaires, date)
    if tarif:
        return [('tarif(%s)' % cas[0], cas[1]) for cas in tarif.formule]
    else:
        return []


def GetCodePostal(what):
    try:
        return "%.05d" % what.code_postal
    except:
        return ""


def GetInscritSexe(inscrit):
    if inscrit.sexe == 1:
        return "Garçon"
    else:
        return "Fille"


def GetTelephone(famille):
    result = []
    for parent in famille.parents:
        if parent:
            if parent.telephone_domicile:
                result.append(parent.telephone_domicile)
            if parent.telephone_portable:
                result.append(parent.telephone_portable)
    return ", ".join(set(result))


def GetEmail(famille):
    result = []
    for parent in famille.parents:
        if parent and parent.email:
            result.append(parent.email)
    return ", ".join(result)


def GetTarifsFamilleFields(famille):
    return [(tarif.label.lower().replace(" ", "_"), tarif.label if (famille and (famille.tarifs & (1 << tarif.idx))) else "") for tarif in database.creche.tarifs_speciaux if tarif.label]


def GetParentFields(parent, index=None):
    ref = "parent%d" % index if index else "parent"
    return[(ref, GetPrenomNom(parent)),
           ('prenom-%s' % ref, parent.prenom),
           ('nom-%s' % ref, parent.nom),
           ('relation-%s' % ref, "papa" if parent.sexe == MASCULIN else "maman"),
           ('adresse-%s' % ref, parent.adresse if parent.adresse else parent.famille.adresse),
           ('code-postal-%s' % ref, GetCodePostal(parent) if parent.code_postal else GetCodePostal(parent.famille)),
           ('ville-%s' % ref, parent.ville if parent.ville else parent.famille.ville),
           ('telephone-domicile-%s' % ref, parent.telephone_domicile),
           ('telephone-travail-%s' % ref, parent.telephone_travail),
           ('telephone-portable-%s' % ref, parent.telephone_portable),
           ('email-%s' % ref, parent.email),
           ('profession-%s' % ref, parent.profession),
           ]


def GetFamilleFields(famille):
    result = [('adresse', famille.adresse if famille else ""),
              ('code-postal', GetCodePostal(famille) if famille else ""),
              ('ville', famille.ville if famille else ""),
              ('numero-securite-sociale', famille.numero_securite_sociale if famille else ""),
              ('numero-allocataire-caf', famille.numero_allocataire_caf if famille else ""),
              ('medecin-traitant', famille.medecin_traitant if famille else ""),
              ('telephone-medecin-traitant', famille.telephone_medecin_traitant if famille else ""),
              ('assureur', famille.assureur if famille else ""),
              ('police-assurance', famille.numero_police_assurance if famille else ""),
              ('noms-parents', GetParentsNomsString(famille) if famille else ""),
              ('civilites-parents', GetParentsCivilitesString(famille) if famille else ""),
              ('prenoms-parents', GetParentsPrenomsString(famille) if famille else ""),
              ('parents', GetParentsString(famille) if famille else ""),
              ('parents-version-longue', GetParentsString(famille, version_longue=True) if famille else ""),
              ('telephone', GetTelephone(famille) if famille else ""),
              ('email', GetEmail(famille) if famille else ""),
              ('sepa-mandate-id', famille.mandate_id),
              ]
    result += GetTarifsFamilleFields(famille)
    if famille:
        for i, parent in enumerate(famille.parents):
            if parent:
                result += GetParentFields(parent, i+1)
    return result


def GetInscritFields(inscrit):
    return GetFamilleFields(inscrit.famille if inscrit else None) + [
        ('prenom', inscrit.prenom if inscrit else ""),
        ('de-prenom', GetDeStr(inscrit.prenom) if inscrit else ""),
        ('nom', inscrit.nom if inscrit else ""),
        ('sexe', GetInscritSexe(inscrit) if inscrit else ""),
        ('naissance', inscrit.naissance if inscrit else ""),
        ('date-entretien-directrice', inscrit.date_entretien_directrice if inscrit else ""),
        ('age', GetAgeString(inscrit.naissance) if inscrit else ""),
        ('age-mois', GetAge(inscrit.naissance) if inscrit and inscrit.naissance else ""),
        ('entree', inscrit.inscriptions[0].debut if inscrit else ""),
        ('sortie', inscrit.inscriptions[-1].fin if inscrit else ""),
        ('ne-e', "né" if inscrit.sexe == 1 else "née"),
        ('type-repas-1', types_repas_1[inscrit.type_repas][0] if inscrit and inscrit.type_repas is not None else ""),
        ('type-repas-2', types_repas_2[inscrit.type_repas2][0] if inscrit and inscrit.type_repas2 is not None else ""),
        ('notes', inscrit.notes),
    ]


def GetSalarieFields(salarie):
    return [('nom', salarie.nom),
            ('prenom', salarie.prenom),
            ('de-prenom', GetDeStr(salarie.prenom)),
            ]            


def GetTypeContratString(type_contrat):
    for label, value in ModeAccueilItems:
        if type_contrat == value:
            return label
    else:
        return ""


def GetInscriptionFields(inscription):
    return [('debut-contrat', inscription.debut),
            ('fin-contrat', inscription.fin),
            ('type-contrat', GetTypeContratString(inscription.mode)),
            ('debut-inscription', inscription.debut),
            ('fin-inscription', inscription.fin),
            ('fin-adaptation', inscription.fin_periode_adaptation),
            ('duree-inscription-mois', (1 + inscription.fin.month - inscription.debut.month + 12 * (inscription.fin.year - inscription.debut.year)) if (inscription.fin and inscription.debut) else "N/A"),
            ('nombre-semaines-conges', inscription.semaines_conges),
            ('groupe', inscription.groupe.nom if inscription.groupe else ""),
            ('professeur-prenom', GetPrenom(inscription.professeur)),
            ('professeur-nom', GetNom(inscription.professeur)),
            ("jours-presence", ", ".join([days[i] for i in range(7) if inscription.get_day_from_index(i).get_state() > 0]))
            ] + GetSiteFields(inscription.site)


def GetCotisationFields(cotisation):
    if cotisation is None:
        return []
    result = [('nombre-factures', cotisation.nombre_factures),
              ('jours-semaine', cotisation.jours_semaine),
              ('heures-semaine', GetHeureString(cotisation.heures_semaine)),
              ('heures-mois', GetHeureString(cotisation.heures_mois)),
              ('debut-periode', cotisation.debut),
              ('fin-periode', cotisation.fin),
              ('mois-periode', GetDurationMonths(cotisation.debut, cotisation.fin)),
              ('heures-periode', GetHeureString(cotisation.heures_periode)),
              ('semaines-periode', cotisation.semaines_periode),
              ('factures-periode', cotisation.nombre_factures),
              ('frais-inscription', cotisation.frais_inscription, FIELD_EUROS),
              ('cotisation-mensuelle', cotisation.cotisation_mensuelle, FIELD_EUROS),
              ('montant-mensuel-activites', "%.02f" % cotisation.montant_mensuel_activites),
              ('cotisation-mensuelle-avec-activites', "%.02f" % cotisation.cotisation_mensuelle_avec_activites),
              ('enfants-a-charge', cotisation.enfants_a_charge),
              ('annee-debut', cotisation.debut.year),
              ('annee-fin', cotisation.debut.year+1),
              ('semaines-conges', cotisation.conges_inscription),
              ('liste-conges', ", ".join(cotisation.liste_conges)),
              ('montant-allocation-caf', cotisation.montant_allocation_caf, FIELD_EUROS),
              ('montant-credit-impots', cotisation.montant_credit_impots, FIELD_EUROS),
              ('tranche-paje', "PAJE%d" % cotisation.tranche_paje),
              ('cotisation-mensuelle-apres-allocation-caf', cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf, FIELD_EUROS),
              ('cotisation-mensuelle-apres-allocation-caf-et-credit-impots', cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf-cotisation.montant_credit_impots, FIELD_EUROS),
              ('cotisation-mensuelle-avec-activites-apres-allocation-caf-et-credit-impots', cotisation.cotisation_mensuelle_avec_activites-cotisation.montant_allocation_caf-cotisation.montant_credit_impots, FIELD_EUROS),
              ('cout-horaire-apres-allocation-caf-et-credit-impots', ((cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf-cotisation.montant_credit_impots) / cotisation.heures_mois) if cotisation.heures_mois != 0 else 0.0, FIELD_EUROS)
              ]
    if cotisation.montant_heure_garde is not None:
        result.append(('montant-heure-garde', cotisation.montant_heure_garde, FIELD_EUROS))
        result.append(('montant-semaine', cotisation.heures_semaine*cotisation.montant_heure_garde, FIELD_EUROS))
        result.append(('montant-periode', cotisation.heures_periode*cotisation.montant_heure_garde, FIELD_EUROS))
    if cotisation.montant_heure_garde and cotisation.cotisation_mensuelle:
        result.append(('montant-heure-garde-apres-allocation-caf', (cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf) / (cotisation.cotisation_mensuelle/cotisation.montant_heure_garde), FIELD_EUROS))
    else:
        result.append(('montant-heure-garde-apres-allocation-caf', 0.0, FIELD_EUROS))
    return result


def GetReglementFields(famille, annee, mois):
    total = 0.0
    dates = []
    moyens = set()
    for encaissement in famille.encaissements:
        if encaissement.date and encaissement.date.year == annee and encaissement.date.month == mois:
            total += encaissement.valeur
            dates.append(encaissement.date)
            if isinstance(encaissement.moyen_paiement, int):
                moyens.add(ModesEncaissement[encaissement.moyen_paiement][0])
            elif isinstance(encaissement.moyen_paiement, str):
                moyens.add(encaissement.moyen_paiement)
    result = [('date-reglement', ', '.join([date2str(date) for date in dates])),
              ('reglement', total, FIELD_EUROS),
              ('moyen-paiement', ', '.join(moyens))
              ]
    return result


def GetFactureFields(facture):
    if facture:
        taux_effort = 0.0
        if facture.taux_effort:
            taux_effort = facture.taux_effort
        if config.options & HEURES_CONTRAT:
            heures_contractualisees = facture.heures_contrat
            heures_facturees = facture.heures_facture
        else:
            heures_contractualisees = facture.heures_contractualisees
            heures_facturees = facture.heures_facturees
        result = [('mois', '%s %d' % (months[facture.mois - 1], facture.annee)),
                  ('mois+1', '%s %d' % ((months[facture.mois], facture.annee) if facture.mois < 12 else (months[0], facture.annee + 1))),
                  ('de-mois', '%s %d' % (GetDeMoisStr(facture.mois - 1), facture.annee)),
                  ('de-mois-recap', '%s %d' % (GetDeMoisStr(facture.debut_recap.month - 1), facture.debut_recap.year)),
                  ('today', date2str(datetime.date.today())),
                  ('date', date2str(facture.date)),
                  ('montant-heure-garde', facture.montant_heure_garde, FIELD_EUROS),
                  ('montant-jour-garde', facture.montant_jour_garde, FIELD_EUROS),
                  ('cotisation-mensuelle', facture.cotisation_mensuelle, FIELD_EUROS),
                  ('heures-cotisation-mensuelle', facture.heures_cotisation_mensuelle, FIELD_HEURES),
                  ('heures-contractualisees', heures_contractualisees, FIELD_HEURES),
                  ('heures-contrat', facture.heures_contrat, FIELD_HEURES),
                  ('heures-realisees', facture.heures_realisees, FIELD_HEURES),
                  ('jours-realises', facture.jours_realises),
                  ('heures-realisees-non-facturees', facture.heures_realisees_non_facturees, FIELD_HEURES),
                  ('heures-facturees-non-realisees', facture.heures_facturees_non_realisees, FIELD_HEURES),
                  ('heures-contractualisees-realisees', facture.heures_contractualisees_realisees, FIELD_HEURES),
                  ('heures-facture', sum(facture.heures_facture_par_mode), FIELD_HEURES),
                  ('heures-facturees', heures_facturees, FIELD_HEURES),
                  ('heures-supplementaires', facture.heures_supplementaires, FIELD_HEURES),
                  ('heures-maladie', facture.heures_maladie, FIELD_HEURES),
                  ('heures-maladie-non-deduites', sum(facture.jours_maladie_non_deduits.values()), FIELD_HEURES),
                  ('heures-absence-non-prevenue', sum(facture.jours_absence_non_prevenue.values()), FIELD_HEURES),
                  ('heures-absence-maladie', facture.heures_absence_maladie, FIELD_HEURES),
                  ('heures-previsionnelles', facture.heures_previsionnelles, FIELD_HEURES),
                  ('taux-effort', '%.2f' % taux_effort),
                  ('supplement-heures-supplementaires', facture.supplement_heures_supplementaires, FIELD_EUROS),
                  ('regularisation', facture.regularisation, FIELD_EUROS),
                  ('supplement', facture.supplement, FIELD_EUROS),
                  ('formule-supplement', facture.formule_supplement),
                  ('deduction', -facture.deduction, FIELD_EUROS | FIELD_SIGN),
                  ('formule-deduction', facture.formule_deduction),
                  ('supplement-avant-regularisation', facture.supplement_avant_regularisation, FIELD_EUROS),
                  ('raison-supplement-avant-regularisation', facture.raison_supplement_avant_regularisation),
                  ('deduction-avant-regularisation', facture.deduction_avant_regularisation, FIELD_EUROS),
                  ('raison-deduction-avant-regularisation', facture.raison_deduction_avant_regularisation),
                  ('correction', facture.correction, FIELD_EUROS),
                  ('libelle-correction', facture.libelle_correction),
                  ('raison-deduction', facture.raison_deduction),
                  ('raison-supplement', facture.raison_supplement),
                  ('raison-regularisation', facture.raison_regularisation),
                  ('tarif_activite', facture.formule_tarif_activite),
                  ('supplement-activites', facture.supplement_activites, FIELD_EUROS),
                  ('supplement_activites', facture.formule_supplement_activites),
                  ('heures_activites', facture.formule_heures_supplement_activites),
                  ('compte_activites', facture.formule_compte_supplement_activites),
                  ('majoration', facture.majoration_mensuelle, FIELD_EUROS | FIELD_SIGN),
                  ('frais-inscription', facture.frais_inscription, FIELD_EUROS | FIELD_SIGN),
                  ('total-sans-activites', facture.total - facture.supplement_activites, FIELD_EUROS),
                  ('site', GetNom(facture.site)),
                  ('total', facture.total, FIELD_EUROS),
                  ('numfact', facture.GetFactureId()),
                  ('sepa-date-prelevement', facture.GetDatePrelevementAutomatique()),
                  ]
        if config.codeclient == "custom":
            result.append(('codeclient', facture.inscrit.famille.code_client))
        elif isinstance(config.codeclient, str):
            result.append(('codeclient', config.codeclient % {"inscritid": facture.inscrit.idx, "nom": facture.inscrit.nom, "prenom": facture.inscrit.prenom, "nom4p1": GetNom4P1(facture.inscrit, database.creche.inscrits)}))
        return result
    else:
        return [(label, '?') for label in ('mois', 'de-mois', 'de-mois-recap', 'date', 'numfact', 'montant-heure-garde', 'cotisation-mensuelle', 
                                           'heures-contractualisees', 'heures-realisees', 'heures-contractualisees-realisees', 'heures-supplementaires', 'heures-previsionnelles', 
                                           'supplement', 'deduction', 'raison-deduction', 'supplement-activites', 'majoration', 'total')]


def SelectValueInChoice(choice, value):
    for i in range(choice.GetCount()):
        if choice.GetClientData(i) == value:
            choice.SetSelection(i)
            return i
    return None


def AddYearsToChoice(choice):
    for year in range(config.first_date.year, config.last_date.year + 1):
        choice.Append('Année %d' % year, year)
    choice.SetSelection(datetime.date.today().year - config.first_date.year)


def AddMonthsToChoice(choice):
    date = config.first_date
    while date < config.last_date:
        choice.Append('%s %d' % (months[date.month - 1], date.year), date)
        date = GetNextMonthStart(date)
    today = datetime.date.today()
    choice.SetStringSelection('%s %d' % (months[today.month - 1], today.year))


def Add2MonthsToChoice(choice):
    date = config.first_date
    while date < config.last_date:
        choice.Append('%s %d' % (months[date.month - 1], date.year), date)
        date = GetNextMonthStart(GetNextMonthStart(date))
    today = datetime.date.today()
    choice.SetStringSelection('%s %d' % (months[(today.month - 1) & 0xfe], today.year))


def AddWeeksToChoice(choice):
    date = first_monday = config.get_first_monday()
    while date < config.last_date:
        str = 'Semaine %d (%d %s %d)' % (date.isocalendar()[1], date.day, months[date.month - 1], date.year)
        choice.Append(str, date)
        date += datetime.timedelta(7)
    delta = datetime.date.today() - first_monday
    semaine = int(delta.days / 7)
    choice.SetSelection(semaine)


def GetDateFromWeek(year, week, weekday=0):
    return datetime.datetime.strptime("%d-W%d-%d" % (year, week, weekday), "%Y-W%W-%w")


class PeriodePresence(object):
    def __init__(self, date, arrivee=None, depart=None, absent=False, malade=False):
        self.date = date
        self.arrivee = arrivee
        self.depart = depart
        self.absent = absent
        self.malade = malade


def SplitLineTablette(line):
    label, idx, date = line.split()
    idx = int(idx)
    tm = time.strptime(date, "%Y-%m-%d@%H:%M")
    date = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)
    heure = tm.tm_hour * 60 + tm.tm_min
    if label.endswith("_salarie"):
        return True, label[:-8], idx, date, heure
    else:
        return False, label, idx, date, heure


def AddInscritsToChoice(choice):
    def __add_in_array(array, cell):
        if isinstance(cell, str):
            return '[%s]' % cell

        key = GetPrenomNom(cell, tri=database.creche.tri_inscriptions)
        if key.isspace():
            key = 'Nouvelle inscription'
        count = array.count(key)
        array.append(key)
        if count > 0:
            key += " (%d)" % count
        return '  ' + key 

    def __add_in_inscrits_choice(choice, inscrits):
        array = []
        for inscrit in inscrits:
            key = __add_in_array(array, inscrit)
            choice.Append(key, inscrit)
            
    choice.Clear()

    inscrits = []
    autres = []
    for inscrit in database.creche.inscrits:
        if (database.creche.tri_inscriptions & TRI_SANS_SEPARATION) or inscrit.get_inscription(datetime.date.today(), preinscription=True):
            inscrits.append(inscrit)
        else:
            autres.append(inscrit)
    
    if (config.options & RESERVATAIRES) and len(database.creche.reservataires):
        inscrits = GetEnfantsTriesParReservataire(inscrits)
    else:
        if len(inscrits) > 0 and len(autres) > 0:
            choice.Append("[Inscrits]", None)
        inscrits.sort(key=lambda inscrit: GetPrenomNom(inscrit, tri=database.creche.tri_inscriptions))

    __add_in_inscrits_choice(choice, inscrits)        
    
    if len(inscrits) > 0 and len(autres) > 0:
        choice.Append("[Anciens]", None)

    autres.sort(key=lambda inscrit: GetPrenomNom(inscrit, tri=database.creche.tri_inscriptions))

    __add_in_inscrits_choice(choice, autres)


def get_liste_permanences(date):
    permanences = database.query(TimeslotInscrit).filter(TimeslotInscrit.date == date).join(TimeslotInscrit.activity).filter(Activite.mode == MODE_PERMANENCE).all()
    return [(permanence.debut, permanence.fin, permanence.inscrit) for permanence in permanences]


def GetUrlTipi(famille):
    return config.tipi % {"famille": famille.idx}


def get_lines_summary(lines):
    activites = collections.OrderedDict()
    activites_sans_horaires = collections.OrderedDict()

    # collect the summary
    summary = collections.OrderedDict()
    for line in lines:
        line_summary = line.get_summary()
        for key in line_summary:
            if key not in summary:
                summary[key] = []
            summary[key].extend(line_summary[key])

    # sort everything
    for activity in summary:
        timeslots = summary[activity]
        if activity.mode == MODE_SANS_HORAIRES:
            activites_sans_horaires[activity] = len(timeslots)
        else:
            activites[activity] = []
            timeline = []
            for timeslot in timeslots:
                timeline.append([timeslot.debut, +1])
                timeline.append([timeslot.fin, -1])
            timeline.sort(key=lambda event: event[0])
            start, count = None, 0
            for i, event in enumerate(timeline):
                if event[1] == 0:
                    pass
                elif i + 1 < len(timeline) and event[0] == timeline[i + 1][0]:
                    timeline[i + 1][1] += event[1]
                else:
                    if start is not None:
                        activites[activity].append(Timeslot(start, event[0], activity, value=count))
                    count += event[1]
                    start = event[0] if count else None
    return activites, activites_sans_horaires
