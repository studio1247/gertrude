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

from constants import *
from functions import *
from facture import *
from ooffice import *


class CommandeRepasModifications(object):
    def __init__(self, site, debut):
        self.multi = False
        self.template = 'Commande repas.odt'
        self.default_output = "Commande repas %s.odt" % str(debut)
        self.debut = debut
        self.metas = {"Format": 1, "Periodicite": 11}
        self.email = None
        self.site = site

    def repas(self, jour, categories=None):
        try:
            return self.presents(jour, categories, 12 * 12, 14 * 12, True)
        except Exception, e:
            print e
    
    def gouters(self, jour, categories=None):
        return self.presents(jour, categories, 16 * 12, 17 * 12, False)

    def presents(self, jour, categories, debut, fin, allergies):
        if categories is None:
            categories = []
        elif isinstance(categories, basestring):
            categories = [categories]
        total = 0
        normal = 0
        allergiques = {}
        date = self.debut + datetime.timedelta(jour)
        for inscrit in GetInscrits(date, date, site=self.site):
            if not categories or (inscrit.categorie and inscrit.categorie.nom in categories):
                journee = inscrit.GetJournee(date)
                if journee and IsPresentDuringTranche(journee, debut, fin):
                    total += 1
                    if allergies and inscrit.allergies:
                        if inscrit.allergies in allergiques:
                            allergiques[inscrit.allergies] += 1
                        else:
                            allergiques[inscrit.allergies] = 1
                    else:
                        normal += 1
        if total > 0 and normal == 0:
            return " ".join(["%dx%s" % (allergiques[allergie], allergie) for allergie in allergiques])
        elif allergiques:
            return "%d dont\n" % total + " ".join(["%dx%s" % (allergiques[allergie], allergie) for allergie in allergiques])
        elif total:
            return "%d" % total
        else:
            return ""
            
    def execute(self, filename, dom):
        if filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print meta.toprettyxml()
                name = meta.getAttribute('meta:name')
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = float(value)
                else:
                    self.metas[name] = value
            return None
        elif filename != 'content.xml':
            return None
              
        fields = GetCrecheFields(creche) + GetSiteFields(self.site)
        fields.append(('numero-semaine', self.debut.isocalendar()[1]))
        fields.append(('debut-semaine', date2str(self.debut)))
        fields.append(('fin-semaine', date2str(self.debut+datetime.timedelta(4))))
                
        for categorie in creche.categories:
            for day in range(7):
                fields.append(("repas", self.repas))
                fields.append(("gouters", self.gouters))
            
        ReplaceTextFields(dom, fields)
        
        return None