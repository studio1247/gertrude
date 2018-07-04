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

from facture import *
from cotisation import CotisationException
from ooffice import *
from database import Reservataire
from generation.opendocument import OpenDocumentText
from generation.email_helpers import SendToParentsMixin, SendToCAFMixin

PRESENCE_NON_FACTUREE = 256
CONGES = 257


class FactureMensuelle(OpenDocumentText, SendToParentsMixin, SendToCAFMixin):
    title = "Facture mensuelle"
    template = "Facture mensuelle.odt"

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

    @staticmethod
    def GetPrenomNom(who):
        if config.options & FACTURES_FAMILLES:
            return who.nom
        else:
            return GetPrenomNom(who)

        # TODO
        # if self.reservataire:
        #     self.introduction_filename = "Accompagnement facture reservataire.txt"
        # else:
        #     self.introduction_filename = "Accompagnement facture.txt"

    def __init__(self, inscrits, periode):
        OpenDocumentText.__init__(self)
        self.creche = database.creche
        self.last_facture = None
        self.periode = periode
        self.periode_facturation = periode
        if database.creche.temps_facturation != FACTURATION_FIN_MOIS:
            self.periode_facturation = GetMonthStart(periode - datetime.timedelta(1))
        self.reservataire = False
        if len(inscrits) > 0 and isinstance(inscrits[0], Reservataire):
            self.inscrits = inscrits
            self.reservataire = inscrits[0]
            self.site = None
            self.set_default_output("Facture %s %s %d.odt" % (self.reservataire.nom, months[periode.month - 1], periode.year))
            self.destination_emails[ENVOI_RESERVATAIRES] = [self.reservataire]
        elif len(inscrits) > 1:
            self.inscrits = GetEnfantsTriesSelonParametreTriFacture(inscrits)
            # TODO sauf si le site n'est pas le même pour tout le monde
            self.site = self.inscrits[0].get_inscriptions(self.periode_facturation, None)[0].site
            self.set_default_output("Factures %s %d.odt" % (months[periode.month - 1], periode.year))
        else:
            self.inscrits = inscrits
            who = self.inscrits[0]
            self.site = who.get_inscriptions(self.periode_facturation, None)[0].site
            self.set_default_output("Facture %s %s %d.odt" % (self.GetPrenomNom(who), months[periode.month - 1], periode.year))

        if not self.reservataire:
            SendToParentsMixin.__init__(self, self.default_output[:-4], "Accompagnement facture.txt", [], "%(count)d factures envoyées")
            SendToCAFMixin.__init__(self, "Factures (%(index)d/%(count)d)",  "Accompagnement factures.txt", "%(count)d factures envoyées")

        if self.reservataire:
            self.template = "Facture reservataire.odt"
        elif self.site and IsTemplateFile("Facture mensuelle %s.odt" % self.site.nom):
            self.template = "Facture mensuelle %s.odt" % self.site.nom
        elif IsTemplateFile("Facture mensuelle %s.odt" % database.creche.nom):
            self.template = "Facture mensuelle %s.odt" % database.creche.nom
        else:
            self.template = 'Facture mensuelle.odt'

    def split(self, who):
        return FactureMensuelle([who], self.periode)

    def fill_recap_section(self, section, facture):
        column_heures = 1 if "heures-facturees" in self.metas else 0
        empty_cells = facture.debut_recap.weekday()
        if "Week-end" in database.creche.feries and empty_cells > 4:
            empty_cells -= 7

        tables = section.getElementsByTagName("table:table")
        for table in tables:
            if table.getAttribute("table:name").startswith('Presences'):
                rows = table.getElementsByTagName("table:table-row")[1:]
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
                        row = (date.day + empty_cells - 1) // 7
                        cell = cells[row][col]
                        # ecriture de la date dans la cellule
                        text_node = cell.getElementsByTagName('text:p')[0]
                        if date in facture.jours_presence_non_facturee:
                            state = PRESENCE_NON_FACTUREE
                            details = " (%s)" % GetHeureString(facture.jours_presence_non_facturee[date])
                        elif date in facture.jours_absence_non_prevenue:
                            state = ABSENCE_NON_PREVENUE
                            details = " (%s)" % GetHeureString(facture.jours_absence_non_prevenue[date])
                        elif date in facture.jours_maladie_non_deduits:
                            state = MALADE
                            details = " (%s)" % GetHeureString(facture.jours_maladie_non_deduits[date])
                        elif date in facture.jours_maladie:
                            state = HOPITAL
                        elif facture.inscrit.is_date_conge(date):
                            state = CONGES
                        elif date in facture.jours_conges_non_factures:
                            state = VACANCES
                        elif date in facture.jours_vacances:
                            state = CONGES_DEPASSEMENT
                            details = " (%s)" % GetHeureString(
                                facture.jours_presence_selon_contrat[date][column_heures])
                        elif date in facture.jours_presence_selon_contrat:
                            state = PRESENT
                            details = " (%s)" % GetHeureString(facture.jours_presence_selon_contrat[date][column_heures])
                        elif date in facture.jours_supplementaires:
                            state = SUPPLEMENT
                            details = " (%s)" % GetHeureString(facture.jours_supplementaires[date][column_heures])
                        else:
                            state = ABSENT
                        if text_node and text_node.firstChild:
                            text_node.firstChild.replaceWholeText('%d%s' % (date.day, details))
                        cell.setAttribute('table:style-name', 'Presences.%s' % self.couleurs[state])
                    date += datetime.timedelta(1)
                for i in range(row + 1, len(rows)):
                    table.removeChild(rows[i])
        self.replace_text_fields(section, facture.fields)

    def is_row_removable(self, row, facture):
        prettyxml = row.toprettyxml()
        if (("&lt;frais-inscription&gt;" in prettyxml and not facture.frais_inscription) or
            ("&lt;correction&gt;" in prettyxml and not facture.correction) or
            ("&lt;supplement-activites&gt;" in prettyxml and not facture.supplement_activites) or
            ("&lt;supplement&gt;" in prettyxml and not facture.supplement) or
            ("&lt;supplement-avant-regularisation&gt;" in prettyxml and not facture.supplement_avant_regularisation) or
            ("&lt;supplement-heures-supplementaires&gt;" in prettyxml and not facture.supplement_heures_supplementaires) or
            ("&lt;deduction-avant-regularisation&gt;" in prettyxml and not facture.deduction_avant_regularisation) or
            ("&lt;regularisation&gt;" in prettyxml and not facture.regularisation) or
            ("&lt;heures-absence-non-prevenue&gt;" in prettyxml and not facture.jours_absence_non_prevenue) or
            ("&lt;heures-maladie-non-deduites&gt;" in prettyxml and not facture.jours_maladie_non_deduits) or
            ("&lt;deduction&gt;" in prettyxml and not facture.deduction)):
            return True
        for field in self.GetFactureCustomFields(facture):
            if field[0] in row.toprettyxml() and not field[1]:
                return True
        return False

    def modify_content(self, dom):
        fields = GetCrecheFields(database.creche)

        # print(dom.toprettyxml())

        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.childNodes[:]

        if "couleurs" in self.metas:
            self.couleurs = eval(self.metas["couleurs"])
            # print("couleurs", self.couleurs)
        else:
            styleB3, styleC3, styleD3 = False, False, False
            for style in doc.getElementsByTagName('style:style'):
                if style.name == 'Presences.B3':
                    styleB3 = True
                if style.name == 'Presences.C3':
                    styleC3 = True
                if style.name == 'Presences.D3':
                    styleD3 = True
            if not styleB3:
                self.couleurs[ABSENCE_NON_PREVENUE] = self.couleurs[ABSENT]
                self.couleurs[ABSENCE_CONGE_SANS_PREAVIS] = self.couleurs[ABSENT]
            if not styleC3:
                self.couleurs[CONGES] = self.couleurs[ABSENT]
            if not styleD3:
                self.couleurs[CONGES_DEPASSEMENT] = self.couleurs[CONGES]

        done = []

        if self.reservataire:
            for index, reservataire in enumerate(self.inscrits):
                for template in templates:
                    clone = template.cloneNode(1)
                    facture = FactureReservataire(reservataire, self.periode)
                    if reservataire.periode_facturation == 1:
                        mois_string = "%s %d" % (months[facture.debut.month - 1], facture.debut.year)
                    elif facture.fin.year == facture.debut.year:
                        mois_string = "%s à %s %d" % (months[facture.debut.month - 1], months[facture.fin.month - 1], facture.debut.year)
                    else:
                        mois_string = "%s %d à %s %d" % (months[facture.debut.month - 1], facture.debut.year, months[facture.fin.month - 1], facture.fin.year)

                    try:
                        numero = int(database.creche.numeros_facture[facture.debut].valeur)
                        numero += len([inscrit for inscrit in database.creche.inscrits if inscrit.has_facture(facture.debut)])
                        numero += self.reservataire.idx
                    except Exception as e:
                        print("Exception numéro de facture", e)
                        numero = 0

                    if config.numfact:
                        fields = {
                            "inscritid": len(database.creche.inscrits) + self.reservataire.idx,
                            "numero": numero,
                            "annee": facture.debut.year,
                            "mois": facture.debut.month
                        }
                        if "numero-global" in config.numfact:
                            fields["numero-global"] = config.numerotation_factures.get("reservataire-%d" % self.reservataire.idx, facture.debut)
                        numfact = config.numfact % fields
                    else:
                        numfact = "%03d%04d%02d" % (900+reservataire.idx, self.periode_facturation.year, self.periode_facturation.month)

                    fields = GetCrecheFields(database.creche) + GetReservataireFields(reservataire) + [
                        ("date", self.periode_facturation),
                        ("mois", mois_string),
                        ("numfact", numfact),
                        ('tarif-periode-reservataire', reservataire.tarif * facture.nombre_mois, FIELD_EUROS),
                    ]

                    inscrits = list(database.creche.select_inscrits(facture.debut, None, reservataire=reservataire))  # parce qu'on veut aussi voir les enfants qui arrivent plus tard
                    if inscrits:
                        inscrit = inscrits[0]
                        fields += GetInscritFields(inscrit)
                        if inscrit.inscriptions:
                            inscription = inscrit.inscriptions[-1]
                            fields += GetInscriptionFields(inscription)
                            try:
                                cotisation = Cotisation(inscrit, inscription.debut, options=NO_REVENUS | NO_PARENTS)
                                fields += GetCotisationFields(cotisation)
                            except Exception as e:
                                print(e)

                    # TODO self.introduction_fields.extend(fields)
                    self.replace_text_fields(clone, fields)

                    if clone.nodeName in ("draw:frame", "draw:custom-shape"):
                        doc.insertBefore(clone, template)
                    else:
                        doc.appendChild(clone)
                    if clone.hasAttribute("text:anchor-page-number"):
                        clone.setAttribute("text:anchor-page-number", str(index + 1))
        else:
            for index, inscrit in enumerate(self.inscrits):
                if config.options & FACTURES_FAMILLES:
                    skip = False
                    enfants = [enfant for enfant in GetInscritsFamille(inscrit.famille) if enfant.has_facture(self.periode)]
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
                site = None
                for enfant in enfants:
                    try:
                        prenoms.append(enfant.prenom)
                        facture = Facture(enfant, self.periode.year, self.periode.month, options=0 if (config.saas_port and not config.debug) else TRACES)
                        self.last_facture = facture
                        total_facture += facture.total_facture
                    except CotisationException as e:
                        self.errors[GetPrenomNom(enfant)] = e.errors
                        has_errors = True
                        continue

                    last_inscription = None
                    for tmp in enfant.inscriptions:
                        if not last_inscription or not last_inscription.fin or (tmp.fin and tmp.fin > last_inscription.fin):
                            last_inscription = tmp
                            site = last_inscription.site
                    facture.fields = fields + GetInscritFields(enfant) + GetInscriptionFields(last_inscription) + GetFactureFields(facture) + GetCotisationFields(facture.last_cotisation)
                    # TODO self.introduction_fields.extend(facture.fields)
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

                    if clone.tagName == "table:table":
                        tables = [clone]
                    else:
                        tables = clone.getElementsByTagName("table:table")
                    for table in tables:
                        table_name = table.getAttribute("table:name")
                        # Le(s) tableau(x) des montants détaillés
                        if table_name == "Montants":
                            for i, facture in enumerate(factures):
                                if i < len(factures) - 1:
                                    montants_table = table.cloneNode(1)
                                    clone.insertBefore(montants_table, table)
                                else:
                                    montants_table = table
                                montants_table.setAttribute("table:name", "Montants%d" % (i + 1))
                                rows = montants_table.getElementsByTagName("table:table-row")
                                for row in rows:
                                    if self.is_row_removable(row, facture):
                                        montants_table.removeChild(row)
                                self.replace_text_fields(montants_table, facture.fields)

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
                                self.fill_recap_section(section_clone, facture)

                    # Les autres champs de la facture
                    facture_fields = [
                        ('total', total_facture, FIELD_EUROS),
                        ('solde', solde, FIELD_EUROS),
                        ('prenoms', ", ".join(prenoms)),
                        ('montant-a-regler', total_facture + solde, FIELD_EUROS),
                        ('url-tipi', GetUrlTipi(inscrit.famille))]
                    facture_fields += factures[0].fields + self.GetFactureCustomFields(factures[0])
                    self.replace_text_fields(clone, facture_fields)

                    if not recap_section_found:
                        self.fill_recap_section(clone, facture)

                    self.modify_content_bitmaps(clone, site)

        for template in templates:
            doc.removeChild(template)

        # print(doc.toprettyxml())
        return True

    def GetFactureCustomFields(self, facture):
        inscrit = facture.inscrit
        famille = inscrit.famille
        fields = []
        for key in self.metas:
            if key.lower().startswith("formule "):
                label = key[8:]
                try:
                    value = eval(self.metas[key])
                except Exception as e:
                    print("Exception formule:", label, self.metas[key], e)
                    continue
                if isinstance(value, tuple):
                    field = label, value[0], value[1]
                else:
                    field = label, value
                fields.append(field)
        return fields


class RelanceFacture(FactureMensuelle):
    def __init__(self, who, date):
        self.historique = GetHistoriqueSolde(who if isinstance(who, Reservataire) else who.famille, date)
        self.solde = CalculeSoldeFromHistorique(self.historique)
        self.last_facture_date = date
        for line in self.historique:
            if not isinstance(line, EncaissementFamille) and not isinstance(line, EncaissementReservataire):
                self.last_facture_date = line.date
        FactureMensuelle.__init__(self, [who], self.last_facture_date)
        self.parents_subject = self.parents_subject.replace("Facture", "Retard de paiement")
        self.parents_success_message = self.parents_success_message.replace("Facture", "Relance")
        self.parents_introduction_filename = "Accompagnement relance.txt"
        self.set_fields([("solde", self.solde)])


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/elea.db")
    database.load()
    inscrits = [inscrit for inscrit in database.creche.inscrits if inscrit.prenom == "Ambre"]
    facture = FactureMensuelle(inscrits, datetime.date(2018, 2, 1))
    facture.generate("./test-%f.odt" % random.random())
    print(facture.output)
    StartLibreOffice(facture.output)
