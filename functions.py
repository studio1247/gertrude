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

import datetime, binascii
from constants import *
from parameters import *
import wx

def getFirstMonday():
    first_monday = first_date
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(1)
    return first_monday

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

def getDateStr(date, weekday=True):
    if date.day == 1:
        date_str = "1er %s %d" % (months[date.month-1].lower(), date.year)
    else:
        date_str = "%d %s %d" % (date.day, months[date.month-1].lower(), date.year)
    if weekday:
        return days[date.weekday()].lower() + " " + date_str
    else:
        return date_str

def getInitialesPrenom(person):
    for char in ('-', ' '):
        if char in person.prenom:
            parts = person.prenom.split(char)
            return ''.join([part[0] for part in parts if len(part) > 0])
    return person.prenom[0]   

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

def Select(object, date):
    for o in object:
        if o.debut and date >= o.debut and (not o.fin or date <= o.fin):
            return o
    return None

def getDeMoisStr(mois):
    if months[mois].startswith('A') or months[mois].startswith('O'):
        return "d'%s" % months[mois].lower()
    else:
        return "de %s" % months[mois].lower()

def getParentsStr(inscrit):
    if inscrit.papa.nom == inscrit.maman.nom:
        return '%s et %s %s' % (inscrit.maman.prenom, inscrit.papa.prenom, inscrit.papa.nom)
    else:
        return '%s %s et %s %s' % (inscrit.maman.prenom, inscrit.maman.nom, inscrit.papa.prenom, inscrit.papa.nom)

def GetInscritId(inscrit, inscrits):
    for i in inscrits:
        if (inscrit != i and inscrit.prenom == i.prenom):
            return inscrit.prenom + " " + inscrit.nom
    return inscrit.prenom

def getInscritsByMode(start, end, mode): # TODO pourquoi retourner les index
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        for inscription in inscrit.getInscriptions(start, end):
            if inscription.mode & mode:
                result.append(i)
                break
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

def getPresentsIndexes(indexes, (debut, fin)):
    if indexes is None:
        indexes = range(len(creche.inscrits))
    result = []
    for i in range(len(indexes)):
        inscrit = creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if ((inscription.fin is None or inscription.fin >= debut) and (inscription.debut != None and (not fin or inscription.debut <= fin))):
                result.append(indexes[i])
                break
    return result

def getInscrits(debut, fin):
    indexes = getPresentsIndexes(None, (debut, fin))
    return [creche.inscrits[i] for i in indexes]

def getLines(date, inscrits):
    lines = []
    for inscrit in inscrits:
        if inscrit.getInscription(date) is not None:
            # print inscrit.prenom, 
            if date in inscrit.journees:
                line = inscrit.journees[date]
            else:
                line = inscrit.getReferenceDayCopy(date)
            line.nom = inscrit.nom
            line.prenom = inscrit.prenom
            line.label = GetInscritId(inscrit, inscrits)
            line.reference = inscrit.getReferenceDay(date)
            lines.append(line)
    return lines

def getActivityColor(value):
    if value < 0:
        return creche.couleurs[value].couleur
    activity = value & ~(PREVISIONNEL|SUPPLEMENT)
    if activity in creche.activites:
        if value & PREVISIONNEL:
            return creche.activites[activity].couleur_previsionnel
        if value & SUPPLEMENT:
            return creche.activites[activity].couleur_supplement
        else:
            return creche.activites[activity].couleur
    else:
        return 0, 0, 0, 0, 100
        
def getActivitiesSummary(creche, lines):
    class Summary(list):
        def __init__(self, label):
            self.label = label
            self.extend([0] * 96)
            
    summary = {}
    for activity in creche.activites:
        summary[activity] = Summary(creche.activites[activity].label)
        for i in range(96):
            for line in lines:
                if not isinstance(line, list):
                    line = line.values
                if line[i] > 0 and line[i] & (1 << activity):
                    summary[activity][i] += 1
    return summary

class ProgressHandler:
    def __init__(self, display_fn=None, gauge=None, max=None):
        self.display_fn = display_fn
        self.gauge = gauge
        self.max = max
        if self.gauge: self.min = self.gauge.GetValue()
        
    def __del__(self):
        if self.gauge: self.gauge.SetValue(self.max)

    def set(self, value):
        if self.gauge: self.gauge.SetValue(self.min + (self.max-self.min)*value/100)

    def display(self, s):
        print s
        if self.display_fn:
            self.display_fn(s+"\n")
        else:
            print s

    def new(self, value):
        if self.gauge:
            return ProgressHandler(self.display_fn, self.gauge, self.gauge.GetValue(), self.gauge.GetValue() + (self.max-self.min)*value/100)
        else:
            return ProgressHandler(self.display_fn)

default_progress_handler = ProgressHandler()
