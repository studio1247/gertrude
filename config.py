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
import urllib2
import ConfigParser
from functions import *
from data import FileConnection, HttpConnection

CONFIG_FILENAME = "./gertrude.ini"

class Config(object):
    def __init__(self):
        self.connection = FileConnection()

__builtin__.config = Config()

def LoadConfig(progress_handler=default_progress_handler):
    progress_handler.display(u"Chargement de la configuration ...")
    if not os.path.isfile(CONFIG_FILENAME):
        progress_handler.display(u"Pas de fichier gertrude.ini. Utilisation de la configuration par défaut.")
        return

    try:
        parser = ConfigParser.ConfigParser()
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
            proxy_info = { 'host' : parser.get("gertrude", "proxy-host"),
                           'port' : int(parser.get("gertrude", "proxy-port")),
                           'user' : parser.get("gertrude", "proxy-user"),
                           'pass' : parser.get("gertrude", "proxy-pass")
                         }
        except:
            proxy_info = None
        config.connection = HttpConnection(url, auth_info, proxy_info)
