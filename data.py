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

import __builtin__
import os.path, shutil, time
import urllib2, mimetypes, uuid
import ConfigParser
from sqlinterface import SQLConnection
from functions import *

BACKUPS_DIRECTORY = './backups'
TOKEN_FILENAME = '.token'

class HttpConnection(object):
    def __init__(self, url, filename, identity, auth_info=None, proxy_info=None):
        self.url = url
        self.filename = filename
        self.identity = identity
        self.auth_info = auth_info
        self.proxy_info = proxy_info
        if os.path.isfile(TOKEN_FILENAME):
            self.token = file(TOKEN_FILENAME).read()
            self.check_token()
        else:
            self.token = 0
        self.progress_handler = default_progress_handler

    def get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def encode_multipart_formdata(self, fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
        CRLF = '\r\n'
        L = []
        for (key, value) in fields:
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="%s"' % key)
                L.append('')
                L.append(value)
        for (key, filename) in files:
                L.append('--' + BOUNDARY)
                L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
                L.append('Content-Type: %s' % self.get_content_type(filename))
                L.append('Content-Transfer-Encoding: binary')
                L.append('')
                fp = file(filename, 'rb')
                L.append(fp.read())
                fp.close()
        L.append('--' + BOUNDARY + '--')
        L.append('')
        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body

    def urlopen(self, action, body=None, headers=None):
        opener = urllib2.build_opener()
        if self.auth_info:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.url, self.auth_info[0], self.auth_info[1])
            opener.add_handler(urllib2.HTTPBasicAuthHandler(password_mgr))
        if self.proxy_info:
            opener.add_handler(urllib2.ProxyHandler({"http" : "http://%(user)s:%(pass)s@%(host)s:%(port)d" % self.proxy_info}))
        urllib2.install_opener(opener)

        try:
            url = '%s?action=%s&identity=%s' % (self.url, action, self.identity)
            print url
            if self.token:
                url += "&token=%s" % self.token
            # print url
            if body:
                req = urllib2.Request(url, body, headers)
            else:
                req = urllib2.Request(url)
            result = urllib2.urlopen(req).read()
            print '=>', result[:64]
            if len(result) == 1:
                return eval(result)
            else:
                return result
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Exception(u"Echec - code 404 (page non trouvée)")
            else:
                raise Exception(u"Echec - code %d (%s)" % (e.code, e.msg))
        except urllib2.URLError, e:
            raise Exception("Echec - cause:", e.reason)
        except Exception, e:
            raise

    def has_token(self):
        self.progress_handler.display(u"Vérification du jeton ...")
        return self.token and self.urlopen('has_token')

    def check_token(self):
        try:
            if '<' in self.token or '>' in self.token or '&' in self.token:
                self.token = 0
        except:
            self.token = 0
                
    def get_token(self):
        self.progress_handler.display(u"Récupération du jeton ...")
        if force_token:
            self.token = self.urlopen('force_token')
        else:
            self.token = self.urlopen('get_token')
        self.check_token()
        if not self.token:
            return 0
        else:
            file(TOKEN_FILENAME, 'w').write(self.token)
            return 1

    def rel_token(self):
        if not self.token:
            return 1
        self.progress_handler.display(u"Libération du jeton ...")
        if not self.urlopen('rel_token'):
            self.progress_handler.display(u"Libération du jeton refusée...")
            time.sleep(1)
            return 0
        else:
            self.progress_handler.display(u"Libération du jeton accordée...")
            time.sleep(1)
            self.token = 0
            if os.path.exists(TOKEN_FILENAME):
                os.remove(TOKEN_FILENAME)
            return 1

    def do_download(self):
        self.progress_handler.display(u"Téléchargement de la base ...")
        data = self.urlopen('download')
        if data:
            f = file(self.filename, 'wb')
            f.write(data)
            f.close()
            self.progress_handler.display(u'%d octets transférés.' % len(data))
        else:
            self.progress_handler.display(u'Pas de base présente sur le serveur.')
            if os.path.isfile(self.filename):
                self.progress_handler.display("Utilisation de la base locale ...")
        return 1

    def download(self):       
        if self.has_token():
            self.progress_handler.display(u"Jeton déjà pris => pas de download")
            return 1
        elif self.get_token():
            self.progress_handler.set(30)
            if self.do_download():
                self.progress_handler.set(90)
                return 1
            else:
                self.progress_handler.set(90)
                self.rel_token()
                self.progress_handler.display(u"Le download a échoué")
                return 0
        else:
            self.progress_handler.display("Impossible de prendre le jeton.")
            return 0
       
    def do_upload(self):
        self.progress_handler.display("Envoi vers le serveur ...")
        content_type, body = self.encode_multipart_formdata([], [("database", self.filename)])
        headers = {"Content-Type": content_type, 'Content-Length': str(len(body))}
        return self.urlopen('upload', body, headers)

    def upload(self):
        if not self.has_token():
            self.progress_handler.display(u"Pas de jeton présent => pas d'envoi vers le serveur.")
            return 0
        return self.do_upload()

    def Liste(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.do_download():
            return FileConnection(self.filename).Liste(progress_handler)
        else:
            return []
        
    def Load(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.download():
            result = FileConnection(self.filename).Load(progress_handler)
        elif self.do_download():
            result = FileConnection(self.filename).Load(progress_handler)[0], 1
        else:
            result = None, 0
        return result
    
    def LoadJournal(self):
        return self.urlopen('journal')

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
    
    def read_token(self, filename):
        try:
            return file(filename).read()
        except:
            return None
            
    def has_token(self):
        self.progress_handler.display(u"Vérification du jeton ...")
        return self.token and self.token == self.read_token(self.token_url)

    def get_token(self):
        self.progress_handler.display(u"Récupération du jeton ...")
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
        self.progress_handler.display(u"Libération du jeton ...")
        if self.read_token(self.token_url) == self.token:
            os.remove(self.token_url)
            os.remove(TOKEN_FILENAME)
            self.progress_handler.display(u"Libération du jeton accordée...")
            time.sleep(1)
            self.token = None
            return 1
        else:
            self.progress_handler.display(u"Libération du jeton refusée...")
            time.sleep(1)
            return 0

    def do_download(self):
        self.progress_handler.display(u"Téléchargement de la base ...")
        if os.path.isfile(self.url):
            shutil.copyfile(self.url, self.filename)
        else:
            self.progress_handler.display(u'Pas de base présente sur le serveur.')
            if os.path.isfile(self.filename):
                self.progress_handler.display("Utilisation de la base locale ...")
        return 1

    def download(self):       
        if self.has_token():
            self.progress_handler.display(u"Jeton déjà pris => pas de download")
            return 1
        elif self.get_token():
            self.progress_handler.set(30)
            if self.do_download():
                self.progress_handler.set(90)
                return 1
            else:
                self.progress_handler.set(90)
                self.rel_token()
                self.progress_handler.display(u"Le download a échoué")
                return 0
        else:
            self.progress_handler.display("Impossible de prendre le jeton.")
            return 0
       
    def do_upload(self):
        shutil.copyfile(self.filename, self.url)
        return 1

    def upload(self):
        if not self.has_token():
            self.progress_handler.display(u"Pas de jeton présent => pas d'envoi vers le serveur.")
            return 0
        return self.do_upload()

    def Liste(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.do_download():
            return FileConnection(self.filename).Liste(progress_handler)
        else:
            return []
        
    def Load(self, progress_handler=default_progress_handler):
        self.progress_handler = progress_handler
        if self.download():
            result = FileConnection(self.filename).Load(progress_handler)
        elif self.do_download():
            result = FileConnection(self.filename).Load(progress_handler)[0], 1
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
        progress_handler.display('Sauvegarde ...')
        try:
            if os.path.isfile(self.filename):
                if not os.path.isdir(BACKUPS_DIRECTORY):
                    os.mkdir(BACKUPS_DIRECTORY)
                self.backup = 'backup_%s_%d.db' % (self.filename, time.time())
                shutil.copyfile(self.filename, BACKUPS_DIRECTORY + '/' + self.backup)
        except Exception, e:
            progress_handler.display('Impossible de faire la sauvegarde' + e)
    
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
    
    def Load(self, progress_handler=default_progress_handler):
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
        creche = sql_connection.Load(progress_handler)
        return creche, 0

    def Save(self, progress_handler=default_progress_handler):
        sql_connection.commit()
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

