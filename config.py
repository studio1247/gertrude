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
from __future__ import print_function

import sys
import codecs
import os.path
import datetime
if sys.platform == "win32" or sys.version_info > (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser
from constants import *
from progress import *
import numeros_facture
from helpers import str2date


CONFIG_FILENAME = "gertrude.ini"
DEFAULT_SECTION = "gertrude"
if sys.platform == "win32":
    DEFAULT_DATABASE = "gertrude.db"
    BACKUPS_DIRECTORY = "./backups"
    CONFIG_PATHS = [""]
else:
    HOME = os.path.expanduser("~")
    GERTRUDE_DIRECTORY = HOME + "/.gertrude"
    DEFAULT_DATABASE = GERTRUDE_DIRECTORY + "/gertrude.db"
    BACKUPS_DIRECTORY = GERTRUDE_DIRECTORY + '/backups'
    CONFIG_PATHS = ["./", GERTRUDE_DIRECTORY + "/", "/etc/gertrude/"]
DEMO_DATABASE = "demo.db"


def getDefaultDocumentsDirectory():
    if sys.platform == 'win32':
        try:
            from win32com.shell import shell
            df = shell.SHGetDesktopFolder()
            pidl = df.ParseDisplayName(0, None, "::{450d8fba-ad25-11d0-98a8-0800361b1103}")[1]
            return shell.SHGetPathFromIDList(pidl)
        except:
            print("L'extension win32com pour python est recommandée (plateforme windows)")
            return os.getcwd()
    else:
        return os.getcwd()


class Section(object):
    def __init__(self, parser, name=None):
        self.parser = parser
        self.name = name
        self.connection_type = CONNECTION_TYPE_FILE
        self.auth = None
        self.proxy = None
        self.database = self.getStringParameter("database", None)
        self.options = self.getOptionsParameter()
        self.identity = self.getStringParameter("identity")
        self.tipi = self.getStringParameter("tipi")

        if parser.has_option(self.name, "url"):
            self.url = parser.get(self.name, "url")
            if self.url.startswith("http://") or self.url.startswith("https://"):
                self.connection_type = CONNECTION_TYPE_HTTP
                if parser.has_option(self.name, "login") and parser.has_option(self.name, "password"):
                    self.auth = (parser.get(self.name, "login"), parser.get(self.name, "password"))
                if parser.has_option(self.name, "proxy-host") and parser.has_option(self.name, "proxy-port"):
                    self.proxy = {'host': self.getStringParameter("proxy-host"),
                                  'port': self.getIntegerParameter("proxy-port"),
                                  }
                    if parser.has_option(self.name, "proxy-user") and parser.has_option(self.name, "proxy-pass"):
                        self.proxy.update({'user': self.getStringParameter("proxy-user"),
                                           'pass': self.getStringParameter("proxy-pass"),
                                           })
            elif self.url.startswith("file://"):
                self.connection_type = CONNECTION_TYPE_SHARED_FILE
                self.url = self.url[7:]

        self.numfact = self.getStringParameter("numfact", None)
        if self.numfact and "numero-global" in self.numfact:
            self.numerotation_factures = numeros_facture.NumerotationMerEtTerre()
        else:
            self.numerotation_factures = None

        self.codeclient = self.getStringParameter("codeclient", None)

        self.original_window_size = self.getWindowSize()
        self.window_size = self.original_window_size
        self.column_width = self.getIntegerParameter("column-width", 4)

        self.debug = self.getIntegerParameter("debug")
        self.saas_port = self.getIntegerParameter("port", None)
        self.heure_synchro_tablette = self.getTimeParameter("heure-synchro-tablette", None)
        self.preinscription_redirect = self.getStringParameter("preinscription-redirect", "")
        self.preinscription_template = self.getStringParameter("preinscription-template", "")
        self.preinscription_required = self.getStringParameter("preinscription-required", "")
        self.child_selection_widget = self.getStringParameter("child-selection-widget", "autocomplete")

        self.years_before = self.getIntegerParameter("years-before", 2)
        self.years_after = self.getIntegerParameter("years-after", 1)
        today = datetime.date.today()
        self.first_date = datetime.date(today.year - self.years_before, 1, 1)
        self.last_date = datetime.date(today.year + self.years_after, 12, 31)

        self.date_debut_reglements = self.getDateParameter("date-debut-reglements", None)
        self.inscriptions_semaines_conges = self.getIntegerParameter("inscriptions.semaines_conges", None)

        self.pictos = self.getPictos()
        self.hide = self.getStringParameter("hide")

        self.templates_directory = self.getTemplatesDirectory()
        self.original_documents_directory = self.getDocumentsDirectory()
        self.documents_directory = self.original_documents_directory

        self.original_backups_directory = self.getBackupsDirectory()
        self.backups_directory = self.original_backups_directory

        self.original_import_database = self.getStringParameter("import-database", None)
        self.import_database = self.original_import_database

    def getStringParameter(self, key, default=""):
        if self.parser.has_option(self.name, key):
            return self.parser.get(self.name, key)
        elif self.parser.has_option(DEFAULT_SECTION, key):
            return self.parser.get(DEFAULT_SECTION, key)
        else:
            return default

    def getIntegerParameter(self, key, default=0):
        value = self.getStringParameter(key, None)
        if value is not None:
            try:
                return int(value)
            except Exception as e:
                print("Erreur de config pour le paramètre %s" % key, e)
        return default

    def getDateParameter(self, key, default=None):
        value = self.getStringParameter(key, default)
        if value:
            value = str2date(value)
        return value

    def getTimeParameter(self, key, default=None):
        value = self.getStringParameter(key, default)
        if value:
            splitted = value.split(":")
            value = 3600 * int(splitted[0])
            if len(splitted) == 2:
                value += 60 * int(splitted[1])
        return value

    def getOptionsParameter(self):
        options = 0
        value = self.getStringParameter("options")
        if "lecture-seule" in value:
            options |= READONLY
        if "reservataires" in value:
            options |= RESERVATAIRES
        if "frais-inscription-reservataires" in value:
            options |= FRAIS_INSCRIPTION_RESERVATAIRES
        if "categories" in value:
            options |= CATEGORIES
        if "heures-contrat" in value:
            options |= HEURES_CONTRAT
        if "tablette" in value:
            options |= TABLETTE
        if "decloture" in value:
            options |= DECLOTURE
        if "factures-familles" in value:
            options |= FACTURES_FAMILLES
        if "groupes-sites" in value:
            options |= GROUPES_SITES
        if "no-backups" in value:
            options |= NO_BACKUPS
        if "compatibility-conges-2016" in value:
            options |= COMPATIBILITY_MODE_CONGES_2016
        if "compatibility-adaptations-2016" in value:
            options |= COMPATIBILITY_MODE_ADAPTATIONS_2016
        if "compatibility-decompte-semaines-2017" in value:
            options |= COMPATIBILITY_MODE_DECOMPTE_SEMAINES_2017
        if "prelevements-automatiques" in value:
            options |= PRELEVEMENTS_AUTOMATIQUES
        if "newsletters" in value:
            options |= NEWSLETTERS
        if "reglements" in value:
            options |= REGLEMENTS
        if "tarifs-speciaux-labels" in value:
            options |= TARIFS_SPECIAUX_LABELS
        elif "tarifs-speciaux" in value:
            options |= TARIFS_SPECIAUX
        if "no-password" in value:
            options |= NO_PASSWORD
        if "alertes-non-paiement" in value:
            options |= ALERTES_NON_PAIEMENT
        if "gestion-repas" in value:
            options |= GESTION_REPAS
        if "preinscriptions-only" in value:
            options |= PREINSCRIPTIONS_ONLY
        return options

    def getWindowSize(self):
        return self.getIntegerParameter("window-width", 1000), self.getIntegerParameter("window-height", 600)

    def getPictos(self):
        return self.getIntegerParameter("pictos-enfants", None), self.getIntegerParameter("pictos-salaries", None)

    def getDocumentsDirectory(self):
        directory = self.getStringParameter("documents-directory")
        return directory if os.path.isdir(directory) else getDefaultDocumentsDirectory()

    def getTemplatesDirectory(self):
        directory = self.getStringParameter("templates-directory")
        return directory if os.path.isdir(directory) else "templates"

    def getBackupsDirectory(self):
        directory = self.getStringParameter("backups-directory")
        return directory if os.path.isdir(directory) else "backups"


class DefaultConfig(object):
    def __init__(self):
        self.first_date = datetime.date.today() - datetime.timedelta(365)
        self.last_date = datetime.date.today() + datetime.timedelta(365)
        self.templates_directory = "templates"
        self.options = 0
        self.saas_port = None
        self.numfact = None
        self.codeclient = None
        self.tipi = ""


class Config(object):
    def __init__(self):
        self.filename = CONFIG_FILENAME
        self.path = None
        self.sections = {}
        self.default_section = None
        self.current_section = None
        self.readonly = False
        self.default_config = DefaultConfig()

    @staticmethod
    def find_config_file():
        for folder in CONFIG_PATHS:
            path = folder + CONFIG_FILENAME
            if os.path.isfile(path):
                return path
        return None

    def load(self, path=None, progress_handler=default_progress_handler):
        if path is None:
            path = self.find_config_file()

        progress_handler.display("Chargement de la configuration %s ..." % (path if path else "par défaut"))
        parser = ConfigParser()

        if path:
            try:
                if sys.platform == "win32" or sys.version_info > (3, 0):
                    parser.read(path, encoding="utf-8")
                else:
                    parser.read(path)
                self.path = path
            except:
                progress_handler.display("Fichier %s erroné. Utilisation de la configuration par défaut." % path)

        if parser:
            for name in parser.sections():
                section = Section(parser, name)
                if section.database:
                    self.sections[name] = Section(parser, name)

        self.sections_names = list(self.sections.keys())
        self.sections_names.sort(key=lambda name: name.upper())

        if not self.sections:
            self.sections[None] = Section(parser, "")
            self.sections_names.append(None)

        section_name = Section(parser).getStringParameter("default-section", None)
        self.default_section = self.sections.get(section_name, None)

        if len(self.sections) == 1:
            self.set_current_section(self.sections_names[0])
            if not self.current_section.database:
                self.current_section.database = DEFAULT_DATABASE

    def save(self, progress_handler):
        parameters = {}
        if self.window_size != self.original_window_size:
            parameters["window-width"] = str(self.window_size[0])
            parameters["window-height"] = str(self.window_size[1])
        if self.documents_directory != self.original_documents_directory:
            parameters["documents-directory"] = self.documents_directory
        if self.backups_directory != self.original_backups_directory:
            parameters["backups-directory"] = self.backups_directory
        if self.current_section != self.default_section:
            parameters["default-section"] = self.current_section.name
        if parameters:
            try:
                if not self.parser.has_section(DEFAULT_SECTION):
                    self.parser.add_section(DEFAULT_SECTION)
                for key in parameters.keys():
                    if self.parser.has_option(self.current_section, key):
                        self.parser.set(self.current_section, key, parameters[key])
                    else:
                        self.parser.set(DEFAULT_SECTION, key, parameters[key])
                with codecs.open(self.path, "w", encoding="utf-8") as f:
                    self.parser.write(f)
            except Exception as e:
                print(e)
                progress_handler.display("Impossible d'enregistrer les paramètres de configuration !")

    def set_current_section(self, section_name):
        print("Section %s choisie" % section_name)
        self.current_section = self.sections[section_name]

    def get_first_monday(self):
        return self.first_date - datetime.timedelta(self.first_date.weekday())

    def is_date_after_reglements_start(self, date):
        if self.date_debut_reglements is None:
            return True
        elif date >= self.date_debut_reglements:
            return True
        else:
            return False

    def __getattr__(self, key):
        if self.current_section and hasattr(self.current_section, key):
            return getattr(self.current_section, key)
        else:
            return getattr(self.default_config, key)


config = Config()


print("TODO Fin config a revoir")

if 0:
    def Filter():
        # filtrage des inscrits trop anciens (< config.first_date)
        inscrits = []
        for inscrit in database.creche.inscrits:
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
        print("%d inscrits filtrés" % (len(database.creche.inscrits) - len(inscrits)))

    def Update():
        return config.connection.Update()
