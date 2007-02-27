# -*- coding: cp1252 -*-

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
from paques import getPaquesDate

VERSION = 2

PROFIL_INSCRIPTIONS = 1
PROFIL_TRESORIER = 2
PROFIL_BUREAU = 4
PROFIL_SAISIE_PRESENCES = 8
PROFIL_ADMIN = 16
PROFIL_ALL = PROFIL_ADMIN + PROFIL_INSCRIPTIONS + PROFIL_TRESORIER + PROFIL_BUREAU + PROFIL_SAISIE_PRESENCES

days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
months = ["Janvier", u'Février', "Mars", "Avril", "Mai", "Juin", "Juillet", u'Août', "Septembre", "Octobre", "Novembre", u'Décembre']
months_abbrev = ["Janv", u'Fév', "Mars", "Avril", "Mai", "Juin", "Juil", u'Août', "Sept", "Oct", "Nov", u'Déc']
trimestres = ["1er", u'2ème', u'3ème', u'4ème']

today = datetime.date.today()
first_date = max(today - datetime.timedelta(12*30), datetime.date(2005, 1, 1))
last_date = today + datetime.timedelta(6*30)

heureOuverture = 7.75
heureMaximum = 22
heureFermeture = 18.5
tranches = [(heureOuverture, 12, 4), (12, 14, 2), (14, heureMaximum, 4)]

current_directory = "./current"
backups_directory = "./backups"
filename = current_directory + "/petits-potes_" + str(today.year) + ".gtu"
filename = current_directory + "/petits-potes_2005.gtu"

jours_feries = []
for year in range(first_date.year, last_date.year + 1):
    jours_feries.append(datetime.date(year, 1, 1))
    jours_feries.append(datetime.date(year, 5, 1))
    jours_feries.append(datetime.date(year, 5, 8))
    jours_feries.append(datetime.date(year, 7, 14))
    jours_feries.append(datetime.date(year, 11, 1))
    jours_feries.append(datetime.date(year, 11, 11))
    jours_feries.append(datetime.date(year, 12, 25))
    paques = getPaquesDate(year)
    jours_feries.append(paques + datetime.timedelta(1))
    jours_feries.append(paques + datetime.timedelta(39))

def getfirstmonday():
    first_monday = first_date
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(1)
    return first_monday
    
def getNumeroSemaine(date):
    return int((date - datetime.date(date.year, 1, 1)).days / 7) + 1

def datestr(date):
  if date == None:
    return ''
  else:
    return '%.02d/%.02d/%.04d' % (date.day, date.month, date.year)

def periodestr(o):      
    return datestr(o.debut) + ' - ' + datestr(o.fin)

def Select(object, date):
    for o in object:
        if o.debut and date >= o.debut and (not o.fin or date <= o.fin):
            return o
    return None

PRESENT = 0
VACANCES = 1
MALADE = 2
NONINSCRIT = 3 # utilise dans getPresence
SUPPLEMENT = 4 # utilise dans getPresence

from sqlinterface import connection

class Presence(object):
    def __init__(self, inscrit, date, previsionnel=0, value=PRESENT, creation=True):
        self.idx = None
        self.inscrit_idx = inscrit.idx
        self.date = date
        self.previsionnel = previsionnel
        self.value = value
        if value == PRESENT:
            self.details = [0] * int((heureMaximum - heureOuverture) * 4)
        else:
            self.details = None
        if creation:
            self.create()
    
    def create(self):
        print 'nouvelle presence'
        result = connection.execute('INSERT INTO PRESENCES (idx, inscrit, date, previsionnel, value, details) VALUES (NULL,?,?,?,?,?)', (self.inscrit_idx, self.date, self.previsionnel, self.value, str(self.details)))
        self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression presence'
        connection.execute('DELETE FROM PRESENCES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name == 'details':
            value = str(value)
        if name in ['date', 'previsionnel', 'value', 'details'] and self.idx:
            print 'update', name
            connection.execute('UPDATE PRESENCES SET %s=? WHERE idx=?' % name, (value, self.idx))
        
    def Total(self): # TODO 10/0
        total = 0
        if (self.value == 0):
            # Total reel ...
            #for i in range(int((heureMaximum - heureOuverture) * 4)):
            #    if self.details[i]:
            #        total += 0.25
            
            # Total en 4, 2, 4
#            for (debut, fin, valeur) in tranches:
#              for i in range(int((debut - heureOuverture) * 4), int((fin - heureOuverture) * 4)):
#                if self.details[i]:
#                  total += valeur
#                  break

            # Total en 0 / 10
            for (debut, fin, valeur) in tranches:
              for i in range(int((debut - heureOuverture) * 4), int((fin - heureOuverture) * 4)):
                if self.details[i]:
                  total = 10

        return total
    
    def isPresentDuringTranche(self, tranche):
        if (self.value == 0):
            (debut, fin, valeur) = tranches[tranche]
            for i in range(int((debut - heureOuverture) * 4), int((fin - heureOuverture) * 4)):
                if self.details[i]:
                  return True
        return False            

class Bureau(object):
    def __init__(self, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.president = None
        self.vice_president = None
        self.tresorier = None
        self.secretaire = None
        
        if creation:
            print 'nouveau bureau'
            result = connection.execute('INSERT INTO BUREAUX (idx, debut, fin, president, vice_president, tresorier, secretaire) VALUES (NULL,?,?,?,?,?,?)', (self.debut, self.fin, None, None, None, None))
            self.idx = result.lastrowid
   
    def delete(self):
        print 'suppression bureau'
        connection.execute('DELETE FROM BUREAUX WHERE idx=?', (self.idx,))
        
    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'president', 'vice_president', 'tresorier', 'secretaire'] and self.idx:
            if name in ['president', 'vice_president', 'tresorier', 'secretaire'] and value is not None:
                value = value.idx
            print 'update', name
            connection.execute('UPDATE BUREAUX SET %s=? WHERE idx=?' % name, (value, self.idx))

class BaremeCAF(object):
    def __init__(self, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.plancher = 0
        self.plafond = 4000

        if creation:
            print 'nouveau bareme caf'
            result = connection.execute('INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)', (self.debut, self.fin, self.plancher, self.plafond))
            self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression bareme caf'
        connection.execute('DELETE FROM BAREMESCAF WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'plancher', 'plafond'] and self.idx:
            print 'update', name
            connection.execute('UPDATE BAREMESCAF SET %s=? WHERE idx=?' % name, (value, self.idx))

class User(object):
    def __init__(self, creation=True):
        self.idx = None
        self.login = "anonymous"
        self.password = "anonymous"
        self.profile = 0

        if creation:
            print 'nouveau user'
            result = connection.execute('INSERT INTO USERS (idx, login, password, profile) VALUES (NULL,?,?,?)', (self.login, self.password, self.profile))
            self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression user'
        connection.execute('DELETE FROM USERS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['login', 'password', 'profile'] and self.idx:
            print 'update', name
            connection.execute('UPDATE USERS SET %s=? WHERE idx=?' % name, (value, self.idx))

class Creche(object): 
    def __init__(self, creation=True):
        self.idx = None
        self.nom = ''
        self.adresse = ''
        self.code_postal = ''
        self.ville = ''
        self.users = []
        self.bureaux = []
        self.baremes_caf = []
        self.inscrits = []
        self.server_url = ''
        
        if creation:
            print 'nouvelle creche'
            result = connection.execute('INSERT INTO CRECHE(idx, nom, adresse, code_postal, ville, server_url) VALUES (NULL,?,?,?,?)', (self.nom, self.adresse, self.code_postal, self.ville, self.server_url))
            self.idx = result.lastrowid
            self.bureaux.append(Bureau(self))
            self.baremes_caf.append(BaremeCAF())
       
    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['nom', 'adresse', 'code_postal', 'ville', 'server_url'] and self.idx:
            print 'update', name, value
            connection.execute('UPDATE CRECHE SET %s=?' % name, (value,))
      
class Revenu(object):
    def __init__(self, parent, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.revenu = ''
        self.chomage = False
        self.regime = 0

        if creation:
            print 'nouveau revenu'
            result = connection.execute('INSERT INTO REVENUS (idx, parent, debut, fin, revenu, chomage, regime) VALUES(NULL,?,?,?,?,?,?)', (parent.idx, self.debut, self.fin, self.revenu, self.chomage, self.regime))
            self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression revenu'
        connection.execute('DELETE FROM REVENUS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'revenu', 'chomage', 'regime'] and self.idx:
            print 'update', name
            connection.execute('UPDATE REVENUS SET %s=? WHERE idx=?' % name, (value, self.idx))

class Parent(object):
    def __init__(self, inscrit, creation=True):
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.telephone_domicile = ""
        self.telephone_domicile_notes = ""
        self.telephone_portable = ""
        self.telephone_portable_notes = ""
        self.telephone_travail = ""
        self.telephone_travail_notes = ""
        self.email = ""
        self.revenus = []
        # self.justificatif_revenu = 0
        # self.justificatif_chomage = 0

        if creation:
            print 'nouveau parent'
            result = connection.execute('INSERT INTO PARENTS (idx, inscrit, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email) VALUES(NULL,?,?,?,?,?,?,?,?,?,?)', (inscrit.idx, self.prenom, self.nom, self.telephone_domicile, self.telephone_domicile_notes, self.telephone_portable, self.telephone_portable_notes, self.telephone_travail, self.telephone_travail_notes, self.email))
            self.idx = result.lastrowid
            self.revenus.append(Revenu(self))
        
    def delete(self):
        print 'suppression parent'
        connection.execute('DELETE FROM PARENTS WHERE idx=?', (self.idx,))
        for revenu in self.revenus:
            revenu.delete()

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'nom', 'telephone_domicile', 'telephone_domicile_notes', 'telephone_portable', 'telephone_portable_notes', 'telephone_travail', 'telephone_travail_notes', 'email'] and self.idx:
            print 'update', name
            connection.execute('UPDATE PARENTS SET %s=? WHERE idx=?' % name, (value, self.idx))

MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1

class Inscription(object):
    def __init__(self, inscrit, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.mode = MODE_CRECHE
        self.periode_reference = 5 * [[0, 0, 0]]
        self.fin_periode_essai = None

        if creation:
            print 'nouvelle inscription'
            result = connection.execute('INSERT INTO INSCRIPTIONS (idx, inscrit, debut, fin, mode, periode_reference, fin_periode_essai) VALUES(NULL,?,?,?,?,?,?)', (inscrit.idx, self.debut, self.fin, self.mode, str(self.periode_reference), self.fin_periode_essai))
            self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression inscription'
        connection.execute('DELETE FROM INSCRIPTIONS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name == 'periode_reference':
            value = str(value)
        if name in ['debut', 'fin', 'mode', 'fin_periode_essai', 'periode_reference'] and self.idx:
            print 'update', name
            connection.execute('UPDATE INSCRIPTIONS SET %s=? WHERE idx=?' % name, (value, self.idx))

    def GetTotalSemaineType(self): # TODO
        total = 0
        for jour in self.periode_reference:
            if jour != [0, 0, 0]:
                total += 10
        return total            

class Frere_Soeur(object):
    def __init__(self, inscrit, creation=True):
        self.idx = None
        self.prenom = ''
        self.naissance = None
        # self.handicape = 0
        self.entree = None
        self.sortie = None

        if creation:
            print 'nouveau frere / soeur'
            result = connection.execute('INSERT INTO FRATRIES (idx, inscrit, prenom, naissance, entree, sortie) VALUES(NULL,?,?,?,?,?)', (inscrit.idx, self.prenom, self.naissance, self.entree, self.sortie))
            self.idx = result.lastrowid
        
    def delete(self):
        print 'suppression frere / soeur'
        connection.execute('DELETE FROM FRATRIES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'naissance', 'entree', 'sortie'] and self.idx:
            print 'update', name
            connection.execute('UPDATE FRATRIES SET %s=? WHERE idx=?' % name, (value, self.idx))

class Inscrit(object):
    def __init__(self, creation=True):
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.naissance = None
        self.adresse = ""
        self.code_postal = ""
        self.ville = ""
        self.marche = None
        self.photo = None
        self.freres_soeurs = []
        self.papa = None
        self.maman = None
        self.inscriptions = []
        #self.handicape = 0
        self.presences = { }
#        self.reglement_cotisation = 0
#        self.reglement_caution = 0
#        self.reglement_premier_mois = 0
#        self.cheque_depot_garantie = 0
#        self.fiche_medicale = 0
#        self.signature_ri = 0
#        self.signature_permanences = 0
#        self.signature_projet_pedagogique = 0
#        self.signature_projet_etablissement = 0
#        self.signature_contrat_accueil = 0
#        self.autorisation_hospitalisation = 0
#        self.autorisation_transport = 0
#        self.autorisation_image = 0
#        self.autorisation_recherche = 0

        if creation:
            print 'nouvel inscrit'
            result = connection.execute('INSERT INTO INSCRITS (idx, prenom, nom, naissance, adresse, code_postal, ville, marche, photo) VALUES(NULL,?,?,?,?,?,?,?,?)', (self.prenom, self.nom, self.naissance, self.adresse, self.code_postal, self.ville, self.marche, self.photo))
            self.idx = result.lastrowid
            self.papa = Parent(self)
            self.maman = Parent(self)
            self.inscriptions.append(Inscription(self))
        
    def delete(self):
        print 'suppression inscrit'
        connection.execute('DELETE FROM INSCRITS WHERE idx=?', (self.idx,))
        for obj in [self.papa, self.maman] + self.freres_soeurs + self.inscriptions + self.presences.values():
            obj.delete()

    def __setattr__(self, name, value):
        if name in self.__dict__:
            old_value = self.__dict__[name]
        else:
            old_value = '-'
        self.__dict__[name] = value
        if name == 'photo' and value:
            value = binascii.b2a_base64(value)
        if name in ['prenom', 'nom', 'naissance', 'adresse', 'code_postal', 'ville', 'marche', 'photo'] and self.idx:
            print 'update', name, (old_value, value)
            connection.execute('UPDATE INSCRITS SET %s=? WHERE idx=?' % name, (value, self.idx))

    def getInscription(self, date):
        return Select(self.inscriptions, date)

    def getInscriptions(self, date_debut, date_fin):
        result = []
        for i, inscription in enumerate(self.inscriptions):
          if inscription.debut:
            try:
              date_debut_periode = inscription.debut
              if inscription.fin:
                date_fin_periode = inscription.fin
              else:
                date_fin_periode = datetime.date.max
              if ((date_debut >= date_debut_periode and date_debut <= date_fin_periode) or 
                  (date_fin >= date_debut_periode and date_fin <= date_fin_periode) or
                  (date_debut < date_debut_periode and date_fin > date_fin_periode)):
                  result.append(inscription)
            except:
              pass
            
        return result

    def getPresenceFromSemaineType(self, date):
        # retourne toujours du previsionnel
        weekday = date.weekday()
        if (weekday > 4):
          raise 'la date doit etre un jour de semaine'
    
        presence = Presence(self, date, 1, 1, creation=False)
        
        inscription = self.getInscription(date)
        
        if inscription != None:
            for i in range(3):
                if inscription.periode_reference[weekday][i] == 1:
                    if presence.value != 0:
                        presence = Presence(self, date, 1, 0, creation=False)
                    if i == 0:
                        debut = int((8-heureOuverture) * 4)
                        fin = int((12-heureOuverture) * 4)
                    elif i == 1:
                        debut = int((12-heureOuverture) * 4)
                        fin = int((14-heureOuverture) * 4)
                    else:
                        debut = int((14-heureOuverture) * 4)
                        fin = int((18-heureOuverture) * 4)
                    for i in range(debut, fin):
                        presence.details[i] = 1
    
        return presence

    def getPresence(self, date):
        inscription = self.getInscription(date)
        if inscription is None or date.weekday() > 4:
            return NONINSCRIT
        presence_contrat = (inscription.periode_reference[date.weekday()] != [0, 0, 0])
        if date in self.presences:
            presence = self.presences[date]
            if presence.value == MALADE:
                return MALADE
            elif presence.value == VACANCES:
                if presence_contrat:
                    return VACANCES
                else:
                    return NONINSCRIT
            else: # PRESENT
                if presence_contrat:
                    return PRESENT
                else:
                    return SUPPLEMENT
        else:
            if presence_contrat:
                return PRESENT
            else:
                return NONINSCRIT
            
#    def getTotalHeuresMois(self, annee, mois, mode_accueil): # heures facturees
#        total = 0
#        previsionnel = 0
#        
#        date = datetime.date(annee, mois, 1)
#        while (date.month == mois):
#          if (date.weekday() < 5):
#            inscription = self.getInscription(date)
#            if (inscription != None and inscription.mode == mode_accueil):
#              presence_st = self.getPresenceFromSemaineType(date)
#              total_jour = presence_st.Total()              
#              total += total_jour
#              if date in self.presences:
#                presence = self.presences[date]
#                if total_jour == 0 and presence.value == 1:
#                    total += presence.Total() 
#                if presence.previsionnel == 1 and presence.value == 0:
#                    previsionnel = 1
#              else:
#                if (presence_st.value == 0):
#                  previsionnel = 1              
#            
#          date += datetime.timedelta(1)
#        return total, previsionnel
    
    def getTotalHeuresMois(self, annee, mois, mode_accueil): # heures facturees
        total = 0
        previsionnel = 0
        
        if mode_accueil == 0: # Creche
            total_semaine_type = 0
            
            date = datetime.date(annee, mois, 1)
            while (date.month == mois):
              if (date.weekday() < 5):
                inscription = self.getInscription(date)
                if (inscription != None and inscription.mode == mode_accueil):
                  if total_semaine_type  < inscription.GetTotalSemaineType():
                      total_semaine_type = inscription.GetTotalSemaineType()
                  presence_st = self.getPresenceFromSemaineType(date)
                  total_jour_st = presence_st.Total()
                  if date in self.presences:
                    presence = self.presences[date]
                    if total_jour_st == 0 and presence.Total() > 0:                    
                        total += presence.Total()
                    if presence.previsionnel == 1 and presence.value == 0:
                        previsionnel = 1
                  else:
                    if (presence_st.value == 0):
                      previsionnel = 1              
                
              date += datetime.timedelta(1)
            if mois == 8: # mois d'aout
                total += 2 * total_semaine_type
            elif mois == 12: # mois de decembre
                total += 3 * total_semaine_type
            else:
                total += 4 * total_semaine_type
        else: # Halte-garderie
            date = datetime.date(annee, mois, 1)
            while (date.month == mois):
              if (date.weekday() < 5):
                inscription = self.getInscription(date)
                if (inscription != None and inscription.mode == mode_accueil):
                  if date in self.presences:
                    presence = self.presences[date]  
                  else:
                    presence = self.getPresenceFromSemaineType(date)
                    
                  total += presence.Total()
                  
                  if presence.previsionnel == 1 and presence.value == 0:
                    previsionnel = 1

              date += datetime.timedelta(1)
        return total, previsionnel

def GetInscritId(inscrit, inscrits):
    for i in inscrits:
        if (inscrit != i and inscrit.prenom == i.prenom):
            return inscrit.prenom + " " + inscrit.nom
    return inscrit.prenom
