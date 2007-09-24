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

import __builtin__
import os.path, binascii, shutil, socket
import wx
from ftplib import FTP
import urllib2
from threading import Thread
from common import *
import time, datetime
from sqlinterface import *
from translations import Translate

def Backup():
    if os.path.isfile('gertrude.db'):
        if not os.path.isdir(backups_directory):
            os.mkdir(backups_directory)

        backup_filename = 'backup_%d.db' % time.time()
        shutil.copyfile('gertrude.db', backups_directory + '/' + backup_filename)

def urlopen(action):
    return urllib2.urlopen('%s?action=%s&login=%s&pass=%s' % (creche.server_url, action, login, password))

def hasLock():
    return os.path.isfile('.lock')

def Lock():
    print "Lock()"
    try:
        urlfile = urlopen('lock')
    except urllib2.HTTPError, exc:
        if exc.code == 404:
            print "Page non trouvée !"
            return 0
        else:
            print "La requête HTTP a échoué avec le code %d (%s)" % (exc.code, exc.msg)
            return 0
    except urllib2.URLError, exc:
        print "Echec. Cause:", exc.reason
        return 0
    file('.lock', 'w')
    return 1

def Unlock():
    print "Unlock()"
    try:
        urlfile = urlopen('unlock')
    except urllib2.HTTPError, exc:
        if exc.code == 404:
            print "Page non trouvée !"
            return 0
        else:
            print "La requête HTTP a échoué avec le code %d (%s)" % (exc.code, exc.msg)
            return 0
    except urllib2.URLError, exc:
        print "Echec. Cause:", exc.reason
        return 0
    os.remove('.lock')
    return 1

def Download():
    print "Download()"
    try:
        urlfile = urlopen('download')
    except urllib2.HTTPError, exc:
        if exc.code == 404:
            print "Page non trouvée !"
            return 0
        else:
            print "La requête HTTP a échoué avec le code %d (%s)" % (exc.code, exc.msg)
            return 0
    except urllib2.URLError, exc:
        print "Echec. Cause:", exc.reason
        return 0

def Upload():
    print "Upload()"
    try:
        urlfile = urlopen('upload')
    except urllib2.HTTPError, exc:
        if exc.code == 404:
            print "Page non trouvée !"
            return 0
        else:
            print "La requête HTTP a échoué avec le code %d (%s)" % (exc.code, exc.msg)
            return 0
    except urllib2.URLError, exc:
        print "Echec. Cause:", exc.reason
        return 0

def LockAndDownload():
    if hasLock():
        Upload()
    elif Lock():
        Download()

def UploadAndUnlock():
    if Upload():
        Unlock()

class SynchroDialog(wx.Dialog):
    def __init__(self, parent, server):
        wx.Dialog.__init__(self, parent, -1, "Synchronisation", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE | wx.CAPTION | wx.SYSTEM_MENU | wx.THICK_FRAME)
        self.server = server

        topsizer = wx.BoxSizer(wx.VERTICAL)

        self.listbox = wx.ListBox(self, -1, size=(302, 100))
        topsizer.Add(self.listbox, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.gauge = wx.Gauge(self, -1, size=(302, 24))
        self.gauge.SetRange(20)
        topsizer.Add(self.gauge, 50, wx.ALIGN_CENTRE|wx.ALL, 10)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.synchrobutton = wx.Button(self, -1, " Synchroniser ")
        self.synchrobutton.Disable()
        self.Bind(wx.EVT_BUTTON, self.onSynchroButton, self.synchrobutton)
        sizer.Add(self.synchrobutton, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.cancelbutton = wx.Button(self, wx.ID_CANCEL, " Annuler ")
        self.cancelbutton.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.onCancelButton, self.cancelbutton)
        sizer.Add(self.cancelbutton, 0, wx.ALIGN_CENTRE|wx.ALL, 10)

        topsizer.Add(sizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.SetSizer(topsizer)
        topsizer.Fit(self)

        self.thread = Thread(target=self.GetInfos)
        self.result = None
        self.thread.start()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnGetInfosTimer)
        self.timer.Start(1000)

    def GetInfos(self):
        lines = []

        def callback(line):
            lines.append(line)

        try:
            self.ftp = FTP(self.server)
            self.ftp.login("gertude", "schlemel")
            self.ftp.retrlines('LIST', callback)
            for line in lines:
                if 'last' in line:
                    result = line
            self.ftp.retrlines('RETR last', callback)
            self.FTPFilename, self.lasttime = lines[-1].split()
            localFile = file(backups_directory + "/" + self.FTPFilename, 'wb')
            self.ftp.retrbinary('RETR %s' % self.FTPFilename, localFile.write)
            localFile.close()
            self.result = result
        except:
            self.result = "echec"

    def OnGetInfosTimer(self, event):
        if self.result == None:
            self.gauge.SetValue(self.gauge.GetValue() + 1)
        else:
            if self.result == "echec":
                self.listbox.Append(u'La connexion a échoué', 1)
            elif self.result == "rien":
                self.listbox.Append("Fichier local", 1)
                self.synchrobutton.Enable()
            else:
                self.listbox.Append(u'Sauvegarde réseau du %s' % unicode(datetime.datetime.fromtimestamp(float(self.lasttime)).strftime('%A %d %b %Y à %H:%M:%S'), 'iso8859-1'), 0)
                self.listbox.Append('Sauvegarde locale', 1)
                self.synchrobutton.Enable()
            self.timer.Stop()

    def onCancelButton(self, event):
        self.timer.Stop()
        event.Skip()

    def onSynchroButton(self, event):
        sel = self.listbox.GetSelection()
        if sel != -1:
            self.cancelbutton.Disable()
            value = self.listbox.GetClientData(sel)
            if value == 1:
                # Fichier local
                connection.commit()
                name = self.FTPFilename.split('.')[0]
                index = int(name.split('_')[1])
                distantFilename = 'ftpbackup_%d.db' % (index+1)
                self.ftp.storbinary("STOR " + distantFilename, file('gertrude.db', 'rb'))
                file('last', 'w').write('%s %s' % (distantFilename, time.time()))
                self.ftp.storlines('STOR last', file('last', 'r'))
                result = wx.ID_OK
            elif value == 0:
                # Fichier distant
                connection.close()
                Backup()
                shutil.copyfile(backups_directory + "/" + self.FTPFilename, './gertrude.db')
                result = ID_SYNCHRO

            self.ftp.quit()
            self.EndModal(result)

def Load():
    def getdate(str):
        if str is None:
            return None
        annee, mois, jour = map(lambda x: int(x), str.split('-'))
        return datetime.date(annee, mois, jour)

    Translate()

    cur = connection.cursor()

    cur.execute('SELECT nom, adresse, code_postal, ville, server_url, mois_payes, presences_previsionnelles, modes_inscription, idx FROM CRECHE')
    creche_entry = cur.fetchall()
    if len(creche_entry) > 0:
        creche = Creche(creation=False)
        creche.nom, creche.adresse, creche.code_postal, creche.ville, creche.server_url, creche.mois_payes, creche.presences_previsionnelles, creche.modes_inscription, creche.idx = creche_entry[0]
    else:
        creche = Creche()

    cur.execute('SELECT login, password, profile, idx FROM USERS')
    for users_entry in cur.fetchall():
        user = User(creation=False)
        user.login, user.password, user.profile, user.idx = users_entry
        creche.users.append(user)

    cur.execute('SELECT debut, fin, idx FROM CONGES')
    for conges_entry in cur.fetchall():
        conge = Conge(creation=False)
        conge.debut, conge.fin, conge.idx = conges_entry
        creche.add_conge(conge)

    cur.execute('SELECT debut, fin, plancher, plafond, idx FROM BAREMESCAF')
    for bareme_entry in cur.fetchall():
        bareme = BaremeCAF(creation=False)
        bareme.debut, bareme.fin, bareme.plancher, bareme.plafond, idx = bareme_entry
	bareme.debut, bareme.fin, bareme.idx = getdate(bareme.debut), getdate(bareme.fin), idx
        creche.baremes_caf.append(bareme)

    cur.execute('SELECT date_embauche, prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, email, idx FROM EMPLOYES')
    for employe_entry in cur.fetchall():
        employe = Employe(creation=False)
        employe.date_embauche = getdate(employe_entry[0])
        employe.prenom, employe.nom, employe.telephone_domicile, employe.telephone_domicile_notes, employe.telephone_portable, employe.telephone_portable_notes, employe.email, employe.idx = employe_entry[1:]
        creche.employes.append(employe)

    parents = {None: None}
    cur.execute('SELECT idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, marche, photo FROM INSCRITS')
    for idx, prenom, nom, sexe, naissance, adresse, code_postal, ville, marche, photo in cur.fetchall():
        if photo:
            photo = binascii.a2b_base64(photo)
        inscrit = Inscrit(creation=False)
        creche.inscrits.append(inscrit)
        inscrit.prenom, inscrit.nom, inscrit.sexe, inscrit.naissance, inscrit.adresse, inscrit.code_postal, inscrit.ville, inscrit.marche, inscrit.photo, inscrit.idx = prenom, nom, sexe, getdate(naissance), adresse, code_postal, ville, getdate(marche), photo, idx
        cur.execute('SELECT prenom, naissance, entree, sortie, idx FROM FRATRIES WHERE inscrit=?', (inscrit.idx,))
        for frere_entry in cur.fetchall():
            frere = Frere_Soeur(inscrit, creation=False)
            frere.prenom, frere.naissance, frere.entree, frere.sortie, idx = frere_entry
            frere.naissance, frere.entree, frere.sortie, frere.idx = getdate(frere.naissance), getdate(frere.entree), getdate(frere.sortie), idx
            inscrit.freres_soeurs.append(frere)
        cur.execute('SELECT idx, debut, fin, mode, periode_reference, fin_periode_essai FROM INSCRIPTIONS WHERE inscrit=?', (inscrit.idx,))
        for idx, debut, fin, mode, periode_reference, fin_periode_essai in cur.fetchall():
            inscription = Inscription(inscrit, creation=False)
            inscription.debut, inscription.fin, inscription.mode, inscription.periode_reference, inscription.fin_periode_essai, inscription.idx = getdate(debut), getdate(fin), mode, eval(periode_reference), getdate(fin_periode_essai), idx
            inscrit.inscriptions.append(inscription)
        cur.execute('SELECT prenom, nom, telephone_domicile, telephone_domicile_notes, telephone_portable, telephone_portable_notes, telephone_travail, telephone_travail_notes, email, idx FROM PARENTS WHERE inscrit=?', (inscrit.idx,))
        for parent_entry in cur.fetchall():
            parent = Parent(inscrit, creation=False)
            parent.prenom, parent.nom, parent.telephone_domicile, parent.telephone_domicile_notes, parent.telephone_portable, parent.telephone_portable_notes, parent.telephone_travail, parent.telephone_travail_notes, parent.email, parent.idx = parent_entry
            parents[parent.idx] = parent
            if not inscrit.papa:
                inscrit.papa = parent
            else:
                inscrit.maman = parent
            cur.execute('SELECT debut, fin, revenu, chomage, regime, idx FROM REVENUS WHERE parent=?', (parent.idx,))
            for revenu_entry in cur.fetchall():
                revenu = Revenu(parent, creation=False)
                revenu.debut, revenu.fin, revenu.revenu, revenu.chomage, revenu.regime, idx = revenu_entry
                revenu.debut, revenu.fin, revenu.idx = getdate(revenu.debut), getdate(revenu.fin), idx
                parent.revenus.append(revenu)
        cur.execute('SELECT date, previsionnel, value, details, idx FROM PRESENCES WHERE inscrit=?', (inscrit.idx,))
        for date, previsionnel, value, details, idx in cur.fetchall():
            presence = Presence(inscrit, getdate(date), previsionnel, value, creation=False)
            presence.set_details(details)
            presence.idx = idx
            inscrit.presences[getdate(date)] = presence

    cur.execute('SELECT idx, debut, fin, president, vice_president, tresorier, secretaire FROM BUREAUX')
    for idx, debut, fin, president, vice_president, tresorier, secretaire in cur.fetchall():
        bureau = Bureau(creation=False)
        bureau.debut, bureau.fin, bureau.president, bureau.vice_president, bureau.tresorier, bureau.secretaire, bureau.idx = getdate(debut), getdate(fin), parents[president], parents[vice_president], parents[tresorier], parents[secretaire], idx
        creche.bureaux.append(bureau)

    creche.inscrits.sort()
    return creche

if __name__ == '__main__':
    __builtin__.creche = Load()
    __builtin__.profil = 0
    __builtin__.login = "bertrand"
    __builtin__.password = "songis"
    creche.server_url = 'http://gertude.free.fr/gertrude'

    LockAndDownload()
    time.sleep(2)
    UploadAndUnlock()
