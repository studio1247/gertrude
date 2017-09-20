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
from cotisation import CotisationException
from ooffice import *


class ExportComptaCotisationsModifications(object):
    title = "Export compta"
    template = "Export compta cotisations.txt"

    def __init__(self, inscrits, periode):
        self.inscrits = inscrits
        self.periode = periode
        self.default_output = u"Export compta cotisations %s %d.txt" % (months[periode.month - 1], periode.year)
        self.email_to = None
        self.multi = False
        self.email = False
        self.errors = {}

    @staticmethod
    def generate_ciel_line_mvt(inscrit, date, total):
        template = u'"77"\t"VT"\t"%(date)s"\t"%(client)s"\t"%(nom)s"\t"%(total)s"\tD\tB\t"COTISATION %(nom)s"\t"10"\t"%(date)s"\n' + \
                   u'"77"\t"VT"\t"%(date)s"\t"706410"\t"PARTICIPATION FAMILIALE"\t"%(total)s"\tC\tB\t"COTISATION %(nom)s""10"'
        result = template % {"date": date2str(date),
                             "client": inscrit.famille.code_client,
                             "nom": inscrit.nom.upper(),
                             "total": "%.02f" % total
                             }
        return unicode(result).encode("latin-1")

    @staticmethod
    def generate_ciel_line_tiers(inscrit):
        template = u'"%(client)s"\t"%(nom)s"\t"SR"\t"FRA"'
        result = template % {"client": inscrit.famille.code_client,
                             "nom": inscrit.nom.upper(),
                             }
        return unicode(result).encode("latin-1")

    def execute(self, text):
        if "<lines-ciel-mvt>" in text or "<lines-ciel-tiers>" in text:
            return self.execute_ciel(text)
        else:
            return self.execute_ebp(text)

    def generate_ciel_sections(self):
        mvt, tiers = [], []
        for inscrit in self.inscrits:
            try:
                facture = Facture(inscrit, self.periode.year, self.periode.month, NO_NUMERO)
            except CotisationException, e:
                self.errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue
            date = GetMonthStart(self.periode)
            mvt.append(self.generate_ciel_line_mvt(inscrit, date, facture.total))
            tiers.append(self.generate_ciel_line_tiers(inscrit))
        return "\n".join(mvt), "\n".join(tiers)

    def execute_ciel(self, text):
        mvt_section, tiers_section = self.generate_ciel_sections()
        text = text.replace("<lines-ciel-mvt>", mvt_section)
        text = text.replace("<lines-ciel-tiers>", tiers_section)
        return text, self.errors

    def execute_ebp(self, text):
        errors = {}
        result = []
        replacements = {}
        lines = text.splitlines(3)
        for i, line in enumerate(lines):
            if i == 0:
                result.append(line)
            elif i == 1:
                template = line
            else:
                if "=" in line:
                    try:
                        key, value = line.split("=", 1)
                        replacements[key.strip()] = value.strip()
                    except:
                        pass

        # print replacements

        indexOperation = 0
        for inscrit in self.inscrits:
            try:
                facture = Facture(inscrit, self.periode.year, self.periode.month, NO_NUMERO)
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue

            indexOperation += 1
            date = GetMonthEnd(self.periode)
            if len(creche.sites) > 1 and facture.site:
                site = facture.site.nom
            else:
                site = creche.nom

            fields = {'date-fin-mois': '%.2d/%.2d/%d' % (date.day, date.month, date.year),
                      'index-operation': "%04d" % indexOperation,
                      'nom': inscrit.nom.upper(),
                      'mois': months[date.month - 1].lower(),
                      }

            for i in range(5):
                if i == 0 and facture.total:
                    fields['numero-compte'] = "411%s" % inscrit.nom.upper()[:5]
                    fields['debit'] = facture.total
                    fields['credit'] = 0
                    fields['activite'] = ""
                    fields['plan-analytique'] = ""
                    fields['poste-analytique'] = ""
                elif i == 1 and facture.total - facture.supplement_activites:
                    fields['numero-compte'] = 70600000
                    fields['debit'] = 0
                    fields['credit'] = facture.total - facture.supplement_activites
                    fields['activite'] = 'garde'
                    fields['plan-analytique'] = "SITES"
                    fields['poste-analytique'] = site
                elif i == 2 and facture.supplement_activites:
                    fields['numero-compte'] = 70710000
                    fields['debit'] = 0
                    fields['credit'] = facture.supplement_activites
                    fields['activite'] = 'activites'
                    fields['plan-analytique'] = "SITES"
                    fields['poste-analytique'] = site
                elif i == 3 and facture.frais_inscription_reservataire:
                    fields['numero-compte'] = "411RESERVATAIRE"
                    fields['debit'] = facture.frais_inscription_reservataire
                    fields['credit'] = 0
                    fields['activite'] = ""
                    fields['plan-analytique'] = ""
                    fields['poste-analytique'] = ""
                elif i == 4 and facture.frais_inscription_reservataire:
                    fields['numero-compte'] = 70820000
                    fields['debit'] = 0
                    fields['credit'] = facture.frais_inscription_reservataire
                    fields['activite'] = "frais_inscription"
                    fields['plan-analytique'] = "SITES"
                    fields['poste-analytique'] = site
                else:
                    break

                line = template
                for field in fields:
                    value = unicode(fields[field]).encode("latin-1")
                    if value in replacements.keys():
                        value = replacements[value]
                    line = line.replace("<%s>" % field, value)
                result.append(line)

        return ''.join(result), errors


class ExportComptaReglementsModifications(object):
    def __init__(self, inscrits, periode):
        self.template = 'Export compta reglements.txt'
        self.inscrits = inscrits
        self.periode = periode
        self.default_output = u"Export compta reglements %s %d.txt" % (months[periode.month - 1], periode.year)
        self.email_to = None
        self.multi = False
        self.email = False
        self.errors = {}

    @staticmethod
    def generate_ciel_line_mvt_inscrit(inscrit, date, total):
        template = u'"78"\t"BQ"\t"%(date)s"\t"%(client)s"\t"%(nom)s"\t"%(total)s"\tC\tB\t"COTISATION %(mois)s"\t"10"\t"%(date)s"'
        result = template % {"date": date,
                             "mois": months[date.month - 1].upper(),
                             "total": "%.02f" % total,
                             "client": inscrit.famille.code_client,
                             "nom": inscrit.nom.upper(),
                             }
        return unicode(result).encode("latin-1")

    @staticmethod
    def generate_ciel_line_mvt_banque(date, total):
        template = u'"78"\t"BQ"\t"%(date)s"\t"512000"\t"Banque"\t"%(total)s"\tD\tB\t"RECETTES COTISATION %(mois)s"\t"10"'
        result = template % {"date": date,
                             "total": "%.02f" % total,
                             "mois": months[date.month-1].upper(),
                             }
        return unicode(result).encode("latin-1")

    @staticmethod
    def generate_ciel_line_tiers(inscrit):
        template = u'"%(client)s"\t"%(nom)s"\t"SR"\t"FRA"'
        result = template % {"client": inscrit.famille.code_client,
                             "nom": inscrit.nom.upper(),
                             }
        return unicode(result).encode("latin-1")

    def generate_ciel_sections(self):
        mvt, tiers = [], []
        total = 0.0
        for inscrit in self.inscrits:
            encaissements = [encaissement for encaissement in inscrit.famille.encaissements if encaissement.date.month == self.periode.month]
            for encaissement in encaissements:
                mvt.append(self.generate_ciel_line_mvt_inscrit(inscrit, encaissement.date, encaissement.valeur))
                total += encaissement.valeur
            if encaissements:
                tiers.append(self.generate_ciel_line_tiers(inscrit))
        mvt.append(self.generate_ciel_line_mvt_banque(GetMonthEnd(self.periode), total))
        return "\n".join(mvt), "\n".join(tiers)

    def execute(self, text):
        return self.execute_ciel(text)

    def execute_ciel(self, text):
        mvt_section, tiers_section = self.generate_ciel_sections()
        text = text.replace("<lines-ciel-mvt>", mvt_section)
        text = text.replace("<lines-ciel-tiers>", tiers_section)
        return text, self.errors
