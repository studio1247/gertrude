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
import sys, os.path, shutil, time
import urllib2
import ConfigParser
from functions import *
from data import FileConnection, HttpConnection

CONFIG_FILENAME = "./gertrude.ini"
DOCUMENTS_DIRECTORY_FILENAME = "./.gertrude-docs"

class Config(object):
    def __init__(self):
        self.connection = FileConnection()

__builtin__.config = Config()

def LoadDocumentsDirectory():
    if os.path.isfile(DOCUMENTS_DIRECTORY_FILENAME):
        try:
            path = file(DOCUMENTS_DIRECTORY_FILENAME).read()
            if os.path.isdir(path):
                return path
        except:
            print "Problème d'interprétation du fichier %s" % DOCUMENTS_DIRECTORY_FILENAME
    
    if sys.platform == 'win32':
        try:
            from win32com.shell import shell
            df = shell.SHGetDesktopFolder()
            pidl = df.ParseDisplayName(0, None,
                                       "::{450d8fba-ad25-11d0-98a8-0800361b1103}")[1]
            return shell.SHGetPathFromIDList(pidl)
        except:
            print u"L'extension win32com pour python est recommandée (plateforme windows) !"
            
    return os.getcwd()

def SaveDocumentsDirectory(documents_directory):
    try:
        file(DOCUMENTS_DIRECTORY_FILENAME, "w").write(documents_directory)
    except:
        pass
    
def LoadConfig(progress_handler=default_progress_handler):
    progress_handler.display(u"Chargement de la configuration ...")

    config.documents_directory = LoadDocumentsDirectory()
    
    if not os.path.isfile(CONFIG_FILENAME):
        progress_handler.display(u"Pas de fichier gertrude.ini. Utilisation de la configuration par défaut.")
        return

    try:
        parser = ConfigParser.SafeConfigParser()
        parser.read(CONFIG_FILENAME)
    except:
        progress_handler.display(u"Fichier gertrude.ini erroné. Utilisation de la configuration par défaut.")
        return

    try:
        url = parser.get("gertrude", "url")
    except:
        progress_handler.display(u"Pas d'url définie. Utilisation de la configuration par défaut.")
        return

    if url.startswith("http://"):
        try:
            auth_info = (parser.get("gertrude", "login"), parser.get("gertrude", "password"))
        except:
            auth_info = None
        try:
            identity = parser.get("gertrude", "identity")
        except:
            identity = ""
        try:
            proxy_info = { 'host' : parser.get("gertrude", "proxy-host"),
                           'port' : int(parser.get("gertrude", "proxy-port")),
                           'user' : parser.get("gertrude", "proxy-user"),
                           'pass' : parser.get("gertrude", "proxy-pass")
                         }
        except:
            proxy_info = None
        config.connection = HttpConnection(url, identity, auth_info, proxy_info)

def Load(progress_handler=default_progress_handler):
    __builtin__.creche, __builtin__.readonly = config.connection.Load(progress_handler)
    return creche is not None

def Save(progress_handler=default_progress_handler):
    return config.connection.Save(progress_handler)

def Restore(progress_handler=default_progress_handler):
    return config.connection.Restore(progress_handler)

def Exit(progress_handler=default_progress_handler):
    SaveDocumentsDirectory(config.documents_directory)
    return config.connection.Exit(progress_handler)

if __name__ == '__main__':    
    loaded = Load()
    if loaded and not readonly:
        Save()
    Exit()