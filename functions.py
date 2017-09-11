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

import sys, time, os.path
from constants import *
from parameters import *

if sys.platform != "win32":
    HOME = os.path.expanduser("~")
    GERTRUDE_DIRECTORY = HOME + "/.gertrude"


def GetCurrentMonday(date):
    return date - datetime.timedelta(date.weekday())


def GetNextMonday(date):
    return date + datetime.timedelta(7 - date.weekday())


def GetFirstMonday():
    return config.first_date - datetime.timedelta(config.first_date.weekday())


def GetYearStart(date):
    return datetime.date(date.year, 1, 1)


def GetYearEnd(date):
    return datetime.date(date.year, 12, 31)


def GetDateMinus(date, years, months=0):
    d = date.day
    if date.month > months:
        y = date.year-years
        m = date.month-months
    else:
        y = date.year-1-years
        m = date.month+12-months
    end = GetMonthEnd(datetime.date(y, m, 1))
    if d > end.day:
        d = end.day
    return datetime.date(y, m, d)


def GetMonthStart(date):
    return datetime.date(date.year, date.month, 1)


def GetMonthEnd(date):
    if date.month == 12:
        return datetime.date(date.year, 12, 31)
    else:
        return datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(1)


def GetNextMonthStart(date):
    if date.month == 12:
        return datetime.date(date.year+1, 1, 1)
    else:
        return datetime.date(date.year, date.month+1, 1)


def GetTrimestreStart(date):
    return datetime.date(date.year, 1 + 3 * ((date.month - 1) / 3), 1)


def GetTrimestreEnd(date):
    nextTrimestre = GetTrimestreStart(date) + datetime.timedelta(80)
    return GetTrimestreStart(nextTrimestre) - datetime.timedelta(1)    


def GetHeureString(value):
    if value is None:
        return ""
    if not isinstance(value, int):
        value = int(round(value * 12))
    minutes = value * 5
    if value >= 0:
        heures = minutes / 60
        minutes -= heures * 60
        return "%dh%02d" % (heures, minutes)
    else:
        minutes = -minutes
        heures = (minutes / 60)
        minutes -= heures * 60
        return "-%dh%02d" % (heures, minutes)


def GetAge(naissance, date=today):
    age = 0
    if naissance:
        age = (date.year - naissance.year) * 12 + date.month - naissance.month
        if date.day < naissance.day:
            age -= 1
    return age


def GetAgeString(naissance, date=today):
    if naissance:
        age = GetAge(naissance, date)
        annees, mois = age / 12, age % 12
        if annees < 0:
            return ""   
        elif annees and mois:
            return "%d ans et %d mois" % (annees, mois)
        elif annees:
            return "%d ans" % annees
        else:
            return "%d mois" % mois
    else:
        return ""


def GetDateString(date, weekday=True):
    if date.day == 1:
        date_str = "1er %s %d" % (months[date.month - 1].lower(), date.year)
    else:
        date_str = "%d %s %d" % (date.day, months[date.month - 1].lower(), date.year)
    if weekday:
        return days[date.weekday()].lower() + " " + date_str
    else:
        return date_str


def GetDureeArrondie(mode, start, end):
    if mode == ARRONDI_HEURE_ARRIVEE_DEPART:
        return (((end + 11) / 12) - (start / 12)) * 12  
    elif mode == ARRONDI_HEURE:
        return ((end - start + 11) / 12) * 12
    elif mode == ARRONDI_HEURE_MARGE_DEMI_HEURE:
        return ((end - start + 5) / 12) * 12
    elif mode == ARRONDI_DEMI_HEURE:
        return ((end - start + 5) / 6) * 6
    else:
        return end - start


def IsPresentDuringTranche(journee, debut, fin):
    for start, end, value in journee.activites:
        if start < fin and end > debut and (not value & PREVISIONNEL or not value & CLOTURE):
            return True
    return False


def HeuresTranche(journee, debut, fin):
    result = [0] * (24 * 60 / BASE_GRANULARITY)
    for start, end, value in journee.activites:
        if start < fin and end > debut and (not value & PREVISIONNEL or not value & CLOTURE):
            for i in range(max(start, debut), min(end, fin)):
                result[i] = 1
    return float(sum(result) * BASE_GRANULARITY) / 60


def GetJoursOuvres(annee, mois):
    jours_ouvres = 0
    date = datetime.date(annee, mois, 1)
    while date.month == mois:
        if not date in creche.jours_fermeture:
            jours_ouvres += 1
        date += datetime.timedelta(1)
    return jours_ouvres        


def GetHeuresAccueil(annee, mois, site=None):
    if site is not None:
        return GetJoursOuvres(annee, mois) * (creche.fermeture - creche.ouverture) * site.capacite
    result = 0.0
    date = datetime.date(annee, mois, 1)
    while date.month == mois:
        if not date in creche.jours_fermeture:
            result += creche.GetHeuresAccueil(date.weekday()) 
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


def GetPrenomNom(person, maj_nom=False, tri=None):
    if not person:
        return ""
    nom = person.nom
    if tri is None:
        tri = creche.tri_planning
    if maj_nom:
        nom = nom.upper()
    if (tri & 255) == TRI_NOM:
        return "%s %s" % (nom, person.prenom)
    else:
        return "%s %s" % (person.prenom, nom)


def GetDateAnniversaire(date, count=1):
    return datetime.date(date.year + count, date.month, date.day)


def GetInscritsFamille(famille):
    result = []
    for inscrit in creche.inscrits:
        if inscrit.famille is famille:
            result.append(inscrit)
    return result


def GetInscritsFrereSoeurs(inscrit):
    result = []
    for candidat in creche.inscrits:
        if candidat is not inscrit and candidat.famille == inscrit.famille:
            result.append(candidat)
    return result


def GetEnfantsCount(inscrit, date):
    enfants_a_charge = 1
    enfants_en_creche = 1
    debut, fin = None, None
    for frere_soeur in inscrit.famille.freres_soeurs:
        if frere_soeur.naissance:
            if frere_soeur.naissance <= date:
                if not debut or frere_soeur.naissance > debut:
                    debut = frere_soeur.naissance
                enfants_a_charge += 1
                if frere_soeur.entree and frere_soeur.entree <= date and (frere_soeur.sortie is None or frere_soeur.sortie > date):
                    enfants_en_creche += 1
            else:
                if not fin or frere_soeur.naissance < fin:
                    fin = frere_soeur.naissance
    for candidat in creche.inscrits:
        if candidat is not inscrit and candidat.famille == inscrit.famille:
            if candidat.naissance:
                if candidat.naissance <= date:
                    if not debut or candidat.naissance > debut:
                        debut = candidat.naissance
                    enfants_a_charge += 1
                    inscription = candidat.GetInscription(date)
                    if inscription and inscription.debut and inscription.debut <= date and (inscription.fin is None or inscription.fin > date):
                        enfants_en_creche += 1
                else:
                    if not fin or candidat.naissance < fin:
                        fin = candidat.naissance 
    return enfants_a_charge, enfants_en_creche, debut, fin


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
        paths.append("%s/%s_%s" % (path, site.nom, filename))
    try:
        paths.append("%s/[%s] %s" % (path, creche.nom.replace('"', ''), filename))
        paths.append("%s/[%s] %s" % (path, creche.nom.lower().replace('"', ''), filename))
    except:
        pass
    paths.append("%s/%s" % (path, filename))
    paths.append("%s/%s" % (path_dist, filename))
    if sys.platform == "darwin":
        paths.append("../Resources/%s" % filename)
    for directory in ["", "~/.gertrude/", "/usr/share/gertrude/"]:
        for path in paths:
            if os.path.isfile(directory + path):
                return directory + path
    return None


def GetBitmapFile(filename, site=None):
    return GetFile(filename, site, "bitmaps", "bitmaps_dist")


def GetTemplateFile(filename, site=None):
    return GetFile(filename, site, config.templates, "templates_dist")


def IsCustomTemplateFile(filename):
    if os.path.isfile("%s/%s" % (config.templates, filename)):
        return True
    elif os.path.isfile("%s/[%s] %s" % (config.templates, creche.nom, filename)):
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


def str2date(s, year=None, day=None):
    s = s.strip()
    if s.count('/') == 1:
        if year:
            s += '/%d' % year
        elif day:
            s = '01/' + s
    try:
        (jour, mois, annee) = map(lambda x: int(x), s.split('/'))
        if annee < 1900:
            return None
        else:
            return datetime.date(annee, mois, jour)
    except:
        return None


def Number2String(value):
    if isinstance(value, float):
        return "%.2f" % value
    else:
        return "%d" % value


def date2str(date):
    try:
        return '%.02d/%.02d/%.04d' % (date.day, date.month, date.year)
    except:
        return ''


def GetPeriodeString(o):
    if None in (o.debut, o.fin) or (o.debut.year, o.debut.month, o.debut.day) != (o.fin.year, 1, 1) or (o.fin.month, o.fin.day) != (12, 31):
        return date2str(o.debut) + ' - ' + date2str(o.fin)
    else:
        return "Année %d" % o.debut.year


def IsJourSemaineTravaille(day):
    day %= 7
    if days[day] in creche.feries:
        return False
    elif day == 5 or day == 6:
        return "Week-end" not in creche.feries
    else:
        return True


def GetNombreJoursSemaineTravailles():
    result = 0
    for day in range(7):
        if IsJourSemaineTravaille(day):
            result += 1
    return result


def Select(obj, date):
    for o in obj:
        if (not o.debut or date >= o.debut) and (not o.fin or date <= o.fin):
            return o
    return None


def GetDeStr(s):
    if len(s) > 0 and s[0].lower() in ('a', 'e', 'i', 'o', 'u'):
        return "d'" + s
    else:
        return "de " + s


def GetDeMoisStr(mois):
    return GetDeStr(months[mois].lower())


def GetBoolStr(val):
    if val:
        return "OUI"
    else:
        return "NON"


def GetParentsString(famille):
    if not famille.parents[0] and not famille.parents[1]:
        return "Pas de parents"
    elif not famille.parents[1]:
        return GetPrenomNom(famille.parents[0])
    elif not famille.parents[0]:
        return GetPrenomNom(famille.parents[1])
    else:
        parent1 = famille.parents[0]
        parent2 = famille.parents[1]
        if parent1.nom == parent2.nom:
            return '%s et %s %s' % (parent2.prenom, parent1.prenom, parent1.nom)
        else:
            return '%s %s et %s %s' % (parent2.prenom, parent2.nom, parent1.prenom, parent1.nom)


def GetParentsPrenomsString(famille):
    parent1 = famille.parents[0]
    parent2 = famille.parents[1]
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
    parent1 = famille.parents[0]
    parent2 = famille.parents[1]
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
            if parent.relation == "papa":
                messieurs.append("M.")
            elif parent.relation == "maman":
                mesdames.append("Mme")
    return "/".join(mesdames + messieurs)


def GetInscritsByMode(start, end, mode, site=None):  # TODO pourquoi retourner les index
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        for inscription in inscrit.GetInscriptions(start, end):
            if inscription.mode & mode and (site is None or inscription.site == site):
                result.append(i)
                break
    return result


def GetInscriptions(start, end):
    result = []
    for inscrit in creche.inscrits:
        for inscription in inscrit.GetInscriptions(start, end):
            result.append(inscription)
    return result


def GetSalaries(start, end, site=None):
    result = []
    for salarie in creche.salaries:
        for contrat in salarie.GetContrats(start, end):
            if site is None or contrat.site == site:
                result.append(salarie)
                break
    return result


def GetTriParCommuneEtNomIndexes(indexes):
    # Tri par commune (Rennes en premier) + ordre alphabetique des noms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        if i1.famille.ville.lower() != 'rennes' and i2.famille.ville.lower() == 'rennes':
            return 1
        elif i1.famille.ville.lower() == 'rennes' and i2.famille.ville.lower() != 'rennes':
            return -1
        else:
            return cmp("%s %s" % (i1.nom, i1.prenom), "%s %s" % (i2.nom, i2.prenom))

    indexes.sort(tri)
    return indexes


def GetTriParPrenomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1, i2 = creche.inscrits[one], creche.inscrits[two]
        return cmp(i1.prenom, i2.prenom)

    indexes.sort(tri)
    return indexes


def GetTriParNomIndexes(indexes):
    def tri(one, two):
        i1, i2 = creche.inscrits[one], creche.inscrits[two]
        return cmp(i1.nom, i2.nom)

    indexes.sort(tri)
    return indexes


def GetEnfantsTries(enfants, tri):
    if enfants is None:
        enfants = creche.inscrits[:]
    else:
        enfants = enfants[:]
    enfants.sort(tri)
    return enfants


def GetEnfantsTriesParNom(enfants=None):
    def tri(one, two):
        return cmp(GetPrenomNom(one, tri=TRI_NOM), GetPrenomNom(two, tri=TRI_NOM))
    return GetEnfantsTries(enfants, tri)


def GetEnfantsTriesParPrenom(enfants=None):
    def tri(one, two):
        return cmp(GetPrenomNom(one), GetPrenomNom(two))
    return GetEnfantsTries(enfants, tri)


def GetEnfantsTriesParNomParents(enfants=None):
    def tri(one, two):
        return cmp(GetParentsNomsString(one.famille), GetParentsNomsString(two.famille))
    return GetEnfantsTries(enfants, tri)


def GetGroupesEnfants(lines):
    groupes = {}
    for line in lines:
        groupe = line.inscription.groupe
        if groupe not in groupes:
            groupes[groupe] = []
        groupes[groupe].append(line)

    keys = groupes.keys()

    def tri(one, two):
        if one is None:
            return -1
        elif two is None:
            return 1
        else:
            return cmp(one.ordre, two.ordre)

    keys.sort(tri)

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
    if creche.tri_planning & TRI_GROUPE:
        return GetEnfantsTriesParGroupe(enfants)
    elif creche.tri_planning == TRI_NOM:
        return GetEnfantsTriesParNom(enfants)
    else:
        return GetEnfantsTriesParPrenom(enfants)


def GetEnfantsTriesSelonParametreTriFacture(enfants):
    if creche.tri_factures == TRI_NOM:
        return GetEnfantsTriesParNom(enfants)
    elif creche.tri_factures == TRI_NOM_PARENTS:
        return GetEnfantsTriesParNomParents(enfants)
    elif creche.tri_factures == TRI_PRENOM:
        return GetEnfantsTriesParPrenom(enfants)
    else:
        return enfants


def GetPresentsIndexes(indexes, (debut, fin), site=None):
    if indexes is None:
        indexes = range(len(creche.inscrits))
    result = []
    if debut is None:
        return result
    for i in range(len(indexes)):
        inscrit = creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if (inscription.fin is None or inscription.fin >= debut) and \
                    (not creche.preinscriptions or not inscription.preinscription) and \
                    (site is None or inscription.site == site) and \
                    (inscription.debut is not None) and \
                    (not fin or inscription.debut <= fin):
                result.append(indexes[i])
                break
    return result


def GetInscrits(start, end, site=None, handicap=None):
    result = []
    for inscrit in creche.inscrits:
        if inscrit.IsPresent(start, end, site, handicap):
            result.append(inscrit)
    return result


def GetLines(date, inscrits, presence=False, site=None, groupe=None, summary=SUMMARY_ENFANT):
    lines = []
    for inscrit in inscrits:
        inscription = inscrit.GetInscription(date)
        if inscription and (site is None or inscription.site == site) and (groupe is None or inscription.groupe == groupe):
            if presence:
                state = inscrit.GetStateSimple(date)
                if state < 0 or not state & PRESENT:
                    continue
            if date in inscrit.jours_conges or inscrit.GetStateSimple(date) < 0:
                continue
            if date in inscrit.journees:
                line = inscrit.journees[date]
            else:
                line = inscription.GetJourneeReferenceCopy(date)
            line.nom = inscrit.nom
            line.prenom = inscrit.prenom
            line.label = GetPrenomNom(inscrit)
            line.sublabel = ""
            line.inscription = inscription
            line.reference = inscription.GetJourneeReference(date)
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
            reservataires[key].insert(0, u'Pas de réservataire')
        lines.extend(reservataires[key])

    return lines


def GetActivityColor(value):
    if value < 0:
        if value == HOPITAL or value == MALADE_SANS_JUSTIFICATIF:
            value = MALADE
        if value in (ABSENCE_CONGE_SANS_PREAVIS, CONGES_PAYES):
            value = VACANCES
        return creche.couleurs[value].couleur
    activity = value & ~(PREVISIONNEL|SUPPLEMENT|CLOTURE)
    if activity in creche.activites:
        if value & PREVISIONNEL:
            return creche.activites[activity].couleur_previsionnel
        if value & SUPPLEMENT:
            return creche.activites[activity].couleur_supplement
        else:
            return creche.activites[activity].couleur
    else:
        return 0, 0, 0, 0, 100


def GetUnionHeures(journee, reference):
    result = []
    for start, end, value in journee.activites:
        if value == 0:
            result.append((start, end))
    for start, end, value in reference.activites:
        if value == 0:
            result.append((start, end))
    
    again = True
    while again:
        again = False
        union = result[:]
        result = []
        for start, end in union:
            found = False
            for i, (s, e) in enumerate(result):
                if end < s or start > e:
                    pass
                elif start >= s and end <= e:
                    found = True
                elif start <= s or end >= e:
                    result[i] = (min(s, start), max(e, end))
                    found = True
            if not found:
                result.append((start, end))
            else:
                again = True

    return result


def GetNombreSemainesPeriode(debut, fin):
    jours = (fin - debut).days
    if not (config.options & COMPATIBILITY_MODE_DECOMPTE_SEMAINES_2017):
        jours += 1
    if creche.arrondi_semaines == ARRONDI_SEMAINE_SUPERIEURE:
        return (jours + 6) / 7
    elif creche.arrondi_semaines == ARRONDI_SEMAINE_PLUS_PROCHE:
        return round(float(jours) / 7)
    else:
        return float(jours) / 7


class State(object):
    def __init__(self, state, heures_contractualisees=.0, heures_realisees=.0, heures_facturees=.0):
        self.state = state
        self.heures_contractualisees = heures_contractualisees
        self.heures_realisees = heures_realisees 
        self.heures_facturees = heures_facturees
        
    def __str__(self):
        return "state:%d, contrat:%f, realise:%f, facture:%f" % (self.state, self.heures_contractualisees, self.heures_realisees, self.heures_facturees) 


class Summary(list):
    def __init__(self, label):
        self.options = 0
        self.label = label
        self.sublabel = ""
        self.GetDynamicText = None
        for i in range(DAY_SIZE):
            self.append([0, 0])


def GetActivitiesSummary(creche, lines, options=0):
    activites = {}
    activites_sans_horaires = {}
    for key in creche.activites:
        activite = creche.activites[key]
        if activite.mode == MODE_SANS_HORAIRES:
            activites_sans_horaires[key] = 0
        elif activite.mode not in (MODE_SYSTEMATIQUE_SANS_HORAIRES, MODE_SYSTEMATIQUE_SANS_HORAIRES_MENSUALISE):
            activites[key] = Summary(activite.label)
    if not (options & NO_SALARIES) and len(creche.salaries) > 0:
        activite_salaries = activites[PRESENCE_SALARIE] = Summary("Présences salariés")
    else:
        activite_salaries = None
        
    for line in lines:
        if line is not None and not isinstance(line, basestring):
            for start, end, value in line.activites:
                if value < PREVISIONNEL+CLOTURE:
                    value &= ~(PREVISIONNEL+CLOTURE)
                    if value in creche.activites:
                        if value == 0:
                            for i in range(start, end):
                                if value in activites:
                                    activites[value][i][line.summary-1] += 1
                                    if not (options & NO_SALARIES) and line.summary == SUMMARY_SALARIE and activite_salaries:
                                        activite_salaries[i][0] += 1
                                    
            for key in line.activites_sans_horaires:
                if key in activites_sans_horaires:
                    activites_sans_horaires[key] += 1  
    
    return activites, activites_sans_horaires


def GetSiteFields(site):
    return [('site', GetNom(site)),
            ('nom-site', GetNom(site)),
            ('adresse-site', site.adresse if site else creche.adresse),
            ('code-postal-site', GetCodePostal(site) if site else GetCodePostal(creche)),
            ('ville-site', site.ville if site else creche.ville),
            ('telephone-site', site.telephone if site else creche.telephone),
            ('capacite-site', site.capacite if site else creche.GetCapacite()),
            ]


def GetCrecheFields(creche):
    return [('nom-creche', creche.nom),
            ('adresse-creche', creche.adresse),
            ('code-postal-creche', GetCodePostal(creche)),
            ('departement-creche', GetDepartement(creche.code_postal)),
            ('ville-creche', creche.ville),
            ('telephone-creche', creche.telephone),
            ('email-creche', creche.email),
            ('capacite', creche.GetCapacite()),
            ('capacite-creche', creche.GetCapacite()),
            ('amplitude-horaire', creche.GetAmplitudeHoraire()),
            ('sepa-creditor-id', creche.creditor_id),
            ('siret-creche', creche.siret),
            ]


def GetReservataireFields(reservataire):
    return [('nom-reservataire', reservataire.nom),
            ('tarif-reservataire', reservataire.tarif),
            ('tarif-periode-reservataire', reservataire.tarif * reservataire.periode_facturation),
            ('periodicite-reservataire', reservataire.periode_facturation),
            ('adresse-reservataire', reservataire.adresse),
            ('code-postal-reservataire', GetCodePostal(reservataire)),
            ('ville-reservataire', reservataire.ville),
            ('telephone-reservataire', reservataire.telephone),
            ]


def GetTarifsHorairesFields(creche, date):
    tarifs = Select(creche.tarifs_horaires, date)
    if tarifs:
        return [('tarif(%s)' % cas[0], cas[1]) for cas in tarifs]
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
    return [(tarif.label.lower().replace(" ", "_"), tarif.label if (famille and (famille.tarifs & (1 << tarif.idx))) else "") for tarif in creche.tarifs_speciaux]


def GetParentFields(parent, index=None):
    ref = "parent%d" % index if index else "parent"
    return[(ref, GetPrenomNom(parent)),
           ('prenom-%s' % ref, parent.prenom),
           ('nom-%s' % ref, parent.nom),
           ('relation-%s' % ref, parent.relation),
           ('adresse-%s' % ref, parent.adresse),
           ('code-postal-%s' % ref, parent.code_postal),
           ('ville-%s' % ref, parent.ville),
           ('email-%s' % ref, parent.email),
           ('telephone-domicile-%s' % ref, parent.telephone_domicile),
           ('telephone-travail-%s' % ref, parent.telephone_travail),
           ('telephone-portable-%s' % ref, parent.telephone_portable),
           ('email-%s' % ref, parent.email),
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
        ('age', GetAgeString(inscrit.naissance) if inscrit else ""),
        ('entree', inscrit.inscriptions[0].debut if inscrit else ""),
        ('sortie', inscrit.inscriptions[-1].fin if inscrit else ""),
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
            ('type-contrat', GetTypeContratString(inscription.type)),
            ('debut-inscription', inscription.debut),
            ('fin-inscription', inscription.fin),
            ('fin-adaptation', inscription.fin_periode_adaptation),
            ('duree-inscription-mois', (1 + inscription.fin.month - inscription.debut.month) if (inscription.fin and inscription.debut) else "N/A"),
            ('nombre-semaines-conges', inscription.semaines_conges),
            ('groupe', inscription.groupe.nom if inscription.groupe else ""),
            ('professeur-prenom', GetPrenom(inscription.professeur)),
            ('professeur-nom', GetNom(inscription.professeur)),
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
              ('heures-periode', GetHeureString(cotisation.heures_periode)),
              ('semaines-periode', cotisation.semaines_periode),
              ('factures-periode', cotisation.nombre_factures),
              ('frais-inscription', cotisation.frais_inscription, FIELD_EUROS | FIELD_SIGN),
              ('cotisation-mensuelle', "%.02f" % cotisation.cotisation_mensuelle),
              ('montant-mensuel-activites', "%.02f" % cotisation.montant_mensuel_activites),
              ('cotisation-mensuelle-avec-activites', "%.02f" % cotisation.cotisation_mensuelle_avec_activites),
              ('enfants-a-charge', cotisation.enfants_a_charge),
              ('annee-debut', cotisation.debut.year),
              ('annee-fin', cotisation.debut.year+1),
              ('semaines-conges', cotisation.conges_inscription),
              ('liste-conges', ", ".join(cotisation.liste_conges)),
              ('montant-allocation-caf', cotisation.montant_allocation_caf, FIELD_EUROS | FIELD_SIGN),
              ('cotisation-mensuelle-apres-allocation-caf', cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf, FIELD_EUROS | FIELD_SIGN),
              ]
    if cotisation.montant_heure_garde is not None:
        result.append(('montant-semaine', cotisation.heures_semaine*cotisation.montant_heure_garde, FIELD_EUROS|FIELD_SIGN))
        result.append(('montant-periode', cotisation.heures_periode*cotisation.montant_heure_garde, FIELD_EUROS|FIELD_SIGN))
    if cotisation.montant_heure_garde and cotisation.cotisation_mensuelle:
        result.append(('montant-heure-garde-apres-allocation-caf', (cotisation.cotisation_mensuelle-cotisation.montant_allocation_caf) / (cotisation.cotisation_mensuelle/cotisation.montant_heure_garde), FIELD_EUROS|FIELD_SIGN))
    else:
        result.append(('montant-heure-garde-apres-allocation-caf', 0.0, FIELD_EUROS|FIELD_SIGN))
    return result


def GetReglementFields(famille, annee, mois):
    total = 0.0
    dates = []
    moyens = set()
    for encaissement in famille.encaissements:
        if encaissement.date and encaissement.date.year == annee and encaissement.date.month == mois:
            total += encaissement.valeur
            dates.append(encaissement.date)
            moyens.add(ModesEncaissement[encaissement.moyen_paiement][0] if isinstance(encaissement.moyen_paiement, int) else encaissement.moyen_paiement)
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
        elif isinstance(config.codeclient, basestring):
            result.append(('codeclient', config.codeclient % {"inscritid": facture.inscrit.idx, "nom": facture.inscrit.nom, "prenom": facture.inscrit.prenom, "nom4p1": GetNom4P1(facture.inscrit, creche.inscrits)}))
        return result
    else:
        return [(label, '?') for label in ('mois', 'de-mois', 'de-mois-recap', 'date', 'numfact', 'montant-heure-garde', 'cotisation-mensuelle', 
                                           'heures-contractualisees', 'heures-realisees', 'heures-contractualisees-realisees', 'heures-supplementaires', 'heures-previsionnelles', 
                                           'supplement', 'deduction', 'raison-deduction', 'supplement-activites', 'majoration', 'total')]


class ProgressHandler:
    def __init__(self, display_fn=None, gauge_fn=None, min=None, max=None):
        self.display_fn = display_fn
        self.gauge_fn = gauge_fn
        self.min, self.max = min, max
        self.value = min
        
    def set(self, value):
        if self.gauge_fn:
            self.gauge_fn(self.min + (self.max-self.min)*value/100)

    def display(self, s):
        print s
        if self.display_fn:
            self.display_fn(s+"\n")

    def new(self, ratio):
        return ProgressHandler(self.display_fn, self.gauge_fn, self.value, self.value + (self.max-self.min)*ratio/100)

default_progress_handler = ProgressHandler()


def SelectValueInChoice(choice, value):
    for i in range(choice.GetCount()):
        if choice.GetClientData(i) == value:
            choice.SetSelection(i)
            return i
    return None


def AddYearsToChoice(choice):
    for year in range(config.first_date.year, config.last_date.year + 1):
        choice.Append(u'Année %d' % year, year)
    choice.SetSelection(today.year - config.first_date.year)


def AddMonthsToChoice(choice):
    date = config.first_date
    while date < config.last_date:
        choice.Append(u'%s %d' % (months[date.month - 1], date.year), date)
        date = GetNextMonthStart(date)
    choice.SetStringSelection('%s %d' % (months[today.month - 1], today.year))


def Add2MonthsToChoice(choice):
    date = config.first_date
    while date < config.last_date:
        choice.Append(u'%s %d' % (months[date.month - 1], date.year), date)
        date = GetNextMonthStart(GetNextMonthStart(date))
    choice.SetStringSelection('%s %d' % (months[(today.month - 1) & 0xfe], today.year))


def AddWeeksToChoice(choice):
    date = first_monday = GetFirstMonday()
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
        if isinstance(cell, basestring):
            return '[%s]' % cell

        key = GetPrenomNom(cell, tri=creche.tri_inscriptions)
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
    for inscrit in creche.inscrits:
        if (creche.tri_inscriptions & TRI_SANS_SEPARATION) or inscrit.GetInscription(datetime.date.today(), preinscription=True):
            inscrits.append(inscrit)
        else:
            autres.append(inscrit)
    
    if (config.options & RESERVATAIRES) and len(creche.reservataires):
        inscrits = GetEnfantsTriesParReservataire(inscrits)
    else:
        if len(inscrits) > 0 and len(autres) > 0:
            choice.Append("[Inscrits]", None)
        inscrits.sort(key=lambda inscrit: GetPrenomNom(inscrit, tri=creche.tri_inscriptions))

    __add_in_inscrits_choice(choice, inscrits)        
    
    if len(inscrits) > 0 and len(autres) > 0:
        choice.Append("[Anciens]", None)

    autres.sort(key=lambda inscrit: GetPrenomNom(inscrit, tri=creche.tri_inscriptions))

    __add_in_inscrits_choice(choice, autres)


def GetListePermanences(date):
    result = []
    for inscrit in creche.inscrits:
        journee = inscrit.GetJournee(date)
        if journee:
            liste = journee.GetListeActivitesParMode(MODE_PERMANENCE)
            for start, end in liste:
                result.append((start, end, inscrit))
    return result


def GetUrlTipi(famille):
    return config.database.tipi % {"famille": famille.idx}


def GetPlanningStates(salarie=False):
    if salarie:
        return [VACANCES, CONGES_PAYES, MALADE, PRESENT]
    else:
        states = [VACANCES, ABSENCE_CONGE_SANS_PREAVIS, ABSENCE_NON_PREVENUE, MALADE, HOPITAL, MALADE_SANS_JUSTIFICATIF, PRESENT]
        if not creche.gestion_preavis_conges:
            states.remove(ABSENCE_CONGE_SANS_PREAVIS)
        if not creche.gestion_absences_non_prevenues:
            states.remove(ABSENCE_NON_PREVENUE)
        if not creche.gestion_maladie_hospitalisation:
            states.remove(HOPITAL)
        if not creche.gestion_maladie_sans_justificatif:
            states.remove(MALADE_SANS_JUSTIFICATIF)
        return states


class LigneConge(object):
    def __init__(self, state, info):
        self.state = state
        self.info = info
        self.readonly = True
        self.reference = None
        self.options = 0
        self.commentaire = ""

    def GetNombreHeures(self):
        return 0.0

    def GetDynamicText(self):
        return None

    def GetStateIcon(self):
        return self.state


def GetDateIntersection(periodes):
    for one in range(0, len(periodes)-1):
        i1 = periodes[one]
        if i1.debut:
            for two in range(one+1, len(periodes)):
                i2 = periodes[two]
                if i2.debut:
                    latest_start = max(i1.debut, i2.debut)
                    earliest_end = min(i1.GetFin(), i2.GetFin())
                    if (earliest_end - latest_start).days > 0:
                        return latest_start
    return None
