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

PRESENCE_NON_FACTUREE = 256
CONGES = 257

couleurs = {SUPPLEMENT: 'A2',
            MALADE: 'B2',
            HOPITAL: 'B2',
            MALADE_SANS_JUSTIFICATIF: 'B2',
            PRESENT: 'C2',
            VACANCES: 'D2',
            ABSENT: 'E2',
            PRESENCE_NON_FACTUREE: 'A3',
            ABSENCE_NON_PREVENUE: 'B3',
            CONGES_DEPASSEMENT: 'D3',
            ABSENCE_CONGE_SANS_PREAVIS: 'B3',
            CONGES: 'C3'
            }


class FactureModifications(object):
    @staticmethod
    def GetPrenomNom(who):
        if config.options & FACTURES_FAMILLES:
            return who.nom
        else:
            return GetPrenomNom(who)

    def __init__(self, inscrits, periode):
        self.title = "Facture mensuelle"
        self.metas = {}
        self.multi = False
        self.inscrits = GetEnfantsTriesSelonParametreTriFacture(inscrits)
        self.periode = periode
        self.periode_facturation = periode
        if creche.temps_facturation != FACTURATION_FIN_MOIS:
            self.periode_facturation = GetMonthStart(periode - datetime.timedelta(1))

        self.email = True
        if len(self.inscrits) > 1:
            self.site = self.inscrits[0].GetInscriptions(self.periode_facturation, None)[0].site
            self.email_subject = u"Factures %s %d" % (months[periode.month - 1], periode.year)
            self.default_output = u"Factures %s %d.odt" % (months[periode.month - 1], periode.year)
            self.email_to = None
        else:
            who = self.inscrits[0]
            self.site = who.GetInscriptions(self.periode_facturation, None)[0].site
            self.email_subject = u"Facture %s %s %d" % (self.GetPrenomNom(who), months[periode.month - 1], periode.year)
            self.email_to = list(set([parent.email for parent in who.famille.parents if parent and parent.email]))
            self.default_output = self.email_subject + ".odt"

        if self.site and IsTemplateFile("Facture mensuelle simple %s.odt" % self.site.nom):
            self.template = "Facture mensuelle simple %s.odt" % self.site.nom
            if len(self.inscrits) > 1:
                self.multi = True
                self.default_output = u"Facture <enfant> %s %d.odt" % (months[periode.month - 1], periode.year)
        elif IsTemplateFile("Facture mensuelle simple.odt"):
            self.template = "Facture mensuelle simple.odt"
            self.multi = True
            self.default_output_multi = u"Facture <enfant> %s %d.odt" % (months[periode.month - 1], periode.year)
        elif self.site and IsTemplateFile("Facture mensuelle %s.odt" % self.site.nom):
            self.template = "Facture mensuelle %s.odt" % self.site.nom
        elif IsTemplateFile("Facture mensuelle %s.odt" % creche.nom):
            self.template = "Facture mensuelle %s.odt" % creche.nom
        elif IsTemplateFile("Facture mensuelle simple.odt"):
            self.template = "Facture mensuelle simple.odt"
            if len(self.inscrits) > 1:
                self.multi = True
                self.default_output = u"Facture <enfant> %s %d.odt" % (months[periode.month - 1], periode.year)
        else:
            self.template = 'Facture mensuelle.odt'

        self.email_text = "Accompagnement facture.txt"

    def GetSimpleModifications(self, filename):
        return [(filename.replace("<enfant>", self.GetPrenomNom(inscrit)).replace("<prenom>", inscrit.prenom).replace(
            "<nom>", inscrit.nom), FactureModifications([inscrit], self.periode)) for inscrit in self.inscrits]

    def FillRecapSection(self, section, facture):
        empty_cells = facture.debut_recap.weekday()
        if "Week-end" in creche.feries and empty_cells > 4:
            empty_cells -= 7

        tables = section.getElementsByTagName('table:table')
        for table in tables:
            if table.getAttribute('table:name').startswith('Presences'):
                rows = table.getElementsByTagName('table:table-row')[1:]
                cells_count = GetCellsCount(rows[0])
                cells = []
                for i in range(len(rows)):
                    cells.append(rows[i].getElementsByTagName('table:table-cell'))
                    for cell in cells[i]:
                        cell.setAttribute('table:style-name', 'Presences.E7')
                        text_node = cell.getElementsByTagName('text:p')[0]
                        if text_node and text_node.firstChild:
                            text_node.firstChild.replaceWholeText(' ')
                date = facture.debut_recap
                while date.month == facture.debut_recap.month:
                    col = date.weekday()
                    if col < cells_count:
                        details = ""
                        row = (date.day + empty_cells - 1) / 7
                        cell = cells[row][col]
                        # ecriture de la date dans la cellule
                        text_node = cell.getElementsByTagName('text:p')[0]
                        if date in facture.jours_presence_non_facturee:
                            state = PRESENCE_NON_FACTUREE
                            details = " (%s)" % GetHeureString(facture.jours_presence_non_facturee[date])
                        elif date in facture.jours_absence_non_prevenue:
                            state = ABSENCE_NON_PREVENUE
                            details = " (%s)" % GetHeureString(facture.jours_absence_non_prevenue[date])
                        elif date in facture.jours_presence_selon_contrat:
                            state = PRESENT
                            details = " (%s)" % GetHeureString(facture.jours_presence_selon_contrat[date])
                        elif date in facture.jours_supplementaires:
                            state = SUPPLEMENT
                            details = " (%s)" % GetHeureString(facture.jours_supplementaires[date])
                        elif date in facture.jours_maladie_non_deduits:
                            state = MALADE
                            details = " (%s)" % GetHeureString(facture.jours_maladie_non_deduits[date])
                        elif date in facture.jours_maladie:
                            state = HOPITAL
                        elif facture.inscrit.IsDateConge(date):
                            state = CONGES
                        elif date in facture.jours_conges_non_factures:
                            state = VACANCES
                        elif date in facture.jours_vacances:
                            state = CONGES_DEPASSEMENT
                        else:
                            state = ABSENT
                        if text_node and text_node.firstChild:
                            text_node.firstChild.replaceWholeText('%d%s' % (date.day, details))
                        cell.setAttribute('table:style-name', 'Presences.%s' % couleurs[state])
                    date += datetime.timedelta(1)
                for i in range(row + 1, len(rows)):
                    table.removeChild(rows[i])
        ReplaceTextFields(section, facture.fields)

    def GetMetas(self, dom):
        metas = dom.getElementsByTagName('meta:user-defined')
        for meta in metas:
            # print meta.toprettyxml()
            name = meta.getAttribute('meta:name')
            try:
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = float(value)
                else:
                    self.metas[name] = value
            except:
                pass

    def execute(self, filename, dom):
        global couleurs

        if filename == 'meta.xml':
            self.GetMetas(dom)
            return None

        fields = GetCrecheFields(creche)
        if filename != 'content.xml':
            ReplaceTextFields(dom, fields)
            return None

        errors = {}

        # print dom.toprettyxml()

        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.childNodes[:]

        if "Couleurs" in self.metas:
            couleurs = eval(self.metas["Couleurs"])
            print "METAS COULEURS", couleurs
        else:
            styleC3, styleD3 = False, False
            for style in doc.getElementsByTagName('style:style'):
                if style.name == 'Presences.D3':
                    styleD3 = True
            if not styleD3:
                couleurs[CONGES_DEPASSEMENT] = 'B3'

        done = []

        for index, inscrit in enumerate(self.inscrits):
            if config.options & FACTURES_FAMILLES:
                skip = False
                enfants = [enfant for enfant in GetInscritsFamille(inscrit.famille) if enfant.HasFacture(self.periode)]
                for enfant in enfants:
                    if enfant in done:
                        skip = True
                        break
                    else:
                        done.append(enfant)
                if skip:
                    continue
            else:
                enfants = [inscrit]

            prenoms = []
            factures = []
            total_facture = 0.0
            has_errors = False
            for enfant in enfants:
                try:
                    prenoms.append(enfant.prenom)
                    facture = Facture(enfant, self.periode.year, self.periode.month, options=TRACES)
                    total_facture += facture.total
                except CotisationException, e:
                    errors["%s %s" % (enfant.prenom, enfant.nom)] = e.errors
                    has_errors = True
                    continue
                last_inscription = None
                for tmp in enfant.inscriptions:
                    if not last_inscription or not last_inscription.fin or (tmp.fin and tmp.fin > last_inscription.fin):
                        last_inscription = tmp
                facture.fields = fields + GetInscritFields(enfant) + GetInscriptionFields(last_inscription) + GetFactureFields(facture) + GetCotisationFields(facture.last_cotisation)
                factures.append(facture)

            if has_errors:
                continue

            solde = CalculeSolde(inscrit.famille, GetMonthEnd(self.periode))

            for template in templates:
                clone = template.cloneNode(1)
                if clone.nodeName in ("draw:frame", "draw:custom-shape"):
                    doc.insertBefore(clone, template)
                else:
                    doc.appendChild(clone)
                if clone.hasAttribute("text:anchor-page-number"):
                    clone.setAttribute("text:anchor-page-number", str(index + 1))

                tables = clone.getElementsByTagName('table:table')
                for table in tables:
                    table_name = table.getAttribute('table:name')
                    # Le(s) tableau(x) des montants détaillés
                    if table_name == 'Montants':
                        for i, facture in enumerate(factures):
                            if i < len(factures) - 1:
                                montants_table = table.cloneNode(1)
                                clone.insertBefore(montants_table, table)
                            else:
                                montants_table = table
                            montants_table.setAttribute('table:name', "Montants%d" % (i + 1))
                            rows = montants_table.getElementsByTagName('table:table-row')
                            for row in rows:
                                prettyxml = row.toprettyxml()
                                if (("&lt;frais-inscription&gt;" in prettyxml and not facture.frais_inscription) or
                                    ("&lt;correction&gt;" in prettyxml and not facture.correction) or
                                    ("&lt;supplement-activites&gt;" in prettyxml and not facture.supplement_activites) or
                                    ("&lt;supplement&gt;" in prettyxml and not facture.supplement) or
                                    ("&lt;supplement-avant-regularisation&gt;" in prettyxml and not facture.supplement_avant_regularisation) or
                                    ("&lt;deduction-avant-regularisation&gt;" in prettyxml and not facture.deduction_avant_regularisation) or
                                    ("&lt;regularisation&gt;" in prettyxml and not facture.regularisation) or
                                    ("&lt;heures-absence-non-prevenue&gt;" in prettyxml and not facture.jours_absence_non_prevenue) or
                                    ("&lt;heures-maladie-non-deduites&gt;" in prettyxml and not facture.jours_maladie_non_deduits) or
                                    ("&lt;deduction&gt;" in prettyxml and not facture.deduction)):
                                    montants_table.removeChild(row)
                            ReplaceTextFields(montants_table, facture.fields)

                sections = clone.getElementsByTagName('text:section')
                recap_section_found = False
                for section in sections:
                    section_name = section.getAttribute('text:name')
                    # Le(s) sections(x) des presences du mois
                    if section_name == "SectionRecap":
                        recap_section_found = True
                        for i, facture in enumerate(factures):
                            if i < len(factures) - 1:
                                section_clone = section.cloneNode(1)
                                clone.insertBefore(section_clone, section)
                            else:
                                section_clone = section
                            self.FillRecapSection(section_clone, facture)

                # Les autres champs de la facture
                facture_fields = fields + GetFamilleFields(inscrit.famille) + \
                    [('total', total_facture, FIELD_EUROS), ('solde', solde, FIELD_EUROS),
                     ('prenoms', ", ".join(prenoms)),
                     ('montant-a-regler', total_facture + solde, FIELD_EUROS),
                     ('url-tipi', GetUrlTipi(inscrit.famille))] + \
                    GetFactureFields(factures[0]) + \
                    self.GetFactureCustomFields(inscrit, inscrit.famille, facture)
                ReplaceTextFields(clone, facture_fields)

                if not recap_section_found:
                    self.FillRecapSection(clone, facture)

        for template in templates:
            doc.removeChild(template)

        # print doc.toprettyxml()
        return errors

    def GetFactureCustomFields(self, inscrit, famille, facture):
        fields = []
        for key in self.metas:
            if key.startswith("formule "):
                label = key[8:]
                try:
                    value = eval(self.metas[key])
                except Exception, e:
                    print "Exception formule:", label, self.metas[key], e
                    continue
                if isinstance(value, tuple):
                    field = label, value[0], value[1]
                else:
                    field = label, value
                fields.append(field)
        return fields
