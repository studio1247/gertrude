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

import __builtin__
import os.path, shutil, time
import urllib2, mimetypes
import ConfigParser
import sqlinterface

def default_handler(count=None, msg=None, max=None):
    if msg: print msg
    if max: return default_handler

BACKUPS_DIRECTORY = './backups'
def Backup(handler=default_handler):
    handler(msg='Sauvegarde ...')
    if os.path.isfile('gertrude.db'):
        if not os.path.isdir(BACKUPS_DIRECTORY):
            os.mkdir(BACKUPS_DIRECTORY)
        backup_filename = 'backup_%d.db' % time.time()
        shutil.copyfile('gertrude.db', BACKUPS_DIRECTORY + '/' + backup_filename)
    handler(100)

TOKEN_FILENAME = '.token'

    
class HttpConnection(object):
    def __init__(self, url, auth_info=None, proxy_info=None):
        self.url = url
        opener = urllib2.build_opener()
        if auth_info:
            password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, url, auth_info[0], auth_info[1])
            opener.add_handler(urllib2.HTTPBasicAuthHandler(password_mgr))
        if proxy_info:
            opener.add_handler(urllib2.ProxyHandler({"http" : "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info}))
        urllib2.install_opener(opener)
        if os.path.isfile(TOKEN_FILENAME):
            self.token = file(TOKEN_FILENAME).read()
        else:
            self.token = 0
        self.handler = default_handler

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


    def urlopen(self, action, body=None, headers=None, decode=True):
        try:
            url = '%s?action=%s' % (self.url, action)
            if self.token:
                url += "&token=%s" % self.token
            # print url
            if body:
                req = urllib2.Request(url, body, headers)
            else:
                req = urllib2.Request(url)
            result = urllib2.urlopen(req).read()
            print result[:100]
            if decode:
                return eval(result)
            else:
                return result
        except urllib2.HTTPError, e:
            if e.code == 404:
                print "Echec - page non trouvée"
                return None
            else:
                print "Echec - code %d (%s)" % (e.code, e.msg)
                return None
        except urllib2.URLError, e:
            print "Echec - cause:", e.reason
            return None
        except Exception, e:
            print "Echec - exception:", e
            return None

    def has_token(self):
        self.handler(msg=u"Vérification du jeton ...")
        return self.token and self.urlopen('has_token')

    def get_token(self):
        self.handler(msg=u"Récupération du jeton ...")
        self.token = self.urlopen('get_token', decode=False)
        if not self.token or self.token == "0":
            return 0
        else:
            file(TOKEN_FILENAME, 'w').write(self.token)
            return 1

    def rel_token(self):
        self.handler(msg=u"Libération du jeton ...")
        if not self.urlopen('rel_token'):
            return 0
        else:
            if os.path.exists(TOKEN_FILENAME):
                os.remove(TOKEN_FILENAME)
            return 1

    def do_download(self):
        self.handler(msg=u"Téléchargement de la base ...")
        data = self.urlopen('download', decode=False)
        if data:
            f = file('./gertrude.db', 'wb')
            f.write(data)
            f.close()
            print '%d bytes writen' % len(data)
            return 1
        else:
            return 0

    def download(self):       
        if self.has_token():
            self.handler(msg=u"Jeton déjà pris => pas de download")
            return 1
        elif self.get_token():
            self.handler(30)
            if self.do_download():
                self.handler(90)
                return 1
            else:
                self.handler(90)
                self.rel_token()
                self.handler(msg=u"Le download a échoué")
                return 0
        else:
            self.handler(msg="Impossible de prendre le jeton.")
            return 0
       
    def do_upload(self):
        self.handler(msg="Envoi vers le serveur ...")
        content_type, body = self.encode_multipart_formdata([], [("database", "./gertrude.db")])
        headers = {"Content-Type": content_type, 'Content-Length': str(len(body))}
        return self.urlopen('upload', body, headers)

    def upload(self):
        if not self.has_token():
            self.handler(u"Pas de jeton présent => pas d'envoi vers le serveur.")
            return 0
        if self.do_upload():
            return self.rel_token()
        else:
            return 0

    def Load(self, handler=default_handler):
        self.handler = handler
        if self.download():
            result = FileConnection().Load()
        elif self.do_download():
            result = FileConnection().Load()[0], 1
        else:
            result = None, 0
        handler(100)
        return result

    def Save(self, handler=default_handler):
        self.handler = handler
        return FileConnection().Save() and self.upload()

class FileConnection(object):
    def __init__(self):
        pass
    
    def Load(self, handler=default_handler):
        creche = sql_connection.load()
        handler(100)
        return creche, 0

    def Save(self, handler=default_handler):
        sql_connection.close()
        handler(100)
        return True

def getConnection():
    parser = ConfigParser.ConfigParser()
    parser.read("./gertrude.ini")
    url = parser.get("gertrude", "url")
    if url.startswith("http://"):
        try:
            auth_info = (parser.get("gertrude", "login"), parser.get("gertrude", "password"))
        except:
            auth_info = None
        try:
            proxy_info = { 'host' : parser.get("gertrude", "proxy-host"),
                           'port' : int(parser.get("gertrude", "proxy-port")),
                           'user' : parser.get("gertrude", "proxy-user"),
                           'pass' : parser.get("gertrude", "proxy-pass")
                           }
        except:
            proxy_info = None
        connection = HttpConnection(url, auth_info, proxy_info)
    else:
        connection = FileConnection()
    return connection

def Load(handler=default_handler):
    connection = getConnection()
    handler(10)
    __builtin__.creche, __builtin__.readonly = connection.Load(handler(max=90))
    handler(100)
    return creche is not None

def Save(handler=default_handler):
    connection = getConnection()
    return connection.Save(handler(max=100))
    
if __name__ == '__main__':
    loaded = Load()
    if loaded and not readonly:
        Save()    
