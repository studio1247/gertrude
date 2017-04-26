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

import binascii
import bcrypt
import wx
from functions import *
from cotisation import GetDateRevenus


class SQLObject(object):
    def delete(self):
        print 'suppression %s (table=%s, idx=%d)' % (self.__class__.__name__, self.table, self.idx)
        sql_connection.execute('DELETE FROM %s WHERE idx=?' % self.table, (self.idx,))
        self.idx = None


class Day(object):
    table = None
    reference = None
    exclusive = False
    options = 0
    GetDynamicText = None
    table_commentaires = None

    def __init__(self):
        self.activites = {}
        self.activites_sans_horaires = {}
        self.last_heures = None
        self.readonly = False
        self.commentaire = ""
        self.commentaire_idx = None

    def SetActivity(self, start, end, value):
        self.last_heures = None
        if self.exclusive:
            for a, b, v in self.activites.keys():
                if v == value:
                    if start <= b + 1 and end >= a - 1:
                        start, end = min(a, start), max(b, end)
                        self.RemoveActivity(a, b, v)
            self.InsertActivity(start, end, value)
        else:
            activity_value = value & ~PREVISIONNEL
            if value == activity_value:
                self.Confirm()
            activity = creche.activites[activity_value]
            for a, b, v in self.activites.keys():
                if v < 0:
                    self.RemoveActivity(a, b, v)
                elif value == v:
                    if start <= b + 1 and end >= a - 1:
                        start, end = min(a, start), max(b, end)
                        self.RemoveActivity(a, b, v)
                elif activity.mode == MODE_LIBERE_PLACE and start < b and end > a:
                    self.RemoveActivity(a, b, v)
                    if a < start:
                        self.InsertActivity(a, start, v)
                    if b > end:
                        self.InsertActivity(end, b, v)
                elif creche.activites[v & ~(PREVISIONNEL + CLOTURE)].mode == MODE_LIBERE_PLACE and start < b and end > a:
                    self.RemoveActivity(a, b, v)
                    if a < start:
                        self.InsertActivity(a, start, v)
                    if b > end:
                        self.InsertActivity(end, b, v)
            self.InsertActivity(start, end, value)
            if activity_value != 0 and activity.mode in (MODE_NORMAL, MODE_PRESENCE_NON_FACTUREE):
                self.SetActivity(start, end, value & PREVISIONNEL)

    def ClearActivity(self, start, end, value):
        self.last_heures = None
        if self.exclusive:
            for a, b, v in self.activites.keys():
                if start <= b + 1 and end >= a - 1:
                    self.RemoveActivity(a, b, v)
                    if start > a:
                        self.InsertActivity(a, start, v)
                    if end < b:
                        self.InsertActivity(end, b, v)
        else:
            activity_value = value & ~PREVISIONNEL
            if value == activity_value:
                self.Confirm()
            for a, b, v in self.activites.keys():
                if value == v:
                    if start <= b + 1 and end >= a - 1:
                        self.RemoveActivity(a, b, v)
                        if start > a:
                            self.InsertActivity(a, start, v)
                        if end < b:
                            self.InsertActivity(end, b, v)
                elif activity_value == 0 and (not v & CLOTURE) and creche.activites[v & ~PREVISIONNEL].mode == MODE_NORMAL and start < b and end > a:
                    self.RemoveActivity(a, b, v)
                    if a < start:
                        self.InsertActivity(a, start, v)
                    if b > end:
                        self.InsertActivity(end, b, v)

    def InsertActivity(self, start, end, value):
        self.AddActivity(start, end, value, None)

    def AddActivity(self, start, end, value, idx):
        if start is None and end is None:
            self.activites_sans_horaires[value] = idx
        else:
            self.activites[(start, end, value)] = idx

    def RemoveActivities(self, activity):
        for start, end, value in self.activites.keys():
            if activity == value:
                self.RemoveActivity(start, end, value)
        for key in self.activites_sans_horaires.keys():
            if activity == key:
                self.RemoveActivity(None, None, key)

    def RemoveAllActivities(self):
        for start, end, value in self.activites.keys():
            if value < 0 or not value & CLOTURE:
                self.RemoveActivity(start, end, value)
        for key in self.activites_sans_horaires.keys():
            if key < 0 or not key & CLOTURE:
                self.RemoveActivity(None, None, key)

    def Backup(self):
        backup = []
        for start, end, value in self.activites:
            if value < 0 or not value & CLOTURE:
                backup.append((start, end, value))
        for key in self.activites_sans_horaires:
            if key < 0 or not key & CLOTURE:
                backup.append((None, None, key))
        return backup

    def Restore(self, backup):
        self.RemoveAllActivities()
        for start, end, value in backup:
            self.AddActivity(start, end, value, None)
        self.Save()

    def Confirm(self):
        self.last_heures = None
        for start, end, value in self.activites.keys():
            if value & PREVISIONNEL and not value & CLOTURE:
                self.RemoveActivity(start, end, value)
                value -= PREVISIONNEL
                self.InsertActivity(start, end, value)
        for value in self.activites_sans_horaires.keys():
            if value & PREVISIONNEL and not value & CLOTURE:
                self.RemoveActivity(None, None, value)
                value -= PREVISIONNEL
                self.InsertActivity(None, None, value)
        self.Save()

    def Save(self):
        self.last_heures = None
        for start, end, value in self.activites.keys():
            if self.activites[(start, end, value)] == None:
                self.InsertActivity(start, end, value)
        for value in self.activites_sans_horaires.keys():
            if self.activites_sans_horaires[value] == None:
                self.InsertActivity(None, None, value)

    def CloturePrevisionnel(self):
        for start, end, value in self.activites.keys() + self.activites_sans_horaires.keys():
            if value >= 0:
                self.InsertActivity(start, end, value | PREVISIONNEL | CLOTURE)

    def HasPrevisionnelCloture(self):
        for start, end, value in self.activites.keys() + self.activites_sans_horaires.keys():
            if value >= PREVISIONNEL + CLOTURE:
                return True
        return False

    def RestorePrevisionnelCloture(self, previsionnel=True):
        self.last_heures = None
        self.RemoveAllActivities()
        for start, end, value in self.activites.keys() + self.activites_sans_horaires.keys():
            if previsionnel:
                self.InsertActivity(start, end, value - CLOTURE)
            else:
                self.InsertActivity(start, end, value - PREVISIONNEL - CLOTURE)

    def SetState(self, state):
        self.last_heures = None
        self.RemoveAllActivities()
        for debut, fin in creche.GetPlagesOuvertureArray():
            self.InsertActivity(debut, fin, state)

    def GetState(self):
        state = ABSENT
        for start, end, value in self.activites:
            if value < 0:
                return value
            elif value == 0:
                state = PRESENT
            elif value == PREVISIONNEL:
                return PRESENT | PREVISIONNEL
        return state

    def GetStateIcon(self):
        state = self.GetState()
        if state > 0:
            activities_state = state & ~(PRESENT | PREVISIONNEL)
            if activities_state:
                state &= ~activities_state
                state |= PRESENT
        elif state == VACANCES:
            try:
                if self.inscription.IsNombreSemainesCongesAtteint(self.key):
                    state = CONGES_DEPASSEMENT
            except:
                pass
        return state

    def GetNombreHeures(self, facturation=False, adaptation=False):
        #        if self.last_heures is not None:
        #            return self.last_heures
        self.last_heures = 0.0
        for start, end, value in self.activites:
            if value < 0:
                self.last_heures = 0.0
                return self.last_heures
            elif value == 0 or value == PREVISIONNEL:
                if facturation and adaptation:
                    mode_arrondi = creche.arrondi_facturation_periode_adaptation
                elif facturation:
                    mode_arrondi = creche.arrondi_facturation
                else:
                    mode_arrondi = eval('creche.' + self.mode_arrondi)
                self.last_heures += 5.0 * GetDureeArrondie(mode_arrondi, start, end)
        if creche.mode_facturation == FACTURATION_FORFAIT_10H:
            self.last_heures = 10.0 * (self.last_heures > 0)
        else:
            self.last_heures /= 60
        return self.last_heures

    def GetHeureArrivee(self, activite=0):
        for start, end, value in self.activites:
            if value & ~(PREVISIONNEL + CLOTURE) == activite:
                return GetHeureString(start)
        return ''

    def GetHeureDepart(self, activite=0):
        for start, end, value in self.activites:
            if value & ~(PREVISIONNEL + CLOTURE) == activite:
                return GetHeureString(end)
        return ''

    def GetHeureArriveeDepart(self, activite=0):
        for start, end, value in self.activites:
            if value & ~(PREVISIONNEL + CLOTURE) == activite:
                return u"de %s à %s" % (GetHeureString(start), GetHeureString(end))
        return ''

    def Copy(self, day, previsionnel=True):
        self.last_heures = None
        self.exclusive = day.exclusive
        self.reference = day.reference
        self.RemoveAllActivities()
        for start, end, value in day.activites:
            if previsionnel:
                self.activites[(start, end, value | PREVISIONNEL)] = None
            else:
                self.activites[(start, end, value)] = None
        for key in day.activites_sans_horaires:
            self.activites_sans_horaires[key] = None

    def GetExtraActivites(self):
        result = set()
        for key in self.activites.keys():
            value = key[2]
            if value > 0:
                result.add(value & ~PREVISIONNEL)
        for value in self.activites_sans_horaires.keys():
            result.add(value)
        if self.activites:
            for key in creche.activites:
                activite = creche.activites[key]
                if activite.mode == MODE_SYSTEMATIQUE_SANS_HORAIRES:
                    result.add(key)
        return result

    def GetPlageHoraire(self):
        debut, fin = None, None
        for start, end, value in self.activites.keys():
            if not debut or start < debut:
                debut = start
            if not fin or end > fin:
                fin = end
        return debut, fin

    def GetListeActivitesParMode(self, mode):
        result = []
        for start, end, value in self.activites:
            if value in creche.activites:
                activite = creche.activites[value]
                if activite.mode == mode:
                    result.append((start, end))
        return result

    def GetTotalActivitesParMode(self, mode, arrondi=SANS_ARRONDI):
        result = 0
        liste = self.GetListeActivitesParMode(mode)
        for start, end in liste:
            result += (5 * GetDureeArrondie(arrondi, start, end))
        return float(result) / 60

    def GetTotalActivitesPresenceNonFacturee(self):
        return self.GetTotalActivitesParMode(MODE_PRESENCE_NON_FACTUREE, eval('creche.' + self.mode_arrondi))

    def GetTotalPermanences(self):
        return self.GetTotalActivitesParMode(MODE_PERMANENCE)

    def delete(self):
        print 'suppression jour'
        for start, end, value in self.activites.keys():
            self.RemoveActivity(start, end, value)
        for value in self.activites_sans_horaires.keys():
            self.RemoveActivity(None, None, value)

    def RemoveActivity(self, start, end, value):
        if start is None and end is None:
            if self.activites_sans_horaires[value] is not None:
                print u'delete %r (table=%s, idx=%d)' % (self.nom, self.table, self.activites_sans_horaires[value])
                sql_connection.execute('DELETE FROM %s WHERE idx=?' % self.table,
                                       (self.activites_sans_horaires[value],))
            del self.activites_sans_horaires[value]
        else:
            if self.activites[(start, end, value)] is not None:
                print u'delete %r (table=%s, idx=%d)' % (self.nom, self.table, self.activites[(start, end, value)])
                sql_connection.execute('DELETE FROM %s WHERE idx=?' % self.table,
                                       (self.activites[(start, end, value)],))
            del self.activites[(start, end, value)]

    def GetActivity(self, heure):
        if not isinstance(heure, int):
            heure = int(round(heure * 12))
        for start, end, value in self.activites:
            if start <= heure < end:
                return self.activites[(start, end, value)]
        else:
            return None


class JourneeCapacite(Day):
    table = "CAPACITE"
    nom = u"capacité"
    exclusive = True

    def __init__(self, jour):
        Day.__init__(self)
        self.jour = jour
        self.label = days[jour]
        self.sublabel = ""
        self.insert = None
        self.mode_arrondi = 'arrondi_heures'
        self.summary = None
        self.salarie = None

    def InsertActivity(self, start, end, value):
        print u'nouvelle tranche horaire %s de capacité (%r, %r %d)' % (self.label, start, end, value),
        result = sql_connection.execute('INSERT INTO CAPACITE (idx, value, debut, fin, jour) VALUES (NULL,?,?,?,?)',
                                        (value, start, end, self.jour))
        idx = result.lastrowid
        self.activites[(start, end, value)] = idx
        print idx


class JourneeReferenceInscription(Day):
    table = "REF_ACTIVITIES"
    nom = u"activité de référence"

    def __init__(self, inscription, day):
        Day.__init__(self)
        self.inscription = inscription
        self.day = day
        self.mode_arrondi = 'arrondi_heures'

    def InsertActivity(self, start, end, value):
        print 'nouvelle activite de reference (%r, %r %d)' % (start, end, value),
        result = sql_connection.execute(
            'INSERT INTO REF_ACTIVITIES (idx, reference, day, value, debut, fin) VALUES (NULL,?,?,?,?,?)',
            (self.inscription.idx, self.day, value, start, end))
        idx = result.lastrowid
        if start is None and end is None:
            self.activites_sans_horaires[value] = idx
        else:
            self.activites[(start, end, value)] = idx
        print idx


class JourneeReferenceSalarie(Day):
    table = "REF_JOURNEES_SALARIES"
    nom = u"journée de référence (salarié)"

    def __init__(self, contrat, day):
        Day.__init__(self)
        self.contrat = contrat
        self.day = day
        self.mode_arrondi = 'arrondi_heures_salaries'

    def InsertActivity(self, start, end, value):
        print 'salarie : nouvelle activite de reference (%r, %r %d)' % (start, end, value),
        result = sql_connection.execute(
            'INSERT INTO REF_JOURNEES_SALARIES (idx, reference, day, value, debut, fin) VALUES (NULL,?,?,?,?,?)',
            (self.contrat.idx, self.day, value, start, end))
        idx = result.lastrowid
        if start is None and end is None:
            self.activites_sans_horaires[value] = idx
        else:
            self.activites[(start, end, value)] = idx
        print idx


class WeekActivity(SQLObject):
    table = "PLANNING_HEBDOMADAIRE"
    nom = u"semaine"

    def __init__(self, inscrit, date, activity, value, idx=None):
        self.idx = None
        self.inscrit = inscrit
        self.date = date
        self.activity = activity
        self.value = value
        if idx is None:
            self.create()
        else:
            self.idx = idx

    def create(self):
        print 'nouvelle activite semaine', self.inscrit.idx, self.date, self.activity, self.value
        result = sql_connection.execute(
            'INSERT INTO PLANNING_HEBDOMADAIRE (idx, inscrit, date, activity, value) VALUES (NULL,?,?,?,?)',
            (self.inscrit.idx, self.date, self.activity, self.value))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ('date', 'activity', 'value') and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE PLANNING_HEBDOMADAIRE SET %s=? WHERE idx=?' % name, (value, self.idx))


class WeekPlanning(object):
    def __init__(self, inscrit, date):
        self.inscrit = inscrit
        self.date = date
        self.activities = {}

    def SetActivity(self, activity, value, idx=None):
        if activity not in self.activities:
            self.activities[activity] = WeekActivity(self.inscrit, self.date, activity, value, idx)
        else:
            self.activities[activity].value = value


class Journee(Day):
    table = "ACTIVITES"
    nom = u"activité"

    def __init__(self, inscrit, date, reference=None):
        Day.__init__(self)
        self.inscrit_idx = inscrit.idx
        self.date = date
        self.previsionnel = 0
        self.mode_arrondi = 'arrondi_heures'
        if reference:
            self.Copy(reference, creche.presences_previsionnelles)

    def SetCommentaire(self, commentaire):
        self.commentaire = commentaire
        if sql_connection:
            if self.commentaire_idx is None:
                print 'nouveau commentaire'
                result = sql_connection.execute('INSERT INTO COMMENTAIRES (idx, inscrit, date, commentaire) VALUES (NULL,?,?,?)', (self.inscrit_idx, self.date, commentaire))
                self.commentaire_idx = result.lastrowid
            else:
                print 'update commentaire'
                sql_connection.execute('UPDATE COMMENTAIRES SET commentaire=? WHERE idx=?', (commentaire, self.commentaire_idx))

    def InsertActivity(self, start, end, value):
        if sql_connection:
            print 'nouvelle activite %d (%r, %r, %d)' % (self.inscrit_idx, start, end, value),
            result = sql_connection.execute(
                'INSERT INTO ACTIVITES (idx, inscrit, date, value, debut, fin) VALUES (NULL,?,?,?,?,?)',
                (self.inscrit_idx, self.date, value, start, end))
            idx = result.lastrowid
            print idx
        else:
            idx = None
        if start is None and end is None:
            self.activites_sans_horaires[value] = idx
        else:
            self.activites[(start, end, value)] = idx
        return idx


class JourneeSalarie(Day):
    table = "ACTIVITES_SALARIES"
    nom = u"activité salarié"

    def __init__(self, salarie, date, reference=None):
        Day.__init__(self)
        self.salarie_idx = salarie.idx
        self.date = date
        self.previsionnel = 0
        self.mode_arrondi = 'arrondi_heures_salaries'
        if reference:
            self.Copy(reference, creche.presences_previsionnelles)

    def SetCommentaire(self, commentaire):
        self.commentaire = commentaire
        if sql_connection:
            if self.commentaire_idx is None:
                print 'nouveau commentaire'
                result = sql_connection.execute(
                    'INSERT INTO COMMENTAIRES_SALARIES (idx, salarie, date, commentaire) VALUES (NULL,?,?,?)',
                    (self.salarie_idx, self.date, commentaire))
                self.commentaire_idx = result.lastrowid
            else:
                print 'update commentaire'
                sql_connection.execute('UPDATE COMMENTAIRES_SALARIES SET commentaire=? WHERE idx=?',
                                                (commentaire, self.commentaire_idx))

    def InsertActivity(self, start, end, value):
        if sql_connection:
            print 'nouvelle activite (%r, %r, %d)' % (start, end, value),
            result = sql_connection.execute(
                'INSERT INTO ACTIVITES_SALARIES (idx, salarie, date, value, debut, fin) VALUES (NULL,?,?,?,?,?)',
                (self.salarie_idx, self.date, value, start, end))
            idx = result.lastrowid
            print idx
        else:
            idx = None
        if start is None and end is None:
            self.activites_sans_horaires[value] = idx
        else:
            self.activites[(start, end, value)] = idx
        return idx


class Bureau(SQLObject):
    table = "BUREAUX"

    def __init__(self, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.president = ""
        self.vice_president = ""
        self.tresorier = ""
        self.secretaire = ""
        self.directeur = ""
        self.gerant = ""
        self.directeur_adjoint = ""
        self.comptable = ""

        if creation:
            self.create()

    def create(self):
        print 'nouveau bureau'
        result = sql_connection.execute(
            'INSERT INTO BUREAUX (idx, debut, fin, president, vice_president, tresorier, secretaire, directeur) VALUES (NULL,?,?,?,?,?,?,?)',
            (
                self.debut, self.fin, self.president, self.vice_president, self.tresorier, self.secretaire,
                self.directeur))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'president', 'vice_president', 'tresorier', 'secretaire', 'directeur', 'gerant',
                    'directeur_adjoint', 'comptable'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE BUREAUX SET %s=? WHERE idx=?' % name, (value, self.idx))


class BaremeCAF(object):
    def __init__(self, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.plancher = 0
        self.plafond = 4000

        if creation:
            self.create()

    def create(self):
        print 'nouveau bareme caf'
        result = sql_connection.execute(
            'INSERT INTO BAREMESCAF (idx, debut, fin, plancher, plafond) VALUES (NULL,?,?,?,?)',
            (self.debut, self.fin, self.plancher, self.plafond))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression bareme caf'
        sql_connection.execute('DELETE FROM BAREMESCAF WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'plancher', 'plafond'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE BAREMESCAF SET %s=? WHERE idx=?' % name, (value, self.idx))


class Charges(object):
    def __init__(self, date=None, creation=True):
        self.idx = None
        self.date = date
        self.charges = 0.0

        if creation:
            self.create()

    def create(self):
        print 'nouvelles charges'
        result = sql_connection.execute('INSERT INTO CHARGES (idx, date, charges) VALUES (NULL,?,?)',
                                        (self.date, self.charges))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['date', 'charges'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE CHARGES SET %s=? WHERE idx=?' % name, (value, self.idx))


class User(object):
    def __init__(self, creation=True):
        self.idx = None
        self.login = "admin"
        self.password = bcrypt.hashpw(self.login.encode("utf-8"), bcrypt.gensalt())
        self.profile = PROFIL_ALL | PROFIL_ADMIN

        if creation:
            self.create()

    def create(self):
        print 'nouveau user'
        result = sql_connection.execute('INSERT INTO USERS (idx, login, password, profile) VALUES (NULL,?,?,?)',
                                        (self.login, self.password, self.profile))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression user'
        sql_connection.execute('DELETE FROM USERS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['login', 'password', 'profile'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE USERS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Reservataire(SQLObject):
    table = "RESERVATAIRES"

    def __init__(self, creation=True):
        self.idx = None
        self.debut = None
        self.fin = None
        self.nom = ""
        self.adresse = ""
        self.code_postal = ""
        self.ville = ""
        self.telephone = ""
        self.email = ""
        self.places = 0
        self.heures_jour = 0.0
        self.heures_semaine = 0.0
        self.options = 0

        if creation:
            self.create()

    def create(self):
        print 'nouveau reservataire'
        result = sql_connection.execute(
            'INSERT INTO RESERVATAIRES (idx, debut, fin, nom, places, heures_jour, heures_semaine, options) VALUES (NULL,?,?,?,?,?,?,?)',
            (self.debut, self.fin, self.nom, self.places, self.heures_jour, self.heures_semaine, self.options))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'nom', 'places', 'heures_jour', 'heures_semaine', 'options'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE RESERVATAIRES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Conge(object):
    __table__ = "CONGES"

    def __init__(self, parent, creation=True):
        self.idx = None
        self.debut = ""
        self.fin = ""
        self.label = ""
        self.options = 0
        self.parent = parent
        if creation:
            self.create()

    def create(self):
        print 'nouveau conge'
        result = sql_connection.execute(
            'INSERT INTO %s (idx, debut, fin, label, options) VALUES (NULL,?,?,?,?)' % self.__table__,
            (self.debut, self.fin, self.label, self.options))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression conge'
        sql_connection.execute('DELETE FROM %s WHERE idx=?' % self.__table__, (self.idx,))
        self.parent.CalculeJoursConges()

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'label', 'options'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE %s SET %s=? WHERE idx=?' % (self.__table__, name), (value, self.idx))
            self.parent.CalculeJoursConges()


class CongeInscrit(Conge):
    __table__ = "CONGES_INSCRITS"

    def create(self):
        print 'nouveau conge'
        result = sql_connection.execute(
            'INSERT INTO %s (idx, inscrit, debut, fin, label) VALUES (NULL,?,?,?,?)' % self.__table__,
            (self.parent.idx, self.debut, self.fin, self.label))
        self.idx = result.lastrowid


class CongeSalarie(Conge):
    __table__ = "CONGES_SALARIES"

    def create(self):
        print 'nouveau conge salarie'
        result = sql_connection.execute(
            'INSERT INTO %s (idx, salarie, debut, fin, label) VALUES (NULL,?,?,?,?)' % self.__table__,
            (self.parent.idx, self.debut, self.fin, self.label))
        self.idx = result.lastrowid


class Activite(object):
    last_value = 0

    def __init__(self, creation=True, value=None, couleur=None):
        self.idx = None
        self.label = ""
        self.value = value
        self.mode = MODE_NORMAL
        self.couleur = couleur
        self.couleur_supplement = None
        self.couleur_previsionnel = None
        self.formule_tarif = ""
        self.owner = ACTIVITY_OWNER_ALL
        if creation:
            self.create()

    def EvalTarif(self, inscrit, date, montant_heure_garde=0.0):
        if self.formule_tarif.strip():
            enfants, enfants_inscrits = GetEnfantsCount(inscrit, date)[0:2]
            for tarif in creche.tarifs_speciaux:
                try:
                    exec("%s = %r" % (tarif.label.lower().replace(" ", "_"), inscrit.famille.tarifs & (1 << tarif.idx)))
                except:
                    pass
            try:
                return eval(self.formule_tarif)
            except:
                return 0.0
        else:
            return 0.0

    def create(self):
        print 'nouvelle activite',
        if self.value is None:
            values = creche.activites.keys()
            value = Activite.last_value + 1
            while value in values:
                value += 1
            Activite.last_value = self.value = value
        print self.value
        result = sql_connection.execute(
            'INSERT INTO ACTIVITIES (idx, label, value, mode, couleur, couleur_supplement, couleur_previsionnel, formule_tarif, owner) VALUES(NULL,?,?,?,?,?,?,?,?)',
            (self.label, self.value, self.mode, str(self.couleur), str(self.couleur_supplement),
             str(self.couleur_previsionnel), self.formule_tarif, self.owner))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression activite'
        sql_connection.execute('DELETE FROM ACTIVITIES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        if name in ("couleur", "couleur_supplement", "couleur_previsionnel") and isinstance(value, basestring):
            self.__dict__[name] = eval(value)
        else:
            self.__dict__[name] = value
        if name in ['label', 'value', 'mode', 'couleur', "couleur_supplement", "couleur_previsionnel", "formule_tarif", "owner"] and self.idx:
            print 'update', name, value
            if name in ("couleur", "couleur_supplement", "couleur_previsionnel") and not isinstance(value, basestring):
                value = str(value)
            sql_connection.execute('UPDATE ACTIVITIES SET %s=? WHERE idx=?' % name, (value, self.idx))


class PeriodeReference(SQLObject):
    def __init__(self, type, duree_reference=7):
        self.type = type
        self.debut = None
        self.fin = None
        self.duree_reference = duree_reference
        self.reference = []
        for i in range(duree_reference):
            self.reference.append(self.type(self, i))

    def SetReferenceDuration(self, duration):
        if duration > self.duree_reference:
            for i in range(self.duree_reference, duration):
                self.reference.append(self.type(self, i))
        else:
            for i in range(duration, self.duree_reference):
                self.reference[i].delete()
            self.reference = self.reference[0:duration]
        self.duree_reference = duration

    def GetJourneeReference(self, date):
        if self.duree_reference > 7:
            return self.reference[((date - self.debut).days + self.debut.weekday()) % self.duree_reference]
        else:
            return self.reference[date.weekday()]

    def GetNombreJoursPresenceSemaine(self):
        jours = 0
        for i in range(self.duree_reference):
            if IsJourSemaineTravaille(i) and self.reference[i].GetState() & PRESENT:
                jours += 1
        if self.duree_reference > 7:
            return float(jours) / (self.duree_reference / 7)
        else:
            return jours

    def GetNombreHeuresPresenceSemaine(self):
        heures = 0.0
        for i in range(self.duree_reference):
            if IsJourSemaineTravaille(i) and self.reference[i].GetState() & PRESENT:
                heures += self.reference[i].GetNombreHeures()
        if self.duree_reference > 7:
            return heures / (self.duree_reference / 7)
        else:
            return heures

    def GetJoursHeuresReference(self):
        jours = 0
        heures = 0.0
        for i in range(self.duree_reference):
            if IsJourSemaineTravaille(i) and self.reference[i].GetState() & PRESENT:
                jours += 1
                heures += self.reference[i].GetNombreHeures()
        return jours, heures


class Contrat(PeriodeReference):
    def __init__(self, salarie, duree_reference=7, creation=True):
        self.idx = None
        self.salarie = salarie
        self.site = None
        self.fonction = ''
        PeriodeReference.__init__(self, JourneeReferenceSalarie, duree_reference)
        if creation:
            self.create()

    def GetJourneeReferenceCopy(self, date):
        reference = self.GetJourneeReference(date)
        result = JourneeSalarie(self.salarie, date, reference)
        result.reference = reference
        return result

    def create(self):
        print 'nouveau contrat'
        result = sql_connection.execute(
            'INSERT INTO CONTRATS (idx, employe, debut, fin, site, fonction, duree_reference) VALUES (NULL,?,?,?,?,?,?)',
            (self.salarie.idx, self.debut, self.fin, self.site, self.fonction, self.duree_reference))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression contrat'
        sql_connection.execute('DELETE FROM CONTRATS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'site', 'fonction', 'duree_reference'] and self.idx:
            if name == 'site':
                value = value.idx
            print 'update', name
            sql_connection.execute('UPDATE CONTRATS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Salarie(object):
    def __init__(self, creation=True):
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.telephone_domicile = ""
        self.telephone_domicile_notes = ""
        self.telephone_portable = ""
        self.telephone_portable_notes = ""
        self.email = ""
        self.diplomes = ''
        self.contrats = []
        self.conges = []
        self.journees = {}
        self.jours_conges = {}
        self.combinaison = ""
        if creation:
            self.create()

    def AddJournee(self, date):
        self.journees[date] = JourneeSalarie(self, date)
        return self.journees[date]

    def IsDateConge(self, date):
        return date in creche.jours_fermeture or date in self.jours_conges

    def GetJourneeReference(self, date):
        if date in self.jours_conges:
            return JourneeReferenceSalarie(None, 0)
        else:
            contrat = self.GetContrat(date)
            if contrat:
                return contrat.GetJourneeReference(date)
            else:
                return None

    def GetJournee(self, date):
        if self.IsDateConge(date):
            return None

        contrat = self.GetContrat(date)
        if contrat is None:
            return None

        if date in self.journees:
            return self.journees[date]
        else:
            return self.GetJourneeReference(date)

    def GetContrat(self, date):
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
                ratio += float(duree_contrat) / duree_annee * contrat.GetNombreJoursPresenceSemaine() / GetNombreJoursSemaineTravailles()
        return round(creche.conges_payes_salaries * ratio), round(creche.conges_supplementaires_salaries * ratio)

    def GetDecompteHeuresEtConges(self, debut, fin):
        affiche, contractualise, realise, cp, cs = False, 0.0, 0.0, 0, 0
        date = debut
        while date <= fin:
            contrat = self.GetContrat(date)
            if contrat:
                journee_reference = contrat.GetJourneeReference(date)
                affiche = True
                heures_reference = journee_reference.GetNombreHeures()
                if heures_reference > 0 and (date in self.jours_conges or date in creche.jours_conges):
                    cp += 1
                else:
                    if date in self.journees:
                        journee = self.journees[date]
                        state = journee.GetState()
                        if state < 0:
                            if state == CONGES_PAYES:
                                cp += 1
                            elif state == VACANCES:
                                cs += 1
                            heures_reference = 0
                            heures_realisees = 0
                        else:
                            heures_realisees = journee.GetNombreHeures()
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
                        print "Periode incorrecte pour %s :" % GetPrenomNom(self), date_debut_periode, date_fin_periode
                        continue
                    if ((date_debut_periode <= date_debut <= date_fin_periode) or
                            (date_debut_periode <= date_fin <= date_fin_periode) or
                            (date_debut < date_debut_periode and date_fin > date_fin_periode)):
                        result.append(contrat)
                except:
                    pass
        return result

    def GetInscription(self, date):
        # proxy...
        return self.GetContrat(date)

    def AddConge(self, conge, calcule=True):
        print "AddConge", conge, calcule
        self.conges.append(conge)
        if calcule:
            self.CalculeJoursConges()

    def CalculeJoursConges(self, parent=None):
        if parent is None:
            parent = creche
        self.jours_conges = {}

        def AddPeriode(debut, fin, conge):
            date = debut
            while date <= fin:
                if date not in parent.jours_fermeture:
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
            except:
                pass

    def GetStateSimple(self, date):
        if self.IsDateConge(date):
            return ABSENT

        inscription = self.GetInscription(date)
        if inscription is None:
            return ABSENT

        reference = self.GetJourneeReference(date)
        ref_state = reference.GetState()  # TODO on peut s'en passer ?

        if date in self.journees:
            journee = self.journees[date]
            state = journee.GetState()  # TODO on peut s'en passer ?
            if state in (MALADE, HOPITAL, ABSENCE_NON_PREVENUE):
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

    def create(self):
        print 'nouveau salarie'
        result = sql_connection.execute(
            'INSERT INTO EMPLOYES (idx, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, email, diplomes, combinaison) VALUES(NULL,?,?,?,?,?,?,?,?,?)',
            (self.prenom, self.nom, self.telephone_domicile, self.telephone_domicile_notes, self.telephone_portable,
             self.telephone_portable_notes, self.email, self.diplomes, self.combinaison))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression salarie'
        sql_connection.execute('DELETE FROM EMPLOYES WHERE idx=?', (self.idx,))
        for obj in self.contrats + self.journees.values():
            obj.delete()

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'nom', 'telephone_domicile', 'telephone_domicile_notes', 'telephone_portable',
                    'telephone_portable_notes', 'email', 'diplomes', 'combinaison'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE EMPLOYES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Professeur(SQLObject):
    table = "PROFESSEURS"

    def __init__(self, creation=True):
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.entree = None
        self.sortie = None

        if creation:
            self.create()

    def create(self):
        print 'nouveau professeur'
        result = sql_connection.execute(
            'INSERT INTO PROFESSEURS (idx, prenom, nom, entree, sortie) VALUES(NULL,?,?,?,?)',
            (self.prenom, self.nom, self.entree, self.sortie))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'nom', 'entree', 'sortie'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE PROFESSEURS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Site(object):
    def __init__(self, creation=True):
        self.idx = None
        self.nom = ''
        self.adresse = ''
        self.code_postal = ''
        self.ville = ''
        self.telephone = ''
        self.capacite = 0
        self.groupe = 0
        if creation:
            self.create()

    def create(self):
        print 'nouveau site'
        result = sql_connection.execute(
            'INSERT INTO SITES (idx, nom, adresse, code_postal, ville, telephone, capacite, groupe) VALUES(NULL,?,?,?,?,?,?,?)',
            (self.nom, self.adresse, self.code_postal, self.ville, self.telephone, self.capacite, self.groupe))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression site'
        sql_connection.execute('DELETE FROM SITES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['nom', 'adresse', 'code_postal', 'ville', 'telephone', 'capacite', 'groupe'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE SITES SET %s=? WHERE idx=?' % name, (value, self.idx))


def GetFormuleConversion(formule):
    if formule:
        result = []
        for cas in formule:
            condition = cas[0].strip()
            if condition == "":
                condition = "True"
            else:
                condition = condition.lower().\
                    replace(" et ", " and ").\
                    replace(" ou ", " or ").\
                    replace("!=", "__<>").\
                    replace("<=", "__<eq").\
                    replace(">=", "__>eq").\
                    replace("=", "==").\
                    replace("__<>", "!=").\
                    replace("__<eq", "<=").\
                    replace("__>eq", ">=")
            result.append([condition, cas[1], cas[0]])
        return result
    else:
        return None


class Creche(object):
    def __init__(self):
        self.idx = None
        self.nom = ''
        self.adresse = ''
        self.code_postal = ''
        self.ville = ''
        self.telephone = ''
        self.sites = []
        self.reservataires = []
        self.users = []
        self.tarifs_speciaux = []
        self.plages_horaires = []
        self.groupes = []
        self.categories = []
        self.couleurs = {ABSENCE_NON_PREVENUE: Activite(creation=False, value=ABSENCE_NON_PREVENUE,
                                                        couleur=[0, 0, 255, 150, wx.SOLID])}
        self.activites = {}
        self.salaries = []
        self.professeurs = []
        self.feries = {}
        self.conges = []
        self.bureaux = []
        self.baremes_caf = []
        self.charges = {}
        self.numeros_facture = {}
        self.familles = []
        self.inscrits = []
        self.ouverture = 7.75
        self.fermeture = 18.5
        self.affichage_min = 7.75
        self.affichage_max = 19.0
        self.granularite = 15
        self.minimum_maladie = 15
        self.periode_revenus = REVENUS_YM2
        self.mode_facturation = FACTURATION_FORFAIT_10H
        self.repartition = REPARTITION_MENSUALISATION_12MOIS
        self.temps_facturation = FACTURATION_FIN_MOIS
        self.conges_inscription = 0
        self.tarification_activites = ACTIVITES_NON_FACTUREES
        self.traitement_maladie = DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES
        self.preinscriptions = False
        self.presences_previsionnelles = False
        self.presences_supplementaires = True
        self.modes_inscription = MODE_HALTE_GARDERIE + MODE_4_5 + MODE_3_5
        self.email = ''
        self.smtp_server = ''
        self.caf_email = ''
        self.mode_accueil_defaut = 0;
        self.type = TYPE_PARENTAL
        self.mode_saisie_planning = SAISIE_HORAIRE
        self.tranches_capacite = [JourneeCapacite(i) for i in range(7)]
        self.facturation_periode_adaptation = PERIODE_ADAPTATION_FACTUREE_NORMALEMENT
        self.facturation_jours_feries = ABSENCES_DEDUITES_EN_SEMAINES
        self.formule_taux_horaire = None
        self.conversion_formule_taux_horaire = None
        self.formule_taux_effort = None
        self.conversion_formule_taux_effort = None
        self.gestion_alertes = False
        self.age_maximum = 3
        self.seuil_alerte_inscription = 3
        self.cloture_factures = False
        self.arrondi_heures = SANS_ARRONDI
        self.arrondi_facturation = SANS_ARRONDI
        self.arrondi_facturation_periode_adaptation = SANS_ARRONDI
        self.arrondi_mensualisation = ARRONDI_HEURE_PLUS_PROCHE
        self.arrondi_heures_salaries = SANS_ARRONDI
        self.arrondi_mensualisation_euros = SANS_ARRONDI
        self.arrondi_semaines = ARRONDI_SEMAINE_SUPERIEURE
        self.gestion_maladie_hospitalisation = False
        self.gestion_absences_non_prevenues = False
        self.gestion_maladie_sans_justificatif = False
        self.gestion_preavis_conges = False
        self.gestion_depart_anticipe = False
        self.alerte_depassement_planning = False
        self.date_raz_permanences = None
        self.tri_inscriptions = TRI_NOM
        self.tri_planning = TRI_NOM
        self.tri_factures = TRI_NOM
        self.last_tablette_synchro = ""
        self.changement_groupe_auto = False
        self.allergies = ""
        self.regularisation_fin_contrat = True
        self.conges_payes_salaries = 25
        self.conges_supplementaires_salaries = 0
        self.cout_journalier = 0.0
        self.alertes = {}
        self.CalculeJoursConges()

    def GetAllergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",") if allergie.strip()]

    def CalculeJoursConges(self):
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

    def AddConge(self, conge, calcule=True):
        conge.creche = self
        if conge.debut is None:
            return
        if '/' in conge.debut or conge.debut not in [tmp[0] for tmp in jours_fermeture]:
            self.conges.append(conge)
        else:
            self.feries[conge.debut] = conge
        if calcule:
            self.CalculeJoursConges()

    def UpdateFormuleTauxHoraire(self, changed=True):
        if changed:
            print 'update formule_taux_horaire', self.formule_taux_horaire
            sql_connection.execute('UPDATE CRECHE SET formule_taux_horaire=?', (str(self.formule_taux_horaire),))
        self.conversion_formule_taux_horaire = GetFormuleConversion(self.formule_taux_horaire)

    def EvalTauxHoraire(self, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage,
                        conge_parental, heures_mois, heure_mois, paje, tarifs):
        return self.EvalFormule(self.conversion_formule_taux_horaire, mode, handicap, revenus, enfants, jours, heures,
                                reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs)

    def AreRevenusNeeded(self):
        if self.mode_facturation in (FACTURATION_FORFAIT_10H, FACTURATION_PSU, FACTURATION_PSU_TAUX_PERSONNALISES):
            return True
        elif self.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            return False
        if self.formule_taux_horaire is None:
            return False
        for cas in self.formule_taux_horaire:
            if "revenus" in cas[0] or "paje" in cas[0]:
                return True
        else:
            return False

    def CheckFormuleTauxHoraire(self, index):
        return self.CheckFormule(self.conversion_formule_taux_horaire, index)

    def EvalFormule(self, formule, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage,
                    conge_parental, heures_mois, heure_mois, paje, tarifs):
        # print 'EvalFormule', 'mode=%d' % mode, handicap, 'revenus=%f' % revenus, 'enfants=%d' % enfants, 'jours=%d' % jours, 'heures=%f' % heures, reservataire, nom, 'parents=%d' % parents, chomage, conge_parental, 'heures_mois=%f' % heures_mois, heure_mois
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
                    # print cas[0], cas[1]
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
            print e
            return False

    def UpdateFormuleTauxEffort(self, changed=True):
        if changed:
            print 'update formule_taux_effort', self.formule_taux_effort
            sql_connection.execute('UPDATE CRECHE SET formule_taux_effort=?', (str(self.formule_taux_effort),))
        self.conversion_formule_taux_effort = GetFormuleConversion(self.formule_taux_effort)

    def EvalTauxEffort(self, mode, handicap, revenus, enfants, jours, heures, reservataire, nom, parents, chomage,
                       conge_parental, heures_mois, heure_mois, paje, tarifs):
        return self.EvalFormule(self.conversion_formule_taux_effort, mode, handicap, revenus, enfants, jours, heures,
                                reservataire, nom, parents, chomage, conge_parental, heures_mois, heure_mois, paje, tarifs)

    def CheckFormuleTauxEffort(self, index):
        return self.CheckFormule(self.conversion_formule_taux_effort, index)

    def GetActivitesAvecHoraires(self):
        result = []
        for activite in self.activites.values():
            if activite.mode not in (MODE_SANS_HORAIRES, MODE_SYSTEMATIQUE_SANS_HORAIRES):
                result.append(activite)
        return result

    def HasActivitesAvecHoraires(self):
        return len(self.GetActivitesAvecHoraires()) > 1

    def GetActivitesSansHoraires(self):
        result = []
        for activite in self.activites.values():
            if activite.mode == MODE_SANS_HORAIRES:
                result.append(activite)
        return result

    def GetAmplitudeHoraire(self):
        return self.fermeture - self.ouverture

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

    def GetCapacite(self, jour=None, tranche=None):
        if jour is None:
            jours, result = 0, 0.0
            for jour in range(7):
                if IsJourSemaineTravaille(jour):
                    jours += 1
                    result += self.GetCapacite(jour)
            return result / jours
        elif tranche is None:
            return self.GetHeuresAccueil(jour) / self.GetAmplitudeHoraire()
        else:
            for start, end, value in self.tranches_capacite[jour].activites:
                if start <= tranche < end:
                    return value
            else:
                return 0

    def GetHeuresAccueil(self, jour):
        result = 0.0
        for start, end, value in self.tranches_capacite[jour].activites:
            result += value * (end - start)
        return result / 12

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

    def GetSalarie(self, idx):
        return self.GetObject(self.salaries, idx)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['nom', 'adresse', 'code_postal', 'ville', 'telephone', 'ouverture', 'fermeture', 'affichage_min',
                    'affichage_max', 'granularite', 'preinscriptions', 'presences_previsionnelles',
                    'presences_supplementaires', 'modes_inscription', 'minimum_maladie', 'email', 'type',
                    'periode_revenus', 'mode_facturation', 'repartition', 'temps_facturation', 'conges_inscription',
                    'tarification_activites', 'traitement_maladie', 'facturation_jours_feries',
                    'facturation_periode_adaptation', 'gestion_alertes', 'age_maximum', 'seuil_alerte_inscription',
                    'cloture_factures', 'arrondi_heures', 'arrondi_facturation',
                    'arrondi_facturation_periode_adaptation', 'arrondi_heures_salaries',
                    'arrondi_mensualisation_euros', 'arrondi_semaines', 'gestion_maladie_hospitalisation',
                    'gestion_absences_non_prevenues', 'gestion_maladie_sans_justificatif', 'gestion_preavis_conges',
                    'gestion_depart_anticipe', 'alerte_depassement_planning', 'tri_planning', 'tri_inscriptions',
                    'tri_factures', 'smtp_server', 'caf_email', 'mode_accueil_defaut', 'mode_saisie_planning',
                    'last_tablette_synchro', 'changement_groupe_auto', 'allergies',
                    'regularisation_fin_contrat', 'date_raz_permanences',
                    'conges_payes_salaries', 'conges_supplementaires_salaries', 'cout_journalier'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE CRECHE SET %s=?' % name, (value,))


class Revenu(object):
    def __init__(self, parent, debut=None, fin=None, creation=True):
        self.parent = parent
        self.idx = None
        self.debut = debut
        self.fin = fin
        self.revenu = ''
        self.chomage = False
        self.conge_parental = False
        self.regime = 0

        if creation:
            self.create()

    def create(self):
        print 'nouveau revenu'
        result = sql_connection.execute(
            'INSERT INTO REVENUS (idx, parent, debut, fin, revenu, chomage, conge_parental, regime) VALUES(NULL,?,?,?,?,?,?,?)',
            (self.parent.idx, self.debut, self.fin, self.revenu, self.chomage, self.conge_parental, self.regime))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression revenu'
        sql_connection.execute('DELETE FROM REVENUS WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'revenu', 'chomage', 'conge_parental', 'regime'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE REVENUS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Parent(object):
    def __init__(self, famille, relation=None, creation=True, automatic=True):
        self.famille = famille
        self.idx = None
        self.relation = relation
        self.prenom = ""
        self.nom = ""
        self.adresse = ""
        self.code_postal = ""
        self.ville = ""
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
            self.create()
            if automatic:
                date_revenus = GetDateRevenus(today)
                debut = datetime.date(date_revenus.year, 1, 1)
                fin = datetime.date(date_revenus.year, 12, 31)
                self.revenus.append(Revenu(self, debut, fin))

    def create(self):
        print 'nouveau parent'
        result = sql_connection.execute(
            'INSERT INTO PARENTS (idx, famille, relation, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?)',
            (self.famille.idx, self.relation, self.prenom, self.nom, self.telephone_domicile,
             self.telephone_domicile_notes, self.telephone_portable, self.telephone_portable_notes,
             self.telephone_travail, self.telephone_travail_notes, self.email))
        self.idx = result.lastrowid
        for revenu in self.revenus:
            revenu.create()

    def delete(self):
        print 'suppression parent'
        sql_connection.execute('DELETE FROM PARENTS WHERE idx=?', (self.idx,))
        for revenu in self.revenus:
            revenu.delete()
        for bureau in creche.bureaux:
            for attr in ('president', 'vice_president', 'tresorier', 'secretaire'):
                if getattr(bureau, attr) is self:
                    setattr(bureau, attr, None)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['relation', 'prenom', 'nom', 'adresse', 'code_postal', 'ville', 'telephone_domicile', 'telephone_domicile_notes', 'telephone_portable',
                    'telephone_portable_notes', 'telephone_travail', 'telephone_travail_notes', 'email'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE PARENTS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Referent(SQLObject):
    table = "REFERENTS"

    def __init__(self, famille, creation=True):
        self.famille = famille
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.telephone = ""
        if creation:
            self.create()

    def create(self):
        print 'nouveau referent'
        result = sql_connection.execute(
            'INSERT INTO REFERENTS (idx, famille, prenom, nom, telephone) VALUES(NULL,?,?,?,?)',
            (self.famille.idx, self.prenom, self.nom, self.telephone))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'nom', 'telephone'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE REFERENTS SET %s=? WHERE idx=?' % name, (value, self.idx))


class TarifSpecial(SQLObject):
    table = "TARIFSSPECIAUX"

    def __init__(self, creation=True):
        self.idx = None
        self.label = ""
        self.type = TARIF_SPECIAL_MAJORATION
        self.unite = TARIF_SPECIAL_UNITE_EUROS
        self.valeur = 0.0
        if creation:
            self.create()

    def create(self):
        print 'nouveau tarif special'
        result = sql_connection.execute(
            'INSERT INTO TARIFSSPECIAUX (idx, label, type, unite, valeur) VALUES(NULL,?,?,?,?)',
            (self.label, self.type, self.unite, self.valeur))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['label', 'type', 'unite', 'valeur'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE TARIFSSPECIAUX SET %s=? WHERE idx=?' % name, (value, self.idx))


class PlageHoraire(SQLObject):
    table = "PLAGESHORAIRES"

    def __init__(self, creation=True):
        self.idx = None
        self.debut = 0
        self.fin = 0
        self.flags = 0
        if creation:
            self.create()

    def create(self):
        print 'nouvelle plage horaire'
        result = sql_connection.execute('INSERT INTO PLAGESHORAIRES (idx, debut, fin, flags) VALUES(NULL,?,?,?)',
                                        (self.debut, self.fin, self.flags))
        self.idx = result.lastrowid

    def delete(self):
        SQLObject.delete(self)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['debut', 'fin', 'flags'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE PLAGESHORAIRES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Groupe(SQLObject):
    table = "GROUPES"

    def __init__(self, ordre=None, creation=True):
        self.idx = None
        self.nom = ""
        self.ordre = ordre
        self.age_maximum = 0
        if creation:
            self.create()

    def create(self):
        print 'nouveau groupe'
        result = sql_connection.execute('INSERT INTO GROUPES (idx, nom, ordre, age_maximum) VALUES(NULL,?,?,?)',
                                        (self.nom, self.ordre, self.age_maximum))
        self.idx = result.lastrowid

    def delete(self):
        SQLObject.delete(self)

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['nom', 'ordre', 'age_maximum'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE GROUPES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Categorie(SQLObject):
    table = "CATEGORIES"

    def __init__(self, creation=True):
        self.idx = None
        self.nom = ""
        if creation:
            self.create()

    def create(self):
        print 'nouvelle categorie'
        result = sql_connection.execute('INSERT INTO CATEGORIES (idx, nom) VALUES(NULL,?)', (self.nom,))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['nom'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE CATEGORIES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Inscription(PeriodeReference):
    table = "INSCRIPTIONS"

    def __init__(self, inscrit, duree_reference=7, creation=True):
        self.idx = None
        self.inscrit = inscrit
        self.reservataire = None
        self.groupe = None
        self.preinscription = False
        self.site = None
        self.sites_preinscription = []
        self.depart = None
        self.mode = 0
        self.forfait_mensuel_heures = 0.0
        self.semaines_conges = 0
        self.heures_permanences = 0.0
        PeriodeReference.__init__(self, JourneeReferenceInscription, duree_reference)
        self.fin_periode_adaptation = None
        self.professeur = None
        self.forfait_mensuel = 0.0
        self.frais_inscription = 0.0
        self.allocation_mensuelle_caf = 0.0
        self.heures_supplementaires = {}

        if creation:
            self.mode = creche.mode_accueil_defaut
            self.create()
            if creche.modes_inscription == MODE_5_5:
                for i in range(duree_reference):
                    if i % 7 < 5:
                        self.reference[i].SetState(PRESENT)

    def GetJourneeReferenceCopy(self, date):
        reference = self.GetJourneeReference(date)
        result = Journee(self.inscrit, date, reference)
        result.reference = reference
        return result

    def GetNombreJoursCongesPeriode(self):
        if self.semaines_conges:
            return self.semaines_conges * self.GetNombreJoursPresenceSemaine()
        else:
            return 0

    def GetNombreJoursCongesPris(self, debut, fin):
        jours = 0
        date = debut
        # print "GetNombreJoursCongesPris(%s-%s)" % (debut, fin)
        while date < fin:
            state = self.inscrit.GetStateSimple(date)
            if creche.facturation_jours_feries == ABSENCES_DEDUITES_EN_JOURS:
                if state == VACANCES:
                    # print date
                    jours += 1
            else:
                if state in (ABSENT, VACANCES):
                    reference = self.GetJourneeReference(date)
                    if reference.GetNombreHeures() > 0:
                        # print date
                        jours += 1
            date += datetime.timedelta(1)
        return jours

    def GetDebutDecompteJoursConges(self):
        if self.fin_periode_adaptation:
            return self.fin_periode_adaptation + datetime.timedelta(1)
        else:
            return self.debut

    def GetFinDecompteJoursConges(self):
        if creche.gestion_depart_anticipe and self.depart:
            return self.depart
        else:
            return self.fin

    def GetNombreJoursCongesPoses(self):
        if self.debut and self.fin:
            return self.GetNombreJoursCongesPris(self.GetDebutDecompteJoursConges(), self.GetFinDecompteJoursConges())
        else:
            return 0

    def IsNombreSemainesCongesAtteint(self, jalon):
        if creche.facturation_jours_feries == ABSENCES_DEDUITES_SANS_LIMITE:
            return False
        if self.debut:
            if not self.semaines_conges:
                return True
            debut = self.GetDebutDecompteJoursConges()
            pris = self.GetNombreJoursCongesPris(debut, jalon)
            total = self.GetNombreJoursCongesPeriode()
            return pris >= total
        else:
            return False

    def GetDatesFromReference(self, index):
        dates = []
        if self.debut is None:
            return dates
        fin = self.fin
        if not fin:
            fin = datetime.date(self.debut.year + 1, self.debut.month, self.debut.day)
        date = self.debut + datetime.timedelta(index + 7 - self.debut.weekday())
        while date < fin:
            dates.append(date)
            date += datetime.timedelta(self.duree_reference)
        return dates

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

    def create(self):
        print 'nouvelle inscription'
        result = sql_connection.execute(
            'INSERT INTO INSCRIPTIONS (idx, inscrit, debut, fin, depart, mode, forfait_mensuel, frais_inscription, allocation_mensuelle_caf, fin_periode_adaptation, duree_reference, forfait_mensuel_heures, semaines_conges, heures_permanences) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (self.inscrit.idx, self.debut, self.fin, self.depart, self.mode, self.forfait_mensuel, self.frais_inscription, self.allocation_mensuelle_caf, self.fin_periode_adaptation, self.duree_reference, self.forfait_mensuel_heures, self.semaines_conges, self.heures_permanences))
        self.idx = result.lastrowid

    def delete(self):
        SQLObject.delete(self)
        for object in self.reference:
            object.delete()

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ('site', 'professeur', 'reservataire', 'groupe') and value is not None and self.idx:
            value = value.idx
        elif name == "sites_preinscription":
            value = " ".join([str(value.idx) for value in value])
        if name in ['debut', 'fin', 'depart', 'mode', 'forfait_mensuel', 'frais_inscription',
                    'allocation_mensuelle_caf', 'fin_periode_adaptation', 'duree_reference', 'forfait_mensuel_heures',
                    'semaines_conges', 'heures_permanences', 'preinscription', 'site', 'sites_preinscription',
                    'professeur', 'reservataire', 'groupe'] and self.idx:
            print 'update', name, value
            sql_connection.execute('UPDATE INSCRIPTIONS SET %s=? WHERE idx=?' % name, (value, self.idx))


class Frere_Soeur(object):
    def __init__(self, famille, creation=True):
        self.idx = None
        self.famille = famille
        self.prenom = ''
        self.naissance = None
        # self.handicape = 0
        self.entree = None
        self.sortie = None

        if creation:
            self.create()

    def create(self):
        print 'nouveau frere / soeur'
        result = sql_connection.execute(
            'INSERT INTO FRATRIES (idx, famille, prenom, naissance, entree, sortie) VALUES(NULL,?,?,?,?,?)',
            (self.famille.idx, self.prenom, self.naissance, self.entree, self.sortie))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression frere / soeur'
        sql_connection.execute('DELETE FROM FRATRIES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['prenom', 'naissance', 'entree', 'sortie'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE FRATRIES SET %s=? WHERE idx=?' % name, (value, self.idx))


class NumeroFacture(SQLObject):
    table = "NUMEROS_FACTURE"

    def __init__(self, date, valeur=0, idx=None):
        self.ready = False
        self.idx = idx
        self.date = date
        self.valeur = valeur
        self.ready = True

    def create(self):
        print 'nouveau numero de facture'
        result = sql_connection.execute('INSERT INTO NUMEROS_FACTURE (idx, date, valeur) VALUES (NULL,?,?)',
                                        (self.date, self.valeur))
        self.idx = result.lastrowid

    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if self.ready and name in ['valeur']:
            if self.idx and self.valeur:
                print 'update', name
                sql_connection.execute('UPDATE NUMEROS_FACTURE SET %s=? WHERE idx=?' % name, (value, self.idx))
            elif value and not self.idx:
                self.create()
            elif self.idx and not self.valeur:
                self.delete()


class Correction(SQLObject):
    table = "CORRECTIONS"

    def __init__(self, inscrit, date, valeur=0, libelle="", idx=None):
        self.ready = False
        self.idx = idx
        self.inscrit = inscrit
        self.date = date
        self.valeur = valeur
        self.libelle = libelle
        self.ready = True

    def create(self):
        print 'nouvelle correction'
        result = sql_connection.execute(
            'INSERT INTO CORRECTIONS (idx, inscrit, date, valeur, libelle) VALUES (NULL,?,?,?,?)',
            (self.inscrit.idx, self.date, self.valeur, self.libelle))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression correction'
        sql_connection.execute('DELETE FROM CORRECTIONS WHERE idx=?', (self.idx,))
        self.idx = None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if self.ready and name in ['valeur', 'libelle']:
            if self.idx and (self.valeur or self.libelle):
                print 'update', name
                sql_connection.execute('UPDATE CORRECTIONS SET %s=? WHERE idx=?' % name, (value, self.idx))
            elif value and not self.idx:
                self.create()
            elif self.idx and not self.valeur and not self.libelle:
                self.delete()


class Famille(object):
    def __init__(self, creation=True, automatic=True):
        self.idx = None
        self.adresse = ""
        self.code_postal = ""
        self.ville = ""
        self.numero_securite_sociale = ""
        self.numero_allocataire_caf = ""
        self.medecin_traitant = ""
        self.telephone_medecin_traitant = ""
        self.assureur = ""
        self.numero_police_assurance = ""
        self.code_client = ""
        self.tarifs = 0
        self.notes = ""
        self.freres_soeurs = []
        if automatic:
            self.parents = [None, None]
        else:
            self.parents = []
        self.referents = []
        self.encaissements = []

        if creation:
            self.create()
            if automatic:
                self.parents[0] = Parent(self, "papa")
                self.parents[1] = Parent(self, "maman")

    def create(self):
        print 'nouvelle famille'
        result = sql_connection.execute(
            'INSERT INTO FAMILLES (idx, adresse, code_postal, ville, numero_securite_sociale, numero_allocataire_caf, tarifs, notes, medecin_traitant, telephone_medecin_traitant, assureur, numero_police_assurance, code_client) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?,?)',
            (self.adresse, self.code_postal, self.ville, self.numero_securite_sociale, self.numero_allocataire_caf,
             self.tarifs, self.notes, self.medecin_traitant, self.telephone_medecin_traitant, self.assureur,
             self.numero_police_assurance, self.code_client))
        self.idx = result.lastrowid
        for obj in self.parents + self.freres_soeurs + self.referents:
            if obj:
                obj.create()

    def delete(self):
        print 'suppression famille'
        sql_connection.execute('DELETE FROM FAMILLES WHERE idx=?', (self.idx,))
        for obj in self.parents + self.freres_soeurs + self.referents:
            if obj:
                obj.delete()

    def __setattr__(self, name, value):
        if name in self.__dict__:
            old_value = self.__dict__[name]
        else:
            old_value = '-'
        self.__dict__[name] = value
        if name in ['adresse', 'code_postal', 'ville', 'numero_securite_sociale', 'numero_allocataire_caf', 'tarifs',
                    'notes', 'medecin_traitant', 'telephone_medecin_traitant', 'assureur', 'numero_police_assurance',
                    'code_client'] and self.idx:
            print 'update', name, (old_value, value)
            sql_connection.execute('UPDATE FAMILLES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Inscrit(object):
    def __init__(self, creation=True, automatic=True):
        self.idx = None
        self.prenom = ""
        self.nom = ""
        self.sexe = None
        self.naissance = None
        self.handicap = False
        self.categorie = None
        self.marche = None
        self.photo = None
        self.combinaison = ""
        self.notes = ""
        self.inscriptions = []
        self.conges = []
        self.journees = {}
        self.semaines = {}
        self.jours_conges = {}
        self.factures_cloturees = {}
        self.corrections = {}
        self.allergies = ""
        self.famille = None

        if creation:
            self.famille = Famille(automatic=automatic)
            self.create()
            if automatic:
                self.inscriptions.append(Inscription(self))

    def AddJournee(self, date):
        self.journees[date] = Journee(self, date)
        return self.journees[date]

    def GetAllergies(self):
        return [allergie.strip() for allergie in self.allergies.split(",")]

    def create(self):
        print 'nouvel inscrit'
        result = sql_connection.execute(
            'INSERT INTO INSCRITS (idx, prenom, nom, naissance, handicap, marche, photo, notes, combinaison, categorie, allergies, famille) VALUES(NULL,?,?,?,?,?,?,?,?,?,?,?)',
            (self.prenom, self.nom, self.naissance, self.handicap, self.marche, self.photo, self.notes,
             self.combinaison,
             self.categorie, self.allergies, self.famille.idx))
        self.idx = result.lastrowid
        for inscription in self.inscriptions:
            inscription.create()

    def delete(self):
        print 'suppression inscrit'
        sql_connection.execute('DELETE FROM INSCRITS WHERE idx=?', (self.idx,))
        for obj in self.inscriptions + self.journees.values():
            if obj is not None:
                obj.delete()

    def __setattr__(self, name, value):
        if name in self.__dict__:
            old_value = self.__dict__[name]
        else:
            old_value = '-'
        self.__dict__[name] = value
        if name == 'photo' and value:
            value = binascii.b2a_base64(value)
        elif name in ('categorie', 'famille') and value is not None and self.idx:
            value = value.idx
        if name in ['prenom', 'nom', 'sexe', 'naissance', 'handicap', 'marche', 'photo', 'combinaison', 'notes',
                    'categorie', 'allergies', 'famille'] and self.idx:
            print 'update', self.idx, name, (old_value, value)
            sql_connection.execute('UPDATE INSCRITS SET %s=? WHERE idx=?' % name, (value, self.idx))

    def AddConge(self, conge, calcule=True):
        self.conges.append(conge)
        if calcule:
            self.CalculeJoursConges()

    def GetGroupe(self):
        result = None
        age = GetAge(self.naissance)
        for groupe in creche.groupes:
            if not groupe.age_maximum or age <= groupe.age_maximum:
                if result is None or not result.age_maximum or (groupe.age_maximum and groupe.age_maximum < result.age_maximum):
                    result = groupe
        return result

    def CalculeJoursConges(self, parent=None):
        if parent is None:
            parent = creche
        self.jours_conges = {}

        def AddPeriode(debut, fin, conge):
            date = debut
            while date <= fin:
                if date not in parent.jours_fermeture:
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
            except:
                pass

    def IsPresent(self, debut, fin, site, handicap=None):
        for inscription in self.inscriptions:
            if ((inscription.fin is None or inscription.fin >= debut) and
                    (not creche.preinscriptions or not inscription.preinscription) and
                    (site is None or inscription.site == site) and
                    (inscription.debut is not None) and
                    (not fin or inscription.debut <= fin) and
                    (handicap is None or self.handicap == handicap)):
                return True
        return False

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

    def GetInscription(self, date, preinscription=False, departanticipe=True, array=False):
        result = []
        for inscription in self.inscriptions:
            if (preinscription or not creche.preinscriptions or not inscription.preinscription) and \
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

    def GetInscriptions(self, date_debut=None, date_fin=None):
        result = []
        if not date_debut:
            date_debut = datetime.date.min
        if not date_fin:
            date_fin = datetime.date.max
        for inscription in self.inscriptions:
            if (not creche.preinscriptions or not inscription.preinscription) and inscription.debut:
                try:
                    date_debut_periode = inscription.debut
                    if inscription.fin:
                        date_fin_periode = inscription.fin
                    else:
                        date_fin_periode = datetime.date.max
                    if date_fin_periode < date_debut_periode:
                        print "Periode incorrecte pour %s :" % GetPrenomNom(self), date_debut_periode, date_fin_periode
                        continue
                    if ((date_debut_periode <= date_debut <= date_fin_periode) or
                            (date_debut_periode <= date_fin <= date_fin_periode) or
                            (date_debut < date_debut_periode and date_fin > date_fin_periode)):
                        result.append(inscription)
                except:
                    pass
        result.sort(key=lambda i: i.debut)
        return result

    def HasFacture(self, date):
        if not date or date.month in creche.mois_sans_facture:
            return False
        month_start = GetMonthStart(date)
        if config.options & FACTURES_FAMILLES and creche.mode_saisie_planning == SAISIE_HORAIRE:
            day = month_start
            while day.month == date.month:
                journee = self.GetJournee(day)
                if journee and journee.GetState() != 0:  # TODO si < 0 on n'émet pas de facture pour les enfants malades
                    return True
                day += datetime.timedelta(1)
        else:
            if self.GetInscriptions(month_start, GetMonthEnd(date)):
                return True
        if creche.temps_facturation != FACTURATION_FIN_MOIS:
            previous_month_end = month_start - datetime.timedelta(1)
            if self.GetInscriptions(GetMonthStart(previous_month_end), previous_month_end):
                return True
        return False

    def IsFactureCloturee(self, date):
        if creche.temps_facturation == FACTURATION_FIN_MOIS:
            date_cloture = GetMonthStart(date)
        else:
            date_cloture = GetNextMonthStart(date)
        return date_cloture in self.factures_cloturees

    def GetJourneeReference(self, date):
        if date in self.jours_conges:
            return JourneeReferenceInscription(None, 0)
        else:
            inscription = self.GetInscription(date)
            if inscription:
                return inscription.GetJourneeReference(date)
            else:
                return None

    def GetJourneeReferenceCopy(self, date):
        inscription = self.GetInscription(date)
        if inscription:
            return inscription.GetJourneeReferenceCopy(date)
        else:
            return None

    def IsDateConge(self, date):
        return date in creche.jours_fermeture or (
            creche.conges_inscription != GESTION_CONGES_INSCRIPTION_AVEC_SUPPLEMENT and date in self.jours_conges)

    def GetJournee(self, date):
        if self.IsDateConge(date):
            return None

        inscription = self.GetInscription(date)
        if inscription is None:
            return None

        if date in self.journees:
            return self.journees[date]
        else:
            return self.GetJourneeReference(date)

    def GetStateSimple(self, date):
        if self.IsDateConge(date):
            return ABSENT

        inscription = self.GetInscription(date)
        if inscription is None:
            return ABSENT

        reference = self.GetJourneeReference(date)
        ref_state = reference.GetState()  # TODO on peut s'en passer ?

        if date in self.journees:
            journee = self.journees[date]
            state = journee.GetState()  # TODO on peut s'en passer ?
            if state in (MALADE, HOPITAL, ABSENCE_NON_PREVENUE):
                return state
            elif state in (ABSENT, VACANCES):
                if inscription.mode == MODE_5_5 or ref_state:
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

    def GetState(self, date):
        """Retourne les infos sur une journée
        :param date: la journée
        """

        if self.IsDateConge(date):
            return State(ABSENT)

        inscription = self.GetInscription(date)
        if inscription is None:
            return State(ABSENT)

        reference = self.GetJourneeReference(date)
        heures_reference = reference.GetNombreHeures()
        ref_state = reference.GetState()  # TODO on peut s'en passer ?

        if date in self.journees:
            journee = self.journees[date]
            state = journee.GetState()  # TODO on peut s'en passer ?
            if state in (MALADE, HOPITAL, ABSENCE_NON_PREVENUE, ABSENCE_CONGE_SANS_PREAVIS):
                return State(state, heures_reference, 0, heures_reference)
            elif state in (ABSENT, VACANCES):
                if inscription.mode == MODE_5_5 or ref_state:
                    return State(VACANCES, heures_reference, 0, heures_reference)
                else:
                    return State(ABSENT, heures_reference, 0, heures_reference)
            else:  # PRESENT
                tranche = 5.0 / 60
                heures_realisees = 0.0
                heures_facturees = 0.0

                for start, end, value in journee.activites:
                    if value in (0, PREVISIONNEL):
                        heures_realisees += tranche * GetDureeArrondie(creche.arrondi_heures, start, end)

                union = GetUnionHeures(journee, reference)
                if inscription.IsInPeriodeAdaptation(date):
                    for start, end in union:
                        heures_facturees += tranche * GetDureeArrondie(creche.arrondi_facturation_periode_adaptation, start, end)
                else:
                    for start, end in union:
                        heures_facturees += tranche * GetDureeArrondie(creche.arrondi_facturation, start, end)

                return State(PRESENT, heures_reference, heures_realisees, heures_facturees)
        else:
            if ref_state:
                if creche.presences_previsionnelles:
                    return State(PRESENT | PREVISIONNEL, heures_reference, heures_reference, heures_reference)
                else:
                    return State(PRESENT, heures_reference, heures_reference, heures_reference)
            else:
                return State(ABSENT)

    def GetExtraActivites(self, date):
        journee = self.GetJournee(date)
        if journee is None:
            return []
        return journee.GetExtraActivites()

    def GetTotalActivitesPresenceNonFacturee(self, date):
        journee = self.GetJournee(date)
        if journee is None:
            return 0.0
        return journee.GetTotalActivitesPresenceNonFacturee()

    def GetDecomptePermanences(self):
        total, effectue = 0.0, 0.0
        date = creche.date_raz_permanences
        if date:
            while date < today:
                journee = self.GetJournee(date)
                if journee:
                    effectue += journee.GetTotalPermanences()
                date += datetime.timedelta(1)
            anniversaire = GetDateAnniversaire(creche.date_raz_permanences)
            for inscription in self.inscriptions:
                if inscription.debut is not None and creche.date_raz_permanences <= inscription.debut < today:
                    fin = inscription.fin if inscription.fin else anniversaire
                    if fin < today:
                        total += inscription.heures_permanences
                    else:
                        total += inscription.heures_permanences * (today - inscription.debut).days / (fin - inscription.debut).days
        return total, effectue

    def GetRegime(self, date):
        result = 0
        for parent in self.famille.parents:
            if parent:
                revenu = Select(parent.revenus, date)
                if revenu and revenu.regime:
                    result = revenu.regime
                    break
        return result

    def __cmp__(self, other):
        if other is self:
            return 0
        if not isinstance(other, Inscrit):
            return 1
        return cmp("%s %s" % (self.prenom, self.nom), "%s %s" % (other.prenom, other.nom))


class Alerte(object):
    def __init__(self, date, texte, acquittement=False, creation=True):
        self.idx = None
        self.date = date
        self.texte = texte
        self.acquittement = acquittement
        if creation:
            self.create()

    def create(self):
        print 'nouvelle alerte'
        result = sql_connection.execute('INSERT INTO ALERTES (idx, date, texte, acquittement) VALUES(NULL,?,?,?)',
                                        (self.date, self.texte, self.acquittement))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression alerte'
        sql_connection.execute('DELETE FROM ALERTES WHERE idx=?', (self.idx,))

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        if name in ['acquittement'] and self.idx:
            print 'update', name
            sql_connection.execute('UPDATE ALERTES SET %s=? WHERE idx=?' % name, (value, self.idx))


class Encaissement(SQLObject):
    table = "ENCAISSEMENTS"

    def __init__(self, famille, date=today, valeur=0, moyen_paiement=0, idx=None):
        self.ready = False
        self.idx = idx
        self.famille = famille
        self.date = date
        self.valeur = valeur
        self.moyen_paiement = moyen_paiement
        self.ready = True
        if idx is None:
            self.create()

    def create(self):
        print 'nouvel encaissement'
        result = sql_connection.execute(
            'INSERT INTO ENCAISSEMENTS (idx, famille, date, valeur, moyen_paiement) VALUES (NULL,?,?,?,?)',
            (self.famille.idx, self.date, self.valeur, self.moyen_paiement))
        self.idx = result.lastrowid

    def delete(self):
        print 'suppression encaissement'
        sql_connection.execute('DELETE FROM ENCAISSEMENTS WHERE idx=?', (self.idx,))
        self.idx = None

    def __setattr__(self, name, value):
        self.__dict__[name] = value

        if self.ready and name in ['date', 'valeur', 'moyen_paiement']:
            print 'update', name
            sql_connection.execute('UPDATE ENCAISSEMENTS SET %s=? WHERE idx=?' % name, (value, self.idx))
