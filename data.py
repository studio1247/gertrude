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

import __builtin__
import requests
import os.path
import shutil
import uuid

from functions import *
from sqlinterface import SQLConnection

if sys.platform == "win32":
    BACKUPS_DIRECTORY = "./backups"
else:
    BACKUPS_DIRECTORY = GERTRUDE_DIRECTORY + '/backups'
TOKEN_FILENAME = '.token'


class HttpConnection(object):
    def __init__(self, url, filename, identity, auth_info=None, proxy_info=None):
        self.url = url
        self.filename = filename
        self.identity = identity
        self.auth = auth_info
        if proxy_info:
            if 'user' in proxy_info:
                self.proxies = {"http": "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info}
            else:
                self.proxies = {"http": "http://%(host)s:%(port)d" % proxy_info}
        else:
            self.proxies = None
        if os.path.isfile(TOKEN_FILENAME):
            self.token = file(TOKEN_FILENAME).read()
            self.check_token()
        else:
            self.token = 0
        self.progress_handler = default_progress_handler

    def get_url(self, action):
        result = "%s?action=%s&identity=%s" % (self.url, action, self.identity)
        if self.token:
            result += "&token=%s" % self.token
        return result

    def send_action(self, action):
        url = self.get_url(action)
        print url
        response = requests.get(url, auth=self.auth, proxies=self.proxies)
        if response.status_code != requests.codes.ok:
            return 0
        result = response.content
        try:
            # (pas sur mac)
            print '=>', result[:64]
        except:
            pass
        if result.isdigit():
            return int(result)
        else:
            return 0

    def get_server_data(self, action):
        url = self.get_url(action)
        print url
        response = requests.get(url, auth=self.auth, proxies=self.proxies)
        if response.status_code != requests.codes.ok:
            return 0
        return response.content

    def has_token(self):
        self.progress_handler.display("Vérification du jeton ...")
        return self.token and self.send_action('has_token')

    def check_token(self):
        try:
            if self.token == '0' or '<' in self.token or '>' in self.token or '&' in self.token:
                self.token = 0
        except:
            self.token = 0
                
    def get_token(self):
        self.progress_handler.display("Récupération du jeton ...")
        if force_token:
            self.token = self.get_server_data('force_token')
        else:
            self.token = self.get_server_data('get_token')
        print self.token
        self.check_token()
        if not self.token:
            return 0
        else:
            file(TOKEN_FILENAME, 'w').write(self.token)
            return 1

    def rel_token(self):
        if not self.token:
            return 1
        self.progress_handler.display("Libération du jeton ...")
        if not self.send_action('rel_token'):
            self.progress_handler.display("Libération du jeton refusée...")
            time.sleep(1)
            return 0
        else:
            self.progress_handler.display("Libération du jeton accordée...")
            time.sleep(1)
            self.token = 0
            if os.path.exists(TOKEN_FILENAME):
                os.remove(TOKEN_FILENAME)
            return 1

    def do_download(self):
        self.progress_handler.display("Téléchargement de la base ...")
        data = self.get_server_data('download')
        if data:
            f = file(self.filename, 'wb')
            f.write(data)
            f.close()
            self.progress_handler.display('%d octets transférés.' % len(data))
        else:
            self.progress_handler.display('Pas de base présente sur le serveur.')
            if os.path.isfile(self.filename):
                self.progress_handler.display("Utilisation de la base locale ...")
        return 1

    def download(self):       
        if self.has_token():
            self.progress_handler.display("Jeton déjà pris => pas de download")
            return 1
        elif self.get_token():
            self.progress_handler.set(30)
            if self.do_download():
                self.progress_handler.set(90)
                return 1
            else:
                self.progress_handler.set(90)
                self.rel_token()
                self.progress_handler.display("Le download a échoué")
                return 0
        else:
            self.progress_handler.display("Impossible de prendre le jeton.")
            return 0
       
    def do_upload(self):
        self.progress_handler.display("Envoi vers le serveur ...")
        files = {'database': ('database', open(self.filename, 'rb'))}
        try:
            response = requests.post(self.get_url("upload"), files=files, auth=self.auth, proxies=self.proxies)
            if len(response.content) == 1:
                return eval(response.content)
            else:
                return response.content
        except Exception, e:
            raise

    def upload(self):
        if not self.has_token():
            self.progress_handler.display("Pas de jeton présent => pas d'envoi vers le serveur.")
            return 0
        return self.do_upload()

    def Liste(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.do_download():
            return FileConnection(self.filename).Liste(progress_handler)
        else:
            return []
        
    def Load(self, progress_handler=default_progress_handler, autosave=False):
        self.progress_handler = progress_handler
        if self.download():
            result = FileConnection(self.filename).Load(progress_handler, autosave)
        elif self.do_download():
            result = FileConnection(self.filename).Load(progress_handler, autosave)[0], 1
        else:
            result = None, 0
        return result
    
    def LoadJournal(self):
        return self.get_server_data('journal')

    def Update(self):
        return None, None
    
    def Save(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Save() and self.upload()

    def Restore(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Restore()
    
    def Exit(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Save() and self.rel_token()


class SharedFileConnection(object):
    def __init__(self, url, filename, identity):
        self.url = url
        self.token_url = self.url + ".token"
        self.filename = filename
        if identity:
            self.identity = identity
        else:
            self.identity = str(uuid.uuid4())
        self.token = self.read_token(TOKEN_FILENAME)
        self.progress_handler = default_progress_handler
    
    @staticmethod
    def read_token(filename):
        try:
            return file(filename).read()
        except:
            return None
            
    def has_token(self):
        self.progress_handler.display("Vérification du jeton ...")
        return self.token and self.token == self.read_token(self.token_url)

    def get_token(self):
        self.progress_handler.display("Récupération du jeton ...")
        if force_token or self.read_token(self.token_url) is None:
            self.token = self.identity
            file(TOKEN_FILENAME, 'w').write(self.token)
            file(self.token_url, 'w').write(self.token)
            return 1
        else:
            return 0

    def rel_token(self):
        if not self.token:
            return 1
        self.progress_handler.display("Libération du jeton ...")
        if self.read_token(self.token_url) == self.token:
            os.remove(self.token_url)
            os.remove(TOKEN_FILENAME)
            self.progress_handler.display("Libération du jeton accordée ...")
            time.sleep(1)
            self.token = None
            return 1
        else:
            self.progress_handler.display("Libération du jeton refusée ...")
            time.sleep(1)
            return 0

    def do_download(self):
        self.progress_handler.display("Téléchargement de la base ...")
        if os.path.isfile(self.url):
            shutil.copyfile(self.url, self.filename)
        else:
            self.progress_handler.display('Pas de base présente sur le serveur.')
            if os.path.isfile(self.filename):
                self.progress_handler.display("Utilisation de la base locale ...")
        return 1

    def download(self):       
        if self.has_token():
            self.progress_handler.display("Jeton déjà pris => pas de download")
            return 1
        elif self.get_token():
            self.progress_handler.set(30)
            if self.do_download():
                self.progress_handler.set(90)
                return 1
            else:
                self.progress_handler.set(90)
                self.rel_token()
                self.progress_handler.display("Le download a échoué")
                return 0
        else:
            self.progress_handler.display("Impossible de prendre le jeton.")
            return 0
       
    def do_upload(self):
        shutil.copyfile(self.filename, self.url)
        return 1

    def upload(self):
        if not self.has_token():
            self.progress_handler.display("Pas de jeton présent => pas d'envoi vers le serveur.")
            return 0
        return self.do_upload()

    def Liste(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.do_download():
            return FileConnection(self.filename).Liste(progress_handler)
        else:
            return []
        
    def Load(self, progress_handler=default_progress_handler, autosave=False):
        self.progress_handler = progress_handler
        if self.download():
            result = FileConnection(self.filename).Load(progress_handler, autosave)
        elif self.do_download():
            result = FileConnection(self.filename).Load(progress_handler, autosave)[0], 1
        else:
            result = None, 0
        return result

    def Update(self):
        return None, None
    
    def Save(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Save() and self.upload()

    def Restore(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Restore()
    
    def Exit(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        return FileConnection(self.filename).Save() and self.rel_token()


class FileConnection(object):
    def __init__(self, filename):
        self.filename = filename
        self.backup = None

    def Backup(self, progress_handler=default_progress_handler):
        if not config.options & NO_BACKUPS:
            progress_handler.display('Sauvegarde ...')
            try:
                if os.path.isfile(self.filename):
                    if not os.path.isdir(BACKUPS_DIRECTORY):
                        os.makedirs(BACKUPS_DIRECTORY)
                    self.backup = 'backup_%s_%d.db' % (os.path.split(self.filename)[1], time.time())
                    shutil.copyfile(self.filename, BACKUPS_DIRECTORY + '/' + self.backup)
            except Exception, e:
                progress_handler.display('Impossible de faire la sauvegarde' + str(e))
    
    def Liste(self, progress_handler=default_progress_handler):
        if not os.path.isfile(self.filename):
            return []
        try:
            connection = SQLConnection(self.filename)
            return connection.Liste()
        except:
            return []
    
    def Update(self):
        _sql_connection, _creche = None, None
        try:
            if self.file_mtime < os.stat(self.filename).st_mtime:
                self.file_mtime = os.stat(self.filename).st_mtime
                _sql_connection = SQLConnection(self.filename)
                _creche = _sql_connection.Load(None)
        except Exception, e:
            print e
        return _sql_connection, _creche
    
    def Load(self, progress_handler=default_progress_handler, autosave=False):
        if os.path.isfile(self.filename):
            self.file_mtime = os.stat(self.filename).st_mtime
            self.Backup(progress_handler)
        __builtin__.sql_connection = SQLConnection(self.filename)
        if not os.path.isfile(self.filename):
            try:
                sql_connection.Create(progress_handler)
            except:
                sql_connection.close()
                os.remove(self.filename)
                raise
        creche = sql_connection.Load(progress_handler, autosave)
        return creche, 0

    def Save(self, progress_handler=default_progress_handler):
        sql_connection.commit()
        self.Backup(progress_handler)
        return True
    
    def Restore(self, progress_handler=default_progress_handler):
        sql_connection.commit()
        sql_connection.close()
        backup = self.backup
        self.Backup(progress_handler)
        if backup:
            shutil.copyfile(BACKUPS_DIRECTORY + '/' + backup, self.filename)
        return True

    def Exit(self, progress_handler=default_progress_handler):
        sql_connection.commit()
        sql_connection.close()
        return True

    def LoadJournal(self):
        directory = os.path.dirname(self.filename)
        journal_path = os.path.join(directory, 'journal.txt')
        if os.path.isfile(journal_path):
            return file(journal_path).read()
        else:
            return None
