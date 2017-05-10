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

import datetime
from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from ooffice import *
from PySepaDD import PySepaDD


class ExportSepaModifications(object):
    def __init__(self, inscrits, periode):
        self.template = None
        self.inscrits = inscrits
        self.periode = periode
        self.default_output = u"Export sepa %s %d.xml" % (months[periode.month - 1], periode.year)
        self.email_to = None
        self.multi = False
        self.email = False
        self.errors = {}

    def execute(self, _):
        errors = {}
        factures = []
        for inscrit in self.inscrits:
            try:
                factures.append(Facture(inscrit, self.periode.year, self.periode.month, NO_NUMERO))
                # TODO test cloture
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue
        return self.export_sepa(factures), errors

    @staticmethod
    def export_sepa(factures):
        config = {"name": creche.nom,
                  "IBAN": creche.iban,
                  "BIC": creche.bic,
                  "batch": True,
                  "creditor_id": "000000",
                  "currency": "EUR"
                  }
        sepa = PySepaDD(config)

        for facture in factures:
            famille = facture.inscrit.famille
            if creche.temps_facturation == FACTURATION_FIN_MOIS:
                date = facture.date + datetime.timedelta(1)
            else:
                date = facture.date
            date = date.replace(day=famille.jour_prelevement_automatique)
            rcur = (
            date.month != famille.date_premier_prelevement_automatique.month and date.year != famille.date_premier_prelevement_automatique.year)
            payment = {"name": facture.inscrit.nom,
                       "IBAN": famille.iban,
                       "BIC": famille.bic,
                       "amount": int(facture.total * 100),
                       "type": "RCUR" if rcur else "FRST",
                       "collection_date": date if rcur else famille.date_premier_prelevement_automatique,
                       "mandate_id": facture.numero,
                       "mandate_date": facture.date,
                       "description": "Facture %s %d" % (months[facture.mois - 1], facture.annee)
                       }
            sepa.add_payment(payment)

        contents = sepa.export()
        return contents
