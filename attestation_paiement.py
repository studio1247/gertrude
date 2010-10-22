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
from sqlobjects import Parent
from cotisation import Cotisation, CotisationException
from ooffice import *

class AttestationModifications(object):
    def __init__(self, who, debut, fin):
        self.template = 'Attestation paiement.odt'
        if isinstance(who, list):
            self.default_output = u"Attestations de paiement %s-%s %d.odt" % (months[debut.month - 1], months[fin.month - 1], debut.year)
            self.inscrits = [inscrit for inscrit in creche.inscrits if inscrit.getInscriptions(debut, fin)]
        else:
            self.default_output = u"Attestation de paiement %s %s %s-%s %d.odt" % (who.prenom, who.nom, months[debut.month - 1], months[fin.month - 1], debut.year)
            self.inscrits = [who]
        self.debut, self.fin = debut, fin

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        tresorier = ""
        directeur = ""
        bureau = Select(creche.bureaux, today)
        if bureau:
            if bureau.tresorier:
                tresorier = GetPrenomNom(bureau.tresorier)
            if bureau.directeur:
                directeur = GetPrenomNom(bureau.directeur)
        
        # print dom.toprettyxml()
        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.getElementsByTagName('text:section')
        for template in templates:
            doc.removeChild(template)
        
        for inscrit in self.inscrits:
            facture_debut = facture_fin = None
            date = self.debut
            total = 0.0
            try:
                while date <= self.fin:
                    facture = Facture(inscrit, date.year, date.month)
                    if facture.total != 0:
                        if facture_debut is None:
                            facture_debut = date
                        facture_fin = getMonthEnd(date)
                        total += facture.total
                    date = getNextMonthStart(date)
            except CotisationException, e:
                errors[GetPrenomNom(inscrit)] = e.errors
                continue
            
            # Les champs du recu
            fields = [('nom-creche', creche.nom),
                    ('adresse-creche', creche.adresse),
                    ('code-postal-creche', str(creche.code_postal)),
                    ('ville-creche', creche.ville),
                    ('telephone-creche', creche.telephone),
                    ('email-creche', creche.email),
                    ('de-debut', '%s %d' % (getDeMoisStr(facture_debut.month - 1), facture_debut.year)),
                    ('de-fin', '%s %d' % (getDeMoisStr(facture_fin.month - 1), facture_fin.year)),
                    ('prenom', inscrit.prenom),
                    ('parents', getParentsStr(inscrit)),
                    ('naissance', inscrit.naissance),
                    ('nom', inscrit.nom),
                    ('tresorier', tresorier),
                    ('directeur', directeur),
                    ('date', '%.2d/%.2d/%d' % (today.day, today.month, today.year)),
                    ('total', '%.2f' % total)
                    ]
    
            if inscrit.sexe == 1:
                fields.append(('ne-e', u"né"))
            else:
                fields.append(('ne-e', u"née"))
            
            for template in templates:
                section = template.cloneNode(1)
                doc.appendChild(section)
                ReplaceTextFields(section, fields)
                
        return errors

