# -*- coding: cp1252 -*-
import string, datetime

PROFIL_INSCRIPTIONS = 1
PROFIL_TRESORIER = 2
PROFIL_BUREAU = 4
PROFIL_SAISIE_PRESENCES = 8
PROFIL_ADMIN = PROFIL_INSCRIPTIONS + PROFIL_TRESORIER + PROFIL_BUREAU + PROFIL_SAISIE_PRESENCES

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

class Periode(object):
    def __init__(self, debut=None, fin=None):
        self.debut = debut
        self.fin = fin
        
    def __str__(self):
        return datestr(self.debut) + ' - ' + datestr(self.fin)

def Select(object, date):
    for o in object:
        date_debut = o.periode.debut
        date_fin = o.periode.fin
        if (date_debut and date >= date_debut and (not date_fin or date <= date_fin)):
          return o
    return None

PRESENT = 0
VACANCES = 1
MALADE = 2
NONINSCRIT = 3 # utilise dans getPresence
SUPPLEMENT = 4 # utilise dans getPresence
class Presence(object):
    def __init__(self, previsionnel = 0, value = PRESENT):
        # 0 = present ; 1 = en vacances ; 2 = malade
        self.previsionnel = previsionnel
        self.value = value
        if (value == 0):
            self.details = [0] * int((heureMaximum - heureOuverture) * 4)
        else:
            self.details = None
        
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

class Bureau:
    def __init__(self):
        self.periode = Periode()
        self.president = ""
        self.vice_president = ""
        self.tresorier = ""
        self.secretaire = ""

class BaremeCAF:
    def __init__(self):
        self.periode = Periode()
        self.plancher = 0
        self.plafond = 4000

changes = []

class Creche(object):
    def __init__(self):
        self.nom = ''
        self.adresse = ''
        self.code_postal = ''
        self.ville = ''
        self.bureaux = []
        self.baremes_caf = []
        self.lastnumcontrat = 0

    def getNumContrat(self):
        self.lastnumcontrat += 1
        return self.lastnumcontrat
    
    def set(self, attr, value):
        exec('self.%s = value' % attr)
        todo = "UPDATE creche SET %s = '%s'" % (attr, str(value))
        changes.append(todo)

class Revenu:
    def __init__(self):
        self.periode = Periode()
        self.valeur = ["", ""]
        self.chomage = [0, 0]
        self.regime = -1

class Parent(object):
    def __init__(self):
        self.prenom = ""
        self.nom = ""
        self.telephone_domicile = ""
        self.telephone_domicile_notes = ""
        self.telephone_portable = ""
        self.telephone_portable_notes = ""
        self.telephone_travail = ""
        self.telephone_travail_notes = ""
        self.email = ""
        self.justificatif_revenu = 0
        self.justificatif_chomage = 0

MODE_CRECHE = 0
MODE_HALTE_GARDERIE = 1

class Inscription:
    def __init__(self, numcontrat):
        self.periode = Periode()
        self.numcontrat = numcontrat
        self.mode = MODE_CRECHE
        self.semaine_type = 5 * [[0, 0, 0]]
        self.fin_periode_essai = None
    
    def GetTotalSemaineType(self):
        total = 0
        for jour in self.semaine_type:
            if jour != [0, 0, 0]:
                total += 10
        return total            

class Frere_Soeur:
    def __init__(self):
        self.prenom = ''
        self.naissance = None
        #self.handicape = 0
        self.entree_creche = None
        self.sortie_creche = None

class Inscrit(object):
    def __init__(self, creche):
        self.prenom = ""
        self.nom = ""
        self.naissance = None
        self.adresse = ""
        self.code_postal = ""
        self.ville = ""
        self.marche = None
        self.photo_filename = None
        self.freres_soeurs = [Frere_Soeur(), Frere_Soeur(), Frere_Soeur(), Frere_Soeur()]
        #self.enfants_a_charge = 1
        #self.enfants_en_creche = 1
        #self.handicape = 0
        self.papa = Parent()
        self.maman = Parent()
        self.revenus_parents = [Revenu()]
        self.inscriptions = [Inscription(creche.getNumContrat())]
        self.presences = { }
        self.reglement_cotisation = 0
        self.reglement_caution = 0
        self.reglement_premier_mois = 0
        self.cheque_depot_garantie = 0
        self.fiche_medicale = 0
        self.signature_ri = 0
        self.signature_permanences = 0
        self.signature_projet_pedagogique = 0
        self.signature_projet_etablissement = 0
        self.signature_contrat_accueil = 0
        self.autorisation_hospitalisation = 0
        self.autorisation_transport = 0
        self.autorisation_image = 0
        self.autorisation_recherche = 0

    def getInscription(self, date):
        return Select(self.inscriptions, date)

    def getInscriptions(self, date_debut, date_fin):
        result = []
        for i in range(len(self.inscriptions)):
          inscription = self.inscriptions[i]
          if (inscription.periode.debut != None):
            try:
              date_debut_periode = inscription.periode.debut
              if (inscription.periode.fin != None):
                date_fin_periode = inscription.periode.fin
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
    
        presence = Presence(1, 1)
        
        inscription = self.getInscription(date)
        
        if inscription != None:
            for i in range(3):
                if inscription.semaine_type[weekday][i] == 1:
                    if presence.value != 0:
                        presence = Presence(1, 0)
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
        presence_contrat = (inscription.semaine_type[date.weekday()] != [0, 0, 0])
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

