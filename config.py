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
import sys, os.path, shutil, time
import urllib2
import ConfigParser
from functions import *
from data import FileConnection, SharedFileConnection, HttpConnection

CONFIG_FILENAME = "gertrude.ini"
DEFAULT_SECTION = "gertrude"
if sys.platform == "win32":
  DEFAULT_DATABASE = "gertrude.db"
  CONFIG_PATHS = [""]
else:
  DEFAULT_DATABASE = GERTRUDE_DIRECTORY + "/gertrude.db"
  CONFIG_PATHS = ["./", GERTRUDE_DIRECTORY + "/", "/etc/gertrude/"]
DEMO_DATABASE = "demo.db"


class Database(object):
    def __init__(self, section=None, filename=DEFAULT_DATABASE):
        self.section = section
        self.filename = filename
        self.connection = FileConnection(filename)
        self.tipi = ""


class Section(object):
    def __init__(self, database):
        self.database = database
        self.numfact = None
        self.codeclient = None


class Config(object):
    def __init__(self):
        self.filename = CONFIG_FILENAME
        self.sections = {}
        self.options = 0
        self.connection = None
        self.numfact = None
        self.codeclient = None
        self.templates = "templates"
        self.first_date = datetime.date(today.year - 2, 1, 1)
        self.last_date = datetime.date(today.year + 1, 12, 31)
        self.inscriptions_semaines_conges = None
        
    def setSection(self, section):
        self.default_section = section
        self.database = self.sections[section].database
        self.connection = self.database.connection
        self.numfact = self.sections[section].numfact
        self.codeclient = self.sections[section].codeclient

__builtin__.config = Config()


def getOptions(parser):
    options = 0
    try:
        str = parser.get(DEFAULT_SECTION, "options")
        if "lecture-seule" in str:
            options |= READONLY
        if "reservataires" in str:
            options |= RESERVATAIRES
        if "frais-inscription-reservataires" in str:
            options |= FRAIS_INSCRIPTION_RESERVATAIRES
        if "categories" in str:
            options |= CATEGORIES
        if "heures-contrat" in str:
            options |= HEURES_CONTRAT
        if "tablette" in str:
            options |= TABLETTE
        if "decloture" in str:
            options |= DECLOTURE
        if "factures-familles" in str:
            options |= FACTURES_FAMILLES
        if "groupes-sites" in str:
            options |= GROUPES_SITES
        if "no-backups" in str:
            options |= NO_BACKUPS
        if "compatibility-conges-2016" in str:
            options |= COMPATIBILITY_MODE_CONGES_2016
        if "compatibility-adaptations-2016" in str:
            options |= COMPATIBILITY_MODE_ADAPTATIONS_2016
        if "compatibility-decompte-semaines-2017" in str:
            options |= COMPATIBILITY_MODE_DECOMPTE_SEMAINES_2017
        if "prelevements-automatiques" in str:
            options |= PRELEVEMENTS_AUTOMATIQUES
        if "newsletters" in str:
            options |= NEWSLETTERS
        if "reglements" in str:
            options |= REGLEMENTS
    except:
        pass
    return options


def getWindowSize(parser):
    try:
        window_width = int(parser.get(DEFAULT_SECTION, "window-width"))
        window_height = int(parser.get(DEFAULT_SECTION, "window-height"))
        return window_width, window_height
    except:
        return 1000, 600


def getYearsDisplayed(parser):
    try:
        years_before = int(parser.get(DEFAULT_SECTION, "years-before"))
        years_after = int(parser.get(DEFAULT_SECTION, "years-after"))
        return years_before, years_after
    except:
        return 2, 1


def getPictos(parser):
    try:
        pictos_enfants = int(parser.get(DEFAULT_SECTION, "pictos-enfants"))
        pictos_salaries = int(parser.get(DEFAULT_SECTION, "pictos-salaries"))
        return pictos_enfants, pictos_salaries
    except:
        return None, None


def getStringParameter(parser, label, default=""):
    try:
        return parser.get(DEFAULT_SECTION, label)
    except:
        return default


def getIntegerParameter(parser, label, default=0):
    try:
        return int(parser.get(DEFAULT_SECTION, label))
    except:
        return default


def getTimeParameter(parser, label, default=None):
    value = getStringParameter(parser, label, default)
    if value:
        splitted = value.split(":")
        value = 3600 * int(splitted[0])
        if len(splitted) == 2:
            value += 60 * int(splitted[1])
    return value


def getDefaultDocumentsDirectory():
    if sys.platform == 'win32':
        try:
            from win32com.shell import shell
            df = shell.SHGetDesktopFolder()
            pidl = df.ParseDisplayName(0, None, "::{450d8fba-ad25-11d0-98a8-0800361b1103}")[1]
            return shell.SHGetPathFromIDList(pidl)
        except:
            print "L'extension win32com pour python est recommandée (plateforme windows) !"
            return os.getcwd()
    else:
        return os.getcwd()


def getDocumentsDirectory(parser):
    try:
        directory = parser.get(DEFAULT_SECTION, "documents-directory")
        assert os.path.isdir(directory)
        return directory
    except:
        return getDefaultDocumentsDirectory()


def getTemplatesDirectory(parser):
    try:
        directory = parser.get(DEFAULT_SECTION, "templates")
        assert os.path.isdir(directory)
        return directory
    except:
        return "templates"


def getBackupsDirectory(parser):
    try:
        directory = parser.get(DEFAULT_SECTION, "backups-directory")
        assert os.path.isdir(directory)
        return directory
    except:
        return ""


def getField(parser, section, field):
    try:
        return parser.get(section, field)
    except:
        try:
            return parser.get(DEFAULT_SECTION, field)
        except:
            return None


def getDatabase(parser, section):
    try:
        filename = parser.get(section, "database")
    except:
        if section == DEFAULT_SECTION:
            return None
        else:
            filename = DEFAULT_DATABASE

    database = Database(section, filename)

    try:
        url = parser.get(section, "url")
    except:
        return database

    if url.startswith("http://") or url.startswith("https://"):
        try:
            auth_info = (parser.get(section, "login"), parser.get(section, "password"))
        except:
            auth_info = None
        try:
            identity = parser.get(section, "identity")
        except:
            identity = ""
        try:
            proxy_info = {'host': parser.get(DEFAULT_SECTION, "proxy-host"),
                          'port': int(parser.get(DEFAULT_SECTION, "proxy-port")),
                          }
            try:
                proxy_user_info = {'user': parser.get(DEFAULT_SECTION, "proxy-user"),
                                   'pass': parser.get(DEFAULT_SECTION, "proxy-pass")
                                   }
                proxy_info.extend(proxy_user_info)
            except:
                pass
        except:
            proxy_info = None
        database.connection = HttpConnection(url, filename, identity, auth_info, proxy_info)
        try:
            database.tipi = parser.get(section, "tipi")
        except:
            pass
    elif url.startswith("file://"):
        try:
            identity = parser.get(section, "identity")
        except:
            identity = datetime.time()
        database.connection = SharedFileConnection(url[7:], filename, identity)
        
    return database


def GetConfigFile():
    for folder in CONFIG_PATHS:
        path = folder + CONFIG_FILENAME
        if os.path.isfile(path):
            return path
    return None


def LoadConfig(path=None, progress_handler=default_progress_handler):
    if path is None:
        path = GetConfigFile()

    progress_handler.display("Chargement de la configuration %s ..." % (path if path else "par défaut"))
    parser = ConfigParser.SafeConfigParser()

    if path:
        try:
            parser.read(path)
            config.filename = path
        except:
            progress_handler.display("Fichier %s erroné. Utilisation de la configuration par défaut." % path)

    config.original_window_size = getWindowSize(parser)
    config.window_size = config.original_window_size
    config.column_width = getIntegerParameter(parser, "column-width", 4)

    config.debug = getIntegerParameter(parser, "debug")
    config.saas_port = getIntegerParameter(parser, "port", None)
    config.heure_synchro_tablette = getTimeParameter(parser, "heure-synchro-tablette", None)
    config.preinscription_redirect = getStringParameter(parser, "preinscription-redirect", "")
    config.preinscription_template = getStringParameter(parser, "preinscription-form", "")

    years_before, years_after = getYearsDisplayed(parser)
    config.first_date = datetime.date(today.year - years_before, 1, 1)
    config.last_date = datetime.date(today.year + years_after, 12, 31)

    config.inscriptions_semaines_conges = getIntegerParameter(parser, "inscriptions.semaines_conges", None)

    config.pictos = getPictos(parser)
    config.hide = getStringParameter(parser, "hide")

    config.options = getOptions(parser)
    config.templates = getTemplatesDirectory(parser)
    
    config.original_documents_directory = getDocumentsDirectory(parser)
    config.documents_directory = config.original_documents_directory
    
    config.original_backups_directory = getBackupsDirectory(parser)
    config.backups_directory = config.original_backups_directory
    
    config.original_default_section = getStringParameter(parser, "default-database", None)
    config.default_section = config.original_default_section

    config.original_import_database = getStringParameter(parser, "import-database", None)
    config.import_database = config.original_import_database

    if parser:
        for section in parser.sections():
            database = getDatabase(parser, section)
            if database:
                config.sections[section] = Section(database)
                config.sections[section].numfact = getField(parser, section, "numfact")
                config.sections[section].codeclient = getField(parser, section, "codeclient")
                
    if not config.sections:
        config.sections[None] = Section(Database())
    if len(config.sections) == 1:
        config.setSection(config.sections.keys()[0])


def SaveConfig(progress_handler):
    parameters = {}
    if config.window_size != config.original_window_size:
        parameters["window-width"] = str(config.window_size[0])
        parameters["window-height"] = str(config.window_size[1])
    if config.documents_directory != config.original_documents_directory:
        parameters["documents-directory"] = config.documents_directory
    if config.backups_directory != config.original_backups_directory:
        parameters["backups-directory"] = config.backups_directory
    if config.default_section != config.original_default_section:
        parameters["default-database"] = config.default_section
    if parameters:
        try:
            parser = ConfigParser.SafeConfigParser()
            parser.read(config.filename)
            if not parser.has_section(DEFAULT_SECTION):
                parser.add_section(DEFAULT_SECTION)
            for key in parameters.keys():
                parser.set(DEFAULT_SECTION, key, parameters[key])
            parser.write(file(config.filename, "w"))
        except Exception, e:
            print e
            progress_handler.display("Impossible d'enregistrer les paramètres de configuration !")


def Filter():
    # filtrage des inscrits trop anciens (< config.first_date)
    inscrits = []
    for inscrit in creche.inscrits:
        if len(inscrit.inscriptions) > 0:
            inscrits_famille = GetInscritsFamille(inscrit.famille)
            for enfant in inscrits_famille:
                stop = False
                for inscription in enfant.inscriptions:
                    if not inscription.debut or not inscription.fin or inscription.fin >= config.first_date:
                        inscrits.append(inscrit)
                        stop = True
                        break
                if stop:
                    break
        else:
            inscrits.append(inscrit)
    print "%d inscrits filtrés" % (len(creche.inscrits) - len(inscrits))
    creche.inscrits = inscrits


def Load(progress_handler=default_progress_handler, autosave=False):
    __builtin__.creche, _readonly = config.connection.Load(progress_handler, autosave)
    Filter()
    if _readonly:
        __builtin__.readonly = True
    return creche is not None


def Save(progress_handler=default_progress_handler):
    return config.connection.Save(progress_handler)


def Restore(progress_handler=default_progress_handler):
    return config.connection.Restore(progress_handler)


def Update():
    return config.connection.Update()


def Exit(progress_handler=default_progress_handler):
    SaveConfig(progress_handler)
    return config.connection.Exit(progress_handler)


def Liste(progress_handler=default_progress_handler):
    result = {}
    try:
        c = creche
    except:
        c = None
    for value in config.sections.values():
        if value.section == config.default_section and c:
            for inscrit in c.inscrits:
                result[GetPrenomNom(inscrit)] = value
        else:
            for entry in database.connection.Liste(progress_handler):
                result[entry] = value
    return result


def RemoveIncompatibleSAASOptions():
    creche.tri_planning &= ~TRI_GROUPE

