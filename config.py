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

class Config(object):
    def __init__(self):
        self.connection = FileConnection()

__builtin__.config = Config()

def getDocumentsDirectory(parser, progress_handler):
    try:
	directory = parser.get("gertrude", "documents-directory")
        assert os.path.isdir(directory)
    except:
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

def getNetworkConnection(parser, progress_handler):
    if not parser:
        return None
    
    try:
        url = parser.get("gertrude", "url")
    except:
        progress_handler.display(u"Pas d'url définie. Utilisation de la configuration par défaut.")
        return None

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
        return HttpConnection(url, identity, auth_info, proxy_info)
    
def LoadConfig(progress_handler=default_progress_handler):
    progress_handler.display(u"Chargement de la configuration ...")
    
    parser = None
    if os.path.isfile(CONFIG_FILENAME):
        try:
            parser = ConfigParser.SafeConfigParser()
            parser.read(CONFIG_FILENAME)
        except:
            progress_handler.display(u"Fichier gertrude.ini erroné. Utilisation de la configuration par défaut.")
    else:
        progress_handler.display(u"Pas de fichier gertrude.ini. Utilisation de la configuration par défaut.")

    config.original_documents_directory = getDocumentsDirectory(parser, progress_handler)
    config.documents_directory = config.original_documents_directory
    network_connection = getNetworkConnection(parser, progress_handler)
    if network_connection:
        config.connection = network_connection
        
def SaveConfig(progress_handler):
    if config.documents_directory == config.original_documents_directory:
        return
    
    try:
        parser = ConfigParser.SafeConfigParser()
        parser.read(CONFIG_FILENAME)
        if not parser.has_section("gertrude"):
            parser.add_section("gertrude")
        parser.set("gertrude", "documents-directory", config.documents_directory)
        parser.write(file(CONFIG_FILENAME, "w"))
    except Exception, e:
        print e
        progress_handler.display(u"Impossible d'enregistrer le répertoire de destination des documents !")    

def Load(progress_handler=default_progress_handler):
    __builtin__.creche, __builtin__.readonly = config.connection.Load(progress_handler)
    return creche is not None

def Save(progress_handler=default_progress_handler):
    return config.connection.Save(progress_handler)

def Restore(progress_handler=default_progress_handler):
    return config.connection.Restore(progress_handler)

def Exit(progress_handler=default_progress_handler):
    SaveConfig(progress_handler)
    return config.connection.Exit(progress_handler)

if __name__ == '__main__':    
    loaded = Load()
    if loaded and not readonly:
        Save()
    Exit()
