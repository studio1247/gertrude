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

from constants import *
from functions import *
from facture import *
from ooffice import *

class EtatsPresenceModifications(object):
    def __init__(self, debut, fin, site, professeur, inscrit, selection):
        self.multi = False
        self.template = 'Etats presence.ods'
        self.default_output = "Etats presence"
        if site:
            self.default_output += " %s" % site.nom
        if professeur:
            self.default_output += " %s" % GetPrenomNom(professeur)
        if inscrit:
            self.default_output += " %s" % GetPrenomNom(inscrit)
        self.default_output += ".ods"
        self.debut, self.fin, self.site, self.professeur, self.inscrit, self.selection = debut, fin, site, professeur, inscrit, selection
        self.gauge = None
        self.email = None
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)
        lignes = table.getElementsByTagName("table:table-row")

        titres = GetValues(lignes.item(7))
        if creche.type != TYPE_GARDERIE_PERISCOLAIRE:
            for i in range(7):
                if u'Professeur : <critere-professeur>' in GetValues(lignes.item(i)):
                    table.removeChild(lignes.item(i))
                    break                
            if titres[2] == "Professeur":
                RemoveColumn(lignes, 2)
        if len(creche.sites) < 2:
            for i in range(7):
                if u'Site : <critere-site>' in GetValues(lignes.item(i)):
                    table.removeChild(lignes.item(i))
                    break
            if titres[1] == "Site":
                RemoveColumn(lignes, 1)
               
        # Les champs de l'entête
        ReplaceFields(lignes, [('debut', self.debut),
                               ('fin', self.fin),
                               ('critere-site', GetNom(self.site)),
                               ('critere-professeur', GetPrenomNom(self.professeur)),
                               ('critere-inscrit', GetPrenomNom(self.inscrit))])
        
        # Les lignes
        template = lignes.item(8)
        dates = self.selection.keys()
        dates.sort()
        for date in dates:
            for site, professeur, inscrit, heure_arrivee, heure_depart, heures in self.selection[date]:
                ligne = template.cloneNode(1)
                fields = GetInscritFields(inscrit)
                fields.extend([('date', date),
                               ('debut-contrat', inscrit.GetInscription(date).debut),
                               ('fin-contrat', inscrit.GetInscription(date).fin),
                               ('heure-arrivee', GetHeureString(heure_arrivee)),
                               ('heure-depart', GetHeureString(heure_depart)),
                               ('site', GetNom(site)),
                               ('professeur-prenom', GetPrenom(professeur)),
                               ('professeur-nom', GetNom(professeur)),
                               ('heures', GetHeureString(heures))])
                ReplaceFields(ligne, fields)
                table.insertBefore(ligne, template)

        table.removeChild(template)
        if self.gauge:
            self.gauge.SetValue(90)
        return errors
