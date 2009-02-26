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
from cotisation import Cotisation, CotisationException
from ooffice import *

class AttestationModifications(object):
    def __init__(self, inscrit, debut, fin):
        self.inscrit = inscrit
        self.debut, self.fin = debut, fin

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return []
        
        facture_debut = facture_fin = None
        date = self.debut
        total = 0.0
        while date <= self.fin:
            try:
                facture = Facture(self.inscrit, date.year, date.month)
                if facture.total != 0:
		    if facture_debut is None:
		        facture_debut = date
	            facture_fin = getMonthEnd(date)
                    total += facture.total
            except CotisationException, e:
                return [(self.inscrit, e.errors)]

            date = getNextMonthStart(date)
        
        tresorier = Select(creche.bureaux, today).tresorier

        # Les champs du recu
        fields = [('nom-creche', creche.nom),
                ('adresse-creche', creche.adresse),
                ('code-postal-creche', str(creche.code_postal)),
                ('ville-creche', creche.ville),
                ('telephone-creche', creche.telephone),
                ('email-creche', creche.email),
                ('de-debut', '%s %d' % (getDeMoisStr(facture_debut.month - 1), facture_debut.year)),
                ('de-fin', '%s %d' % (getDeMoisStr(facture_fin.month - 1), facture_fin.year)),
                ('prenom', self.inscrit.prenom),
                ('parents', getParentsStr(self.inscrit)),
                ('naissance', self.inscrit.naissance),
                ('nom', self.inscrit.nom),
                ('tresorier', "%s %s" % (tresorier.prenom, tresorier.nom)),
                ('date', '%.2d/%.2d/%d' % (today.day, today.month, today.year)),
                ('total', '%.2f' % total)
                ]

        if self.inscrit.sexe == 1:
            fields.append(('ne-e', u"né"))
        else:
            fields.append(('ne-e', u"née"))

        #print fields
        ReplaceTextFields(dom, fields)
        return []

def GenereAttestationPaiement(oofilename, inscrit, debut, fin):
    return GenerateDocument('Attestation paiement.odt', oofilename, AttestationModifications(inscrit, debut, fin))

