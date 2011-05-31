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

import datetime, os.path
from constants import *
from parameters import *
import wx

def getFirstMonday():
    first_monday = first_date
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(1)
    return first_monday

def GetYearStart(date):
    return datetime.date(date.year, 1, 1)

def GetYearEnd(date):
    return datetime.date(date.year, 12, 31)

def getMonthStart(date):
    return datetime.date(date.year, date.month, 1)

def getMonthEnd(date):
    if date.month == 12:
        return datetime.date(date.year, 12, 31)
    else:
        return datetime.date(date.year, date.month + 1, 1) - datetime.timedelta(1)

def getNextMonthStart(date):
    if date.month == 12:
        return datetime.date(date.year+1, 1, 1)
    else:
        return datetime.date(date.year, date.month+1, 1)

def GetHeureString(value):
    if value is None:
        return ""
    elif isinstance(value, int):
        minutes = value * 5;
        heures = minutes / 60
        minutes -= heures * 60
    else:
        heures = int(value)
        minutes = (value - heures) * 60
    return "%dh%02d" % (heures, round(minutes))

def GetDateString(date, weekday=True):
    if date.day == 1:
        date_str = "1er %s %d" % (months[date.month-1].lower(), date.year)
    else:
        date_str = "%d %s %d" % (date.day, months[date.month-1].lower(), date.year)
    if weekday:
        return days[date.weekday()].lower() + " " + date_str
    else:
        return date_str
    
def IsPresentDuringTranche(journee, debut, fin):
    for start, end, value in journee.activites:
        if start < fin and end > debut and (not value & PREVISIONNEL or not value & CLOTURE):
            return True
    return False

def HeuresTranche(journee, debut, fin):
    result = [0] * ((fin - debut) * (60 / BASE_GRANULARITY))
    for start, end, value in journee.activites:
        if start < fin and end > debut and (not value & PREVISIONNEL or not value & CLOTURE):
            for i in range(max(start, debut) * (60 / BASE_GRANULARITY), min(end, fin) * (60 / BASE_GRANULARITY)):
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

def GetHeuresAccueil(annee, mois):
    return GetJoursOuvres(annee, mois) * (creche.fermeture - creche.ouverture) * creche.capacite
    
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
    
def GetPrenom(person):
    if person:
        return person.prenom
    else:
        return ""
    
def GetPrenomNom(person, maj_nom=False):
    if not person:
        return ""
    elif maj_nom:
        return "%s %s" % (person.prenom, person.nom.upper())
    else:
        return "%s %s" % (person.prenom, person.nom)
    
def GetEnfantsCount(inscrit, date):
    enfants_a_charge = 1
    enfants_en_creche = 1
    debut, fin = None, None
    for frere_soeur in inscrit.freres_soeurs:
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
    return enfants_a_charge, enfants_en_creche, debut, fin

def GetDepartement(cp):
    if cp:
        return int(cp/1000)
    else:
        return ""

def GetFile(filename, base):
    path = "./%s/%s" % (base, filename)
    if os.path.isfile(path):
        return path
    else:
        return "./%s_dist/%s" % (base, filename)
    
def GetBitmapFile(filename):
    return GetFile(filename, "bitmaps")

def GetTemplateFile(filename):
    return GetFile(filename, "templates")

def IsTemplateFile(filename):
    path = "./templates/%s" % filename
    return os.path.isfile(path)

def str2date(str, year=None):
    day = str.strip()
    if year and str.count('/') == 1:
        day += '/%d' % year
    try:
        (jour, mois, annee) = map(lambda x: int(x), day.split('/'))
        if annee < 1900:
            return None
        else:
            return datetime.date(annee, mois, jour)
    except:
        return None

def date2str(date):
    if date is None:
        return ''
    else:
        return '%.02d/%.02d/%.04d' % (date.day, date.month, date.year)

def periodestr(o):
    if None in (o.debut, o.fin) or (o.debut.year, o.debut.month, o.debut.day) != (o.fin.year, 1, 1) or (o.fin.month, o.fin.day) != (12, 31):
        return date2str(o.debut) + ' - ' + date2str(o.fin)
    else:
        return u"Année %d" % o.debut.year

def JourSemaineAffichable(day):
    day = day % 7
    if days[day] in creche.feries:
        return False
    elif day == 5 or day == 6:
        return not "Week-end" in creche.feries
    else:
        return True

def Select(object, date):
    for o in object:
        if o.debut and date >= o.debut and (not o.fin or date <= o.fin):
            return o
    return None

def GetDeMoisStr(mois):
    if months[mois].startswith('A') or months[mois].startswith('O'):
        return "d'%s" % months[mois].lower()
    else:
        return "de %s" % months[mois].lower()
       

def GetParentsString(inscrit):
    if not inscrit.parents['papa'] and not inscrit.parents['maman']:
        return "orphelin"
    elif not inscrit.parents['maman']:
        return GetPrenomNom(inscrit.parents['papa'])
    elif not inscrit.parents['papa']:
        return GetPrenomNom(inscrit.parents['maman'])
    else:
        papa = inscrit.parents['papa']
        maman = inscrit.parents['maman']
        if maman.nom == papa.nom:
            return '%s et %s %s' % (maman.prenom, papa.prenom, papa.nom)
        else:
            return '%s %s et %s %s' % (maman.prenom, maman.nom, papa.prenom, papa.nom)

def GetInscritsByMode(start, end, mode): # TODO pourquoi retourner les index
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        for inscription in inscrit.GetInscriptions(start, end):
            if inscription.mode & mode:
                result.append(i)
                break
    return result

def GetInscriptions(start, end):
    result = []
    for inscrit in creche.inscrits:
        for inscription in inscrit.GetInscriptions(start, end):
            result.append(inscription)
    return result

def getTriParCommuneEtNomIndexes(indexes):
    # Tri par commune (Rennes en premier) + ordre alphabetique des noms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        if (i1.ville.lower() != 'rennes' and i2.ville.lower() == 'rennes'):
            return 1
        elif (i1.ville.lower() == 'rennes' and i2.ville.lower() != 'rennes'):
            return -1
        else:
            return cmp("%s %s" % (i1.nom, i1.prenom), "%s %s" % (i2.nom, i2.prenom))

    indexes.sort(tri)
    return indexes

def getTriParPrenomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        return cmp(i1.prenom, i2.prenom)

    indexes.sort(tri)
    return indexes

def getTriParNomIndexes(indexes):
    # Tri par ordre alphabetique des prenoms
    def tri(one, two):
        i1 = creche.inscrits[one] ; i2 = creche.inscrits[two]
        return cmp(i1.nom, i2.nom)

    indexes.sort(tri)
    return indexes

def getPresentsIndexes(indexes, (debut, fin), site=None):
    if indexes is None:
        indexes = range(len(creche.inscrits))
    result = []
    if debut is None:
        return result
    for i in range(len(indexes)):
        inscrit = creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if ((inscription.fin is None or inscription.fin >= debut) and
                (not creche.preinscriptions or not inscription.preinscription) and
                (site is None or inscription.site == site) and
                inscription.debut != None and 
                (not fin or inscription.debut <= fin)):
                result.append(indexes[i])
                break
    return result

def GetInscrits(debut, fin, site=None):
    indexes = getPresentsIndexes(None, (debut, fin), site=site)
    return [creche.inscrits[i] for i in indexes]

def GetLines(date, inscrits, presence=False):
    lines = []
    for inscrit in inscrits:
        if date in inscrit.jours_conges:
            continue           
        inscription = inscrit.GetInscription(date)
        if inscription is not None:
            # print inscrit.prenom, 
            if presence:
                state = inscrit.getState(date)[0]
                if state < 0 or not state & PRESENT:
                    continue 
            if date in inscrit.journees:
                line = inscrit.journees[date]
            else:
                line = inscription.getReferenceDayCopy(date)
            line.nom = inscrit.nom
            line.prenom = inscrit.prenom
            line.label = GetPrenomNom(inscrit)
            line.inscription = inscription
            line.reference = inscription.getReferenceDay(date)
            lines.append(line)
    return lines

def getActivityColor(value):
    if value < 0:
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
        
class Summary(list):
    def __init__(self, label):
        self.label = label
        self.extend([0] * DAY_SIZE)
            
def GetActivitiesSummary(creche, lines):
    activites = {}
    activites_sans_horaires = {}
    for activite in creche.activites:
        if creche.activites[activite].mode == MODE_SANS_HORAIRES:
            activites_sans_horaires[activite] = 0
        else:
            activites[activite] = Summary(creche.activites[activite].label)
        
    for line in lines:
        for start, end, value in line.activites:
            if value < PREVISIONNEL+CLOTURE:
                value &= ~(PREVISIONNEL+CLOTURE)
                if value in creche.activites:
                    for i in range(start, end):
                        activites[value][i] += 1
        for key in line.activites_sans_horaires:            
            activites_sans_horaires[key] += 1
    return activites, activites_sans_horaires

def GetCrecheFields(creche):
    return [('nom-creche', creche.nom),
            ('adresse-creche', creche.adresse),
            ('code-postal-creche', str(creche.code_postal)),
            ('ville-creche', creche.ville),
            ('telephone-creche', creche.telephone),
            ('email-creche', creche.email),
            ('capacite', creche.capacite)]
    
def GetTarifsHorairesFields(creche):
    if creche.formule_taux_horaire:
        return [('tarif(%s)' % cas[0], cas[1]) for cas in creche.formule_taux_horaire]
    else:
        return []
    
def GetInscritFields(inscrit):
    return [('adresse', inscrit.adresse),
            ('prenom', inscrit.prenom),
            ('nom', inscrit.nom),
            ('code-postal', str(inscrit.code_postal)),
            ('ville', inscrit.ville),
            ('naissance', inscrit.naissance),
            ('numero-securite-sociale', inscrit.numero_securite_sociale),
            ('numero-allocataire-caf', inscrit.numero_allocataire_caf),
            ('parents', GetParentsString(inscrit))]
    
def GetFactureFields(facture):
    if facture:
        return [('mois', '%s %d' % (months[facture.mois - 1], facture.annee)),
                ('de-mois', '%s %d' % (GetDeMoisStr(facture.mois - 1), facture.annee)),
                ('de-mois-recap', '%s %d' % (GetDeMoisStr(facture.debut_recap.month - 1), facture.debut_recap.year)),
                ('date', '%.2d/%.2d/%d' % (facture.date.day, facture.mois, facture.annee)),
                ('numfact', '%03d%04d%02d' % (facture.inscrit.idx, facture.annee, facture.mois)),
                ('montant-heure-garde', facture.montant_heure_garde, FIELD_EUROS),
                ('cotisation-mensuelle', facture.cotisation_mensuelle, FIELD_EUROS),
                ('heures-supplementaires', '%.2f' % facture.heures_supplementaires),
                ('supplement', facture.supplement, FIELD_EUROS),
                ('deduction', '- %.2f' % facture.deduction),
                ('raison-deduction', facture.raison_deduction),
                ('supplement-activites', facture.supplement_activites, FIELD_EUROS),
                ('majoration', '+ %.2f' % facture.majoration_mensuelle),
                ('total', facture.total, FIELD_EUROS)]
    else:
        return [('mois', '?'),
                ('de-mois', '?'),
                ('de-mois-recap', '?'),
                ('date', '?'),
                ('numfact', '?'),
                ('montant-heure-garde', '?'),
                ('cotisation-mensuelle', '?'),
                ('heures-supplementaires', '?'),
                ('supplement', '?'),
                ('deduction', '?'),
                ('raison-deduction', '?'),
                ('supplement-activites', '?'),
                ('majoration', '?'),
                ('total', '?')]
    
class ProgressHandler:
    def __init__(self, display_fn=None, gauge_fn=None, min=None, max=None):
        self.display_fn = display_fn
        self.gauge_fn = gauge_fn
        self.min, self.max = min, max
        self.value = min
        
    def __del__(self):
        if self.gauge_fn:
            self.gauge_fn(self.max)

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
