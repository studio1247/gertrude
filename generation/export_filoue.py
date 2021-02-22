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

from facture import *


class ExportFiloueModifications:
    title = "Export Filoue"
    template = "Export Filoue.csv"

    def __init__(self, site, year):
        self.annee = year
        self.start = datetime.date(year, 1, 1)
        self.end = datetime.date(year, 12, 31)
        self.site = site
        if site:
            self.default_output = u"Export Filoue %s %d.csv" % (site.nom, year)
        else:
            self.default_output = u"Export Filoue %d.csv" % year
        self.email_to = None
        self.multi = False
        self.email = False

    @staticmethod
    def get_regime_caf(inscrit, date):
        regime = inscrit.GetRegime(date)
        if regime == 1:
            return 1
        elif regime == 3:
            return 2
        else:
            return 3

    def execute(self, text):
        errors = {}
        lines = text.splitlines()
        result = [lines[0]]
        template = lines[1]
        for inscrit in database.creche.select_inscrits(self.start, self.end):
            regime_caf = 3
            heures_realisees = 0
            heures_facturees = 0
            total_facture = 0
            date = self.start
            error = False
            facture = None
            while date < self.end:
                try:
                    facture = Facture(inscrit, self.annee, date.month, NO_NUMERO)
                    regime_caf = self.get_regime_caf(inscrit, date)
                    heures_realisees += facture.heures_realisees
                    heures_facturees += facture.heures_facturees
                    total_facture += facture.total
                except CotisationException as e:
                    errors[GetPrenomNom(inscrit)] = e.errors
                    error = True
                if error:
                    break
                date = GetNextMonthStart(date)
            line = template
            if facture:
                fields = {
                    "top-allocataire": 1,
                    "prenom": inscrit.prenom,
                    "nom": inscrit.nom,
                    "matricule-allocataire": inscrit.famille.numero_allocataire_caf,
                    "regime-caf": regime_caf,
                    "date-naissance": inscrit.naissance.strftime("%d/%m/%Y"),
                    "code-postal-famille": inscrit.famille.code_postal,
                    "ville-famille": inscrit.famille.ville,
                    "heures-facturees": "%04.02f" % heures_facturees,
                    "heures-realisees": "%04.02f" % heures_realisees,
                    "total-facture": "%06.02f" % total_facture,
                    "tarif-horaire": "%02.02f" % ((total_facture / heures_facturees) if heures_facturees else 0),
                    "taux-effort": ("%01.02f" % facture_heures.taux_effort) if facture_heures.taux_effort else None,
                    "premier-jour": max(self.start, min([contrat.debut for contrat in inscrit.get_inscriptions() if contrat.debut and not contrat.preinscription])).strftime("%d/%m/%Y"),
                    "dernier-jour": min(self.end, max([(contrat.GetFin() if contrat.GetFin() else self.end) for contrat in inscrit.get_inscriptions() if contrat.debut and not contrat.preinscription])).strftime("%d/%m/%Y"),
                }
                for key, value in fields.items():
                    line = line.replace("<%s>" % key, str(value).replace(";", ",") if value else "")
                result.append(line)

        return "\n".join(result), errors
