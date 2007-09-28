# -*- coding: utf-8 -*-

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

import datetime, binascii
from constants import *
from parameters import *

def default_progress_handler(msg=None, count=None, max=None):
    if msg: print msg
    return default_progress_handler

def getfirstmonday():
    first_monday = first_date
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(1)
    return first_monday

def getNumeroSemaine(date):
    return int((date - datetime.date(date.year, 1, 1)).days / 7) + 1

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

def getDateStr(date):
    if date.day == 1:
        return "1er %s %d" % (months[date.month-1].lower(), date.year)
    else:
        return "%d %s %d" % (date.day, months[date.month-1].lower(), date.year)

def getInitialesPrenom(person):
    for char in ('-', ' '):
        if char in person.prenom:
            parts = person.prenom.split(char)
            return ''.join([part[0] for part in parts])
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
  if date == None:
    return ''
  else:
    return '%.02d/%.02d/%.04d' % (date.day, date.month, date.year)

def periodestr(o):      
    return date2str(o.debut) + ' - ' + date2str(o.fin)

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

def getPleinTempsIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                periode_reference = inscription.periode_reference
                for jour in periode_reference:
                    if jour != [1, 1, 1]:
                        break
                else:
                    result.append(i)
    return result

def getMiTempsIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                periode_reference = inscription.periode_reference
                nb_jours = 0
                for jour in periode_reference:
                    if jour == [1, 1, 1]:
                        nb_jours += 1
                if nb_jours != 5:
                    result.append(i)
    return result

def getCrecheIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) > 0:
            inscription = inscriptions[0]
            if inscription.mode == 0:
                result.append(i)
    return result

def getHalteGarderieIndexes(date_debut, date_fin):
    result = []
    for i, inscrit in enumerate(creche.inscrits):
        inscriptions = inscrit.getInscriptions(date_debut, date_fin)
        if len(inscriptions) and inscriptions[0].mode == 1:
            result.append(i)
    return result

def getAdaptationIndexes(date_debut, date_fin):
    result = []
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
    result = []
    for i in range(len(indexes)):
        inscrit = creche.inscrits[indexes[i]]
        #print inscrit.prenom
        for inscription in inscrit.inscriptions:
            if ((inscription.fin == None or inscription.fin >= debut) and (inscription.debut != None and inscription.debut <= fin)):
                result.append(indexes[i])
                break

    return result

def decodeErrors(errors):
    message = ""
    for error in errors:
        message += '\n'+error[0].prenom+' :\n  '
        message += '\n  '.join(error[1])
    return message
