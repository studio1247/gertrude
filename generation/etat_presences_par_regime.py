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
from functions import GetPrenomNom, GetCrecheFields, GetMonthEnd, GetHeuresAccueil, GetJoursOuvres, Select, \
    GetBureauFields
from globals import database
from helpers import GetTrimestreEnd, GetNextMonthStart, GetTrimestreStart
from cotisation import CotisationException
from generation.opendocument import OpenDocumentText


class Regime(object):
    def __init__(self):
        self.heures_facturees = 0
        self.heures_realisees = 0
        self.total_facture = 0
        self.total_realise = 0


class EtatPresencesParRegime(OpenDocumentText):
    title = "Etat de présences par régime"
    template = "Etat de presences par regime.odt"

    def __init__(self, year):
        OpenDocumentText.__init__(self)
        self.set_default_output("Etat de presences par regime %d.odt" % year)
        self.annee = year
        self.debut, self.fin = datetime.date(year, 1, 1), datetime.date(year, 12, 31)
        self.regimes = ["général et fonctionnaire", "agricole", "autres"]
        self.table = [Regime() for _ in range(len(self.regimes))]
        self.jours_accueil, self.heures_accueil = .0, .0
        self.heures_facturees, self.heures_realisees = .0, .0
        self.total_facture, self.total_realise = .0, .0
        self.inscrits = set()

    def get_regime(self, inscrit, date):
        regime = inscrit.get_regime(date)
        if regime == REGIME_CAF_GENERAL or regime == REGIME_CAF_FONCTION_PUBLIQUE:
            return 0
        elif regime == REGIME_CAF_MSA:
            return 1
        # elif regime == REGIME_CAF_PECHE_MARITIME or regime == REGIME_CAF_MARINS_DU_COMMERCE:
        #     return 2
        else:
            return 2

    def calcule_table(self):
        for mois in range(12):
            self.jours_accueil += GetJoursOuvres(self.annee, mois + 1)
            self.heures_accueil += GetHeuresAccueil(self.annee, mois + 1)
        # TODO impossible à cause du problème plus bas ... for inscrit in database.creche.select_inscrits(self.debut, self.fin):
        for inscrit in database.creche.inscrits:
            date = self.debut
            for mois in range(12):
                try:
                    date = datetime.date(self.annee, mois+1, 1)
                    fin = GetMonthEnd(date)
                    if inscrit.get_inscriptions(date, fin):
                        self.inscrits.add(inscrit)
                        # TODO il y a un problème pour les crèches en facturation debut de mois, le total_facture != total
                        facture = Facture(inscrit, self.annee, mois + 1, NO_NUMERO)
                        regime = self.get_regime(inscrit, date)
                        if config.options & HEURES_CONTRAT:
                            facture_heures_facturees = facture.heures_facture
                        else:
                            facture_heures_facturees = facture.heures_facturees
                        self.table[regime].heures_facturees += facture_heures_facturees
                        self.table[regime].heures_realisees += facture.heures_realisees
                        self.heures_facturees += facture_heures_facturees
                        self.heures_realisees += facture.heures_realisees
                        self.total_facture += facture.total_facture
                        self.total_realise += facture.total_realise
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

        fields = GetCrecheFields(database.creche) + [
            ('annee', self.annee),
            ('date-debut', self.debut),
            ('date-fin', self.fin),
            ("heures-facturees", self.heures_facturees),
            ("heures-realisees", self.heures_realisees),
            ("total-facture", self.total_facture),
            ("total-realise", self.total_realise),
            ("jours-accueil", self.jours_accueil),
            ("heures-accueil", self.heures_accueil),
            ("nombre-inscrits", len(self.inscrits))
        ]
        for i, regime in enumerate(self.regimes):
            fields.extend([
                ("heures-facturees-%d" % i, self.table[i].heures_facturees),
                ("heures-realisees-%d" % i, self.table[i].heures_realisees),
            ])

        if self.heures_accueil:
            fields.extend([
                ("taux-facture", (100.0 * self.heures_facturees) / self.heures_accueil),
                ("taux-realise", (100.0 * self.heures_realisees) / self.heures_accueil)
            ])

        bureau = Select(database.creche.bureaux, datetime.date.today())
        if bureau:
            fields.extend(GetBureauFields(bureau))

        self.replace_text_fields(doc, fields)

        # print doc.toprettyxml()

        return True
