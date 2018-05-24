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
import datetime

from constants import NO_NUMERO, HEURES_CONTRAT, ordinaux, REGIME_CAF_GENERAL, REGIME_CAF_FONCTION_PUBLIQUE, REGIME_CAF_MSA, REGIME_CAF_PECHE_MARITIME, REGIME_CAF_MARINS_DU_COMMERCE
from config import config
from facture import Facture
from functions import GetPrenomNom, GetCrecheFields
from globals import database
from helpers import GetTrimestreEnd, GetNextMonthStart, GetTrimestreStart
from cotisation import CotisationException
from generation.opendocument import OpenDocumentText


class Regime(object):
    def __init__(self):
        self.reel_facture = 0
        self.reel_realise = 0
        self.previsionnel_facture = 0
        self.previsionnel_realise = 0


class ReleveSIEJDocument(OpenDocumentText):
    title = "Relevés SIEJ"
    template = "Releve SIEJ.odt"

    def __init__(self, site, year):
        OpenDocumentText.__init__(self)
        self.set_default_output("Releve SIEJ %d.odt" % year)
        self.site = site
        self.annee = year
        self.debut, self.fin = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
        self.regimes = ["général et fonctionnaire", "agricole", "maritime", "autres"]
        self.table = [Regime() for _ in range(4)]
        self.reel, self.previsionnel, self.facture, self.realise = 0, 0, 0, 0

    def get_regime(self, inscrit, date):
        regime = inscrit.get_regime(date)
        if regime == REGIME_CAF_GENERAL or regime == REGIME_CAF_FONCTION_PUBLIQUE:
            return 0
        elif regime == REGIME_CAF_MSA:
            return 1
        elif regime == REGIME_CAF_PECHE_MARITIME or regime == REGIME_CAF_MARINS_DU_COMMERCE:
            return 2
        else:
            return 3

    def calcule_table(self):
        for inscrit in database.creche.select_inscrits(self.debut, self.fin):
            date = self.debut
            for mois in range(12):
                trimestreEnd = GetTrimestreEnd(date)
                try:
                    facture = Facture(inscrit, self.annee, mois + 1, NO_NUMERO)
                    regime = self.get_regime(inscrit, date)
                    if config.options & HEURES_CONTRAT:
                        facture_heures_facturees = facture.heures_facture
                    else:
                        facture_heures_facturees = facture.heures_facturees
                    if trimestreEnd <= datetime.date.today():
                        self.table[regime].reel_facture += facture_heures_facturees
                        self.table[regime].reel_realise += facture.heures_realisees
                        self.reel += facture_heures_facturees
                        self.facture += facture_heures_facturees
                        self.realise += facture.heures_realisees

                    else:
                        self.table[regime].previsionnel_facture += facture_heures_facturees
                        self.table[regime].previsionnel_realise += facture.heures_realisees
                        self.previsionnel += facture_heures_facturees
                except CotisationException as e:
                    self.errors[GetPrenomNom(inscrit)] = e.errors
                date = GetNextMonthStart(date)

    # def execute(self, filename, dom):
    # if filename == 'meta.xml':
    #     metas = dom.getElementsByTagName('meta:user-defined')
    #     for meta in metas:
    #         # print meta.toprettyxml()
    #         name = meta.getAttribute('meta:name')
    #         value = meta.childNodes[0].wholeText
    #         if meta.getAttribute('meta:value-type') == 'float':
    #             self.metas[name] = float(value)
    #         else:
    #             self.metas[name] = value
    #     return None

    # elif filename == 'styles.xml':
    #     ReplaceTextFields(dom, GetCrecheFields(database.creche))
    #     return []

    def modify_content(self, dom):
        OpenDocumentText.modify_content(self, dom)
        self.calcule_table()
        doc = dom.getElementsByTagName("office:text")[0]

        fields = GetCrecheFields(database.creche) + [('annee', self.annee),
                                                     ('date-debut-reel', self.debut),
                                                     ('date-fin-reel', GetTrimestreStart(datetime.date.today()) - datetime.timedelta(1)),
                                                     ('date-debut-previsionnel', GetTrimestreStart(datetime.date.today())),
                                                     ('date-fin-previsionnel', self.fin),
                                                     ]

        trimestre = (datetime.date.today().month - 1) // 3
        if trimestre > 0:
            fields.append(('trimestre', "%s trimestre" % ordinaux[trimestre - 1]))

        self.replace_text_fields(doc, fields)

        # print doc.toprettyxml()

        for section in doc.getElementsByTagName('text:section'):
            section_name = section.getAttribute('text:name')
            if section_name == 'Regime':
                section_regime = section

        for i, regime in enumerate(self.table):
            section = section_regime.cloneNode(1)
            doc.insertBefore(section, section_regime)
            fields = [('regime', 'Régime %s' % self.regimes[i]),
                      ('reel-facture', regime.reel_facture),
                      ('reel-realise', regime.reel_realise),
                      ('previsionnel-facture', regime.previsionnel_facture),
                      ('previsionnel-realise', regime.previsionnel_realise),
                      ('total-facture', regime.reel_facture + regime.previsionnel_facture),
                      ('total-realise', regime.reel_realise + regime.previsionnel_realise),
                      ('reel', self.reel),
                      ('previsionnel', self.previsionnel),
                      ('total', self.reel + self.previsionnel),
                      ]

            for table in section.getElementsByTagName("table:table"):
                table_name = table.getAttribute("table:name")
                if (i > 0 and table_name == 'Recap') or table_name == 'Facture' or table_name == 'Realise':
                    section.removeChild(table)

            self.replace_text_fields(section, fields)

        # le tableau recap
        section = section_regime.cloneNode(1)
        doc.insertBefore(section, section_regime)
        for table in section.getElementsByTagName("table:table"):
            table_name = table.getAttribute("table:name")
            if table_name == 'Regime':
                section.removeChild(table)
        fields = [('facture', self.facture),
                  ('realise', self.realise),
                  ('reel', self.reel),
                  ('previsionnel', self.previsionnel),
                  ('total', self.reel + self.previsionnel),
                  ]
        for i, regime in enumerate(self.table):
            taux = 100.0 * regime.reel_facture / self.facture
            fields.append(('taux-%d' % i, "%.2f %%" % taux))
        self.replace_text_fields(section, fields)

        doc.removeChild(section_regime)

        return True
