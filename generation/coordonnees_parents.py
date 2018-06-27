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

import datetime

from constants import EXPORT_FAMILLES_PRESENTES, EXPORT_FAMILLES_FUTURES, EXPORT_FAMILLES_PARTIES
from functions import GetDateString, GetPrenomNom, GetInscritFields, GetParentFields, GetCrecheFields, GetSiteFields, \
    GetSalarieFields, GetInitialesPrenom
from globals import database
from generation.opendocument import OpenDocumentText, OpenDocumentSpreadsheet, choose_document


class CoordonneesParentsMixin:
    title = "Coordonnées des parents"

    def __init__(self, site, date, selection=EXPORT_FAMILLES_PRESENTES):
        self.site = site
        self.date = datetime.date.today() if date is None else date
        self.selection = selection

    def get_inscrits(self):
        result = []
        for inscrit in database.creche.inscrits:
            temporalite = 0
            for inscription in inscrit.inscriptions:
                if not inscription.preinscription and (self.site is None or inscription.site == self.site):
                    debut = inscription.debut
                    fin = inscription.depart if inscription.depart else inscription.fin
                    if debut and debut > datetime.date.today():
                        temporalite = EXPORT_FAMILLES_FUTURES
                    elif fin and fin < datetime.date.today():
                        temporalite = EXPORT_FAMILLES_PARTIES
                    else:
                        temporalite = EXPORT_FAMILLES_PRESENTES
                        break
            if temporalite & self.selection:
                result.append(inscrit)
        result.sort(key=lambda x: GetPrenomNom(x))
        return result

    def get_salaries(self):
        result = []
        for salarie in database.creche.salaries:
            temporalite = 0
            for contrat in salarie.contrats:
                if self.site is None or contrat.site == self.site:
                    if contrat.debut and contrat.debut > datetime.date.today():
                        temporalite = EXPORT_FAMILLES_FUTURES
                    elif contrat.fin and contrat.fin < datetime.date.today():
                        temporalite = EXPORT_FAMILLES_PARTIES
                    else:
                        temporalite = EXPORT_FAMILLES_PRESENTES
                        break
            if temporalite & self.selection:
                result.append(salarie)
        result.sort(key=lambda x: GetPrenomNom(x))
        return result


class CoordonneesParentsSpreadsheet(OpenDocumentSpreadsheet, CoordonneesParentsMixin):
    template = "Coordonnees parents.ods"

    def __init__(self, site, date, selection=EXPORT_FAMILLES_PRESENTES):
        OpenDocumentSpreadsheet.__init__(self)
        CoordonneesParentsMixin.__init__(self, site, date, selection)
        self.set_default_output("Coordonnees parents %s.ods" % GetDateString(self.date, weekday=False))

    def modify_content(self, dom):
        OpenDocumentSpreadsheet.modify_content(self, dom)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet')[0]
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")
        template = lignes[1]

        for inscrit in self.get_inscrits():
            inscrit_fields = GetInscritFields(inscrit)
            for parent in inscrit.famille.parents:
                if parent:
                    fields = inscrit_fields + GetParentFields(parent)
                    line = template.cloneNode(1)
                    self.replace_cell_fields(line, fields)
                    table.insertBefore(line, template)
                    inscrit_fields = [(field[0], "") for field in inscrit_fields]

        table.removeChild(template)
        return True


class CoordonneesParentsText(OpenDocumentText, CoordonneesParentsMixin):
    template = "Coordonnees parents.odt"

    def __init__(self, site, date, selection=EXPORT_FAMILLES_PRESENTES):
        OpenDocumentText.__init__(self)
        CoordonneesParentsMixin.__init__(self, site, date, selection)
        self.set_default_output("Coordonnees parents %s.odt" % GetDateString(self.date, weekday=False))

    def modify_content(self, dom):
        OpenDocumentText.modify_content(self, dom)
        fields = GetCrecheFields(database.creche)
        if self.site:
            fields += GetSiteFields(self.site)
        elif len(database.creche.sites) == 1:
            fields += GetSiteFields(database.creche.sites[0])
        fields.append(('date', '%.2d/%.2d/%d' % (self.date.day, self.date.month, self.date.year)))
        self.replace_text_fields(dom, fields)

        inscrits = self.get_inscrits()

        for table in dom.getElementsByTagName("table:table"):
            if table.getAttribute("table:name") == "Enfants":
                template = table.getElementsByTagName("table:table-row")[1]
                # print template.toprettyxml()
                for inscrit in inscrits:
                    line = template.cloneNode(1)
                    referents = [GetPrenomNom(referent) for referent in inscrit.famille.referents]
                    parents = [GetPrenomNom(parent) for parent in inscrit.famille.parents if parent is not None]
                    self.replace_text_fields(line, [
                        ('prenom', inscrit.prenom),
                        ('parents', ", ".join(parents)),
                        ('referents', ", ".join(referents)),
                        ('commentaire', None)])
                    phone_cell = line.getElementsByTagName('table:table-cell')[2]
                    phone_template = phone_cell.getElementsByTagName('text:p')[0]
                    phones = {}  # clé: [téléphone, initiales, ?travail]
                    emails = set()
                    for parent in inscrit.famille.parents:
                        if parent:
                            emails.add(parent.email)
                            for phone_type in ["domicile", "portable", "travail"]:
                                phone = getattr(parent, "telephone_" + phone_type)
                                if phone:
                                    if phone in phones.keys():
                                        phones[phone][1] = ""
                                    else:
                                        phones[phone] = [phone, GetInitialesPrenom(parent), phone_type == "travail"]
                    for phone, initiales, phone_type in phones.values():
                        if initiales and phone_type:
                            remark = "(%s travail)" % initiales
                        elif initiales:
                            remark = "(%s)" % initiales
                        elif phone_type:
                            remark = "(travail)"
                        else:
                            remark = ""
                        phone_line = phone_template.cloneNode(1)
                        self.replace_text_fields(phone_line, [('telephone', phone), ('remarque', remark)])
                        phone_cell.insertBefore(phone_line, phone_template)
                    phone_cell.removeChild(phone_template)
                    email_cell = line.getElementsByTagName('table:table-cell')[3]
                    email_template = email_cell.getElementsByTagName('text:p')[0]
                    for email in emails:
                        email_line = email_template.cloneNode(1)
                        self.replace_text_fields(email_line, [('email', email)])
                        email_cell.insertBefore(email_line, email_template)
                    email_cell.removeChild(email_template)
                    table.insertBefore(line, template)
                table.removeChild(template)

            if table.getAttribute("table:name") == 'Employes':
                template = table.getElementsByTagName("table:table-row")[0]
                # print template.toprettyxml()
                for salarie in self.get_salaries():
                    if 1:  # TODO
                        line = template.cloneNode(1)
                        self.replace_text_fields(line, GetSalarieFields(salarie))
                        table.insertBefore(line, template)
                table.removeChild(template)

        return True


CoordonneesParentsDocument = choose_document(
    CoordonneesParentsSpreadsheet,
    CoordonneesParentsText)


def test_coordonnees_parents():
    import random
    from document_dialog import StartLibreOffice
    database.init("../databases/lutinsminiac.db")
    database.load()
    database.creche.nom = "Les Petits Lutins du Canal"
    document = CoordonneesParentsDocument(None, datetime.date(2018, 2, 19))
    document.generate("./test-%f.ods" % random.random())
    StartLibreOffice(document.output)


if __name__ == '__main__':
    test_coordonnees_parents()
