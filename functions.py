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

def GetDateMinus(date, years, months):
    d = date.day
    if date.month > months:
        y = date.year-years
        m = date.month-months
    else:
        y = date.year-1-years
        m = date.month+12-months
    end = getMonthEnd(datetime.date(y, m, 1))
    if d > end.day:
        d = end.day
    return datetime.date(y, m, d)
                
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
    
def getTrimestreStart(date):
    return datetime.date(date.year, 1 + 3 * ((date.month-1)/3), 1)    

def getTrimestreEnd(date):
    nextTrimestre = getTrimestreStart(date) + datetime.timedelta(80)
    return getTrimestreStart(nextTrimestre) - datetime.timedelta(1)    

def GetHeureString(value):
    if value is None:
        return ""
    if not isinstance(value, int):
        value = int(round(value * 12))
    minutes = value * 5;
    heures = minutes / 60
    minutes -= heures * 60
    return "%dh%02d" % (heures, minutes)

def GetAgeString(naissance):
    if naissance:
        age = today.year * 12 + today.month - naissance.year * 12 - naissance.month
        if today.day < naissance.day:
            age -= 1
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
        date_str = "1er %s %d" % (months[date.month-1].lower(), date.year)
    else:
        date_str = "%d %s %d" % (date.day, months[date.month-1].lower(), date.year)
    if weekday:
        return days[date.weekday()].lower() + " " + date_str
    else:
        return date_str
    
def GetDureeArrondie(mode, start, end):
    if mode == ARRONDI_HEURE_ARRIVEE_DEPART:
        return (((end + 11) / 12) - (start / 12)) * 12  
    elif mode == ARRONDI_HEURE:
        return ((end-start+11) / 12) * 12
    elif mode == ARRONDI_HEURE_MARGE_DEMI_HEURE:
        return ((end-start+5) / 12) * 12
    elif mode == ARRONDI_DEMI_HEURE:
        return ((end-start+5) / 6) * 6
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
        capacite = site.capacite
    else:
        capacite = creche.GetCapacite()
    return GetJoursOuvres(annee, mois) * (creche.fermeture - creche.ouverture) * capacite
    
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

def GetNom4P1(person, array):
    if person:
        result = person.nom[:4].upper()
        noms = [p.nom[:4].upper() for p in array]
        if noms.count(result) > 1 and len(person.prenom) > 0:
            result += person.prenom[0].upper()
        return result
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
    nom = person.nom
    if maj_nom:
        nom = nom.upper()
    if creche.tri_planning == TRI_NOM:
        return "%s %s" % (nom, person.prenom)
    else:
        return "%s %s" % (person.prenom, nom)
    
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

def GetFile(filename, site, base):
    if site and site.nom:
        path = "./%s/%s_%s" % (base, site.nom, filename)
        if os.path.isfile(path):
            return path
    try:
        path = "./%s/%s_%s" % (base, creche.nom.lower(), filename)
        if os.path.isfile(path):
            return path
    except:
        pass
    path = "./%s/%s" % (base, filename)
    if os.path.isfile(path):
        return path
    else:
        return "./%s_dist/%s" % (base, filename)
    
def GetBitmapFile(filename, site=None):
    return GetFile(filename, site, "bitmaps")

def GetTemplateFile(filename, site=None):
    return GetFile(filename, site, "templates")

def IsTemplateFile(filename):
    path = "./templates/%s" % filename
    return os.path.isfile(path)

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

def GetInscritsByMode(start, end, mode, site=None): # TODO pourquoi retourner les index
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

def GetLines(date, inscrits, presence=False, site=None, groupe=None):
    lines = []
    for inscrit in inscrits:
        if date in inscrit.jours_conges:
            continue
        inscription = inscrit.GetInscription(date)
        if inscription and (site is None or inscription.site == site) and (groupe is None or inscription.groupe == groupe):
            if presence:
                state = inscrit.getState(date).state
                if state < 0 or not state & PRESENT:
                    continue 
            if date in inscrit.journees:
                line = inscrit.journees[date]
            else:
                line = inscription.getJourneeReferenceCopy(date)
            line.nom = inscrit.nom
            line.prenom = inscrit.prenom
            line.label = GetPrenomNom(inscrit)
            line.inscription = inscription
            line.reference = inscription.getJourneeReference(date)
            line.summary = 1 # TODO SUMMARY_NUM
            lines.append(line)
    return lines

def TrieParReservataires(inscrits):
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

        
def TrieParGroupes(lines):
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
    lines = []
    for key in keys:
        groupes[key].sort(key=lambda line: line.label)
        if key:
            groupes[key].insert(0, key.nom)                   
        lines.extend(groupes[key])

    return lines

def getActivityColor(value):
    if value < 0:
        if value == HOPITAL or value == MALADE_SANS_JUSTIFICATIF:
            value = MALADE
        if value == ABSENCE_CONGE_SANS_PREAVIS:
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
        self.GetDynamicText = None
        for i in range(DAY_SIZE):
            self.append([0, 0])
            
def GetActivitiesSummary(creche, lines):
    activites = {}
    activites_sans_horaires = {}
    for key in creche.activites:
        activite = creche.activites[key]
        if activite.mode == MODE_SANS_HORAIRES:
            activites_sans_horaires[key] = 0
        elif activite.mode != MODE_SYSTEMATIQUE_SANS_HORAIRES:
            activites[key] = Summary(activite.label)
        
    for line in lines:
        if line is not None and not isinstance(line, basestring):
            for start, end, value in line.activites:
                if value < PREVISIONNEL+CLOTURE:
                    value &= ~(PREVISIONNEL+CLOTURE)
                    if value in creche.activites:
                        for i in range(start, end):
                            if value in activites:
                                activites[value][i][line.summary-1] += 1
            for key in line.activites_sans_horaires:
                if key in activites_sans_horaires:
                    activites_sans_horaires[key] += 1
    return activites, activites_sans_horaires

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
           ]
    
def GetTarifsHorairesFields(creche):
    if creche.formule_taux_horaire:
        return [('tarif(%s)' % cas[0], cas[1]) for cas in creche.formule_taux_horaire]
    else:
        return []
    
def GetCodePostal(what):
    try:
        return "%.05d" % what.code_postal
    except:
        return ""

def GetInscritSexe(inscrit):
    if inscrit.sexe == 1:
        return u"Garçon"
    else:
        return "Fille"

def GetTelephone(inscrit):
    result = []
    for key in inscrit.parents:
        if inscrit.parents[key]:
            if inscrit.parents[key].telephone_domicile:
                result.append(inscrit.parents[key].telephone_domicile)
            if inscrit.parents[key].telephone_portable:
                result.append(inscrit.parents[key].telephone_portable)
    return ", ".join(set(result))

def GetEmail(inscrit):
    result = []
    for key in inscrit.parents:
        if inscrit.parents[key] and inscrit.parents[key].email:
            result.append(inscrit.parents[key].email)
    return ", ".join(result)
            
def GetInscritFields(inscrit):
    return [('adresse', inscrit.adresse),
            ('prenom', inscrit.prenom),
            ('nom', inscrit.nom),
            ('sexe', GetInscritSexe(inscrit)),
            ('adresse', inscrit.adresse),
            ('code-postal', GetCodePostal(inscrit)),
            ('ville', inscrit.ville),
            ('naissance', inscrit.naissance),
            ('age', GetAgeString(inscrit.naissance)),
            ('numero-securite-sociale', inscrit.numero_securite_sociale),
            ('numero-allocataire-caf', inscrit.numero_allocataire_caf),
            ('parents', GetParentsString(inscrit)),
            ('telephone', GetTelephone(inscrit)),
            ('email', GetEmail(inscrit)),
            ]

def GetInscriptionFields(inscription):
    if inscription.site:
        site_adresse, site_ville, site_telephone, site_capacite = inscription.site.adresse, inscription.site.ville, inscription.site.telephone, inscription.site.capacite 
    else:
        site_adresse, site_ville, site_telephone, site_capacite = creche.adresse, creche.ville, creche.telephone, creche.GetCapacite()
    return [('debut-contrat', inscription.debut),
            ('fin-contrat', inscription.fin),
            ('site', GetNom(inscription.site)),
            ('nom-site', GetNom(inscription.site)),
            ('adresse-site', site_adresse),
            ('code-postal-site', GetCodePostal(inscription.site)),
            ('ville-site', site_ville),
            ('telephone-site', site_telephone),
            ('capacite-site', site_capacite),
            ('professeur-prenom', GetPrenom(inscription.professeur)),
            ('professeur-nom', GetNom(inscription.professeur)),
            ]

def GetCotisationFields(cotisation):
    return [('nombre-factures', cotisation.nombre_factures),
            ('jours-semaine', cotisation.jours_semaine),
            ('heures-semaine', GetHeureString(cotisation.heures_semaine)),
            ('heures-mois', GetHeureString(cotisation.heures_mois)),
            ('heures-periode', GetHeureString(cotisation.heures_periode)),
            ('cotisation-mensuelle', "%.02f" % cotisation.cotisation_mensuelle),
            ('enfants-a-charge', cotisation.enfants_a_charge),            
            ('annee-debut', cotisation.debut.year),
            ('annee-fin', cotisation.debut.year+1),
           ]

def GetFactureFields(facture):
    if facture:
        taux_effort = 0.0
        if facture.taux_effort:
            taux_effort = facture.taux_effort
        result = [('mois', '%s %d' % (months[facture.mois - 1], facture.annee)),
                  ('de-mois', '%s %d' % (GetDeMoisStr(facture.mois - 1), facture.annee)),
                  ('de-mois-recap', '%s %d' % (GetDeMoisStr(facture.debut_recap.month - 1), facture.debut_recap.year)),
                  ('date', '%.2d/%.2d/%d' % (facture.date.day, facture.mois, facture.annee)),
                  ('montant-heure-garde', facture.montant_heure_garde, FIELD_EUROS),
                  ('cotisation-mensuelle', facture.cotisation_mensuelle, FIELD_EUROS),
                  ('heures-cotisation-mensuelle', GetHeureString(facture.heures_cotisation_mensuelle)),
                  ('heures-contractualisees', GetHeureString(facture.heures_contractualisees)),
                  ('heures-contrat', GetHeureString(facture.heures_contrat)),
                  ('heures-realisees', GetHeureString(facture.heures_realisees)),
                  ('heures-realisees-non-facturees', GetHeureString(facture.heures_realisees_non_facturees)),
                  ('heures-facturees-non-realisees', GetHeureString(facture.heures_facturees_non_realisees)),
                  ('heures-contractualisees-realisees', GetHeureString(facture.heures_contractualisees_realisees)),
                  ('heures-facturees', GetHeureString(facture.heures_facturees)),
                  ('heures-supplementaires', GetHeureString(facture.heures_supplementaires)),
                  ('heures-maladie', GetHeureString(facture.heures_maladie)),
                  ('heures-previsionnelles', GetHeureString(facture.heures_previsionnelles)),
                  ('taux-effort', '%.2f' % taux_effort),
                  ('supplement', facture.supplement, FIELD_EUROS),
                  ('formule-supplement', facture.formule_supplement),
                  ('deduction', -facture.deduction, FIELD_EUROS|FIELD_SIGN),
                  ('formule-deduction', facture.formule_deduction),
                  ('correction', facture.correction, FIELD_EUROS),
                  ('libelle-correction', facture.libelle_correction),
                  ('raison-deduction', facture.raison_deduction),
                  ('supplement-activites', facture.supplement_activites, FIELD_EUROS),
                  ('majoration', facture.majoration_mensuelle, FIELD_EUROS|FIELD_SIGN),
                  ('frais-inscription', facture.frais_inscription, FIELD_EUROS|FIELD_SIGN),
                  ('site', GetNom(facture.site)),
                  ('total', facture.total, FIELD_EUROS)]
        if config.numfact:
            result.append(('numfact', config.numfact % {"inscritid": facture.inscrit.idx, "numero": facture.numero, "annee": facture.annee, "mois": facture.mois}))
        else:
            result.append(('numfact', '%03d%04d%02d' % (facture.inscrit.idx, facture.annee, facture.mois)))
        if config.codeclient:
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
