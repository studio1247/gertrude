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

from constants import months, days, BASE_GRANULARITY, PRESENCE_SALARIE, TRI_LIGNES_CAHIER, SUMMARY_ENFANT
from database import Inscrit
from functions import IsPresentDuringTranche, HeuresTranche, GetInscritFields, get_lines_summary, GetSiteFields, \
    GetCrecheFields, GetEnfantsTriesSelonParametreTriPlanning, truncate
from helpers import GetDateString, GetMonthStart, GetMonthEnd, date2str
from globals import database
from planning_line import BasePlanningSeparator, ChildPlanningLine, SalariePlanningLine, GetLines
from generation.opendocument import OpenDocumentDraw, OpenDocumentSpreadsheet, choose_document


class PlanningDetailleMixin:
    title = "Planning détaillé"
    
    def __init__(self, start, end, site=None, groupe=None):
        self.start = start
        self.end = end
        self.site = site
        self.groupe = groupe


class PlanningDetailleSpreadsheet(OpenDocumentSpreadsheet, PlanningDetailleMixin):
    template = "Planning detaille.ods"

    def __init__(self, start, end, site=None, groupe=None):
        OpenDocumentSpreadsheet.__init__(self)
        PlanningDetailleMixin.__init__(self, start, end, site, groupe)
        self.set_default_output("Planning detaille %s %d.ods" % (months[self.start.month - 1], self.start.year))
        
    def modify_content(self, dom):
        OpenDocumentSpreadsheet.modify_content(self, dom)
        if self.metas["format"] == 1:
            return self.modify_content_julien(dom)
        elif self.metas["format"] == 2:
            return self.modify_content_123apetitpas(dom)
        else:
            return self.modify_content_default(dom)

    def modify_content_julien(self, dom):
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        HEADER_LINE_COUNT = 5
        BODY_LINE_COUNT = 2
        FOOTER_LINE_COUNT = 1
        TEMPLATE_LINE_COUNT = HEADER_LINE_COUNT + BODY_LINE_COUNT + FOOTER_LINE_COUNT

        template_header = lignes[:HEADER_LINE_COUNT]
        template_lines = lignes[HEADER_LINE_COUNT:HEADER_LINE_COUNT + BODY_LINE_COUNT]
        template_footer = lignes[HEADER_LINE_COUNT + BODY_LINE_COUNT:TEMPLATE_LINE_COUNT]

        date = self.start
        while date <= self.end:
            if date in database.creche.jours_fermeture:
                date += datetime.timedelta(1)
                continue

            # Header
            for line in template_header:
                node = line.cloneNode(1)
                self.replace_cell_fields(node, [('semaine', date.isocalendar()[1]),
                                     ('jour', days[date.weekday()]),
                                     ('date', date2str(date))])
                table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

            # Body
            inscrits = GetLines(date, database.creche.inscrits, site=self.site, groupe=self.groupe)
            lines_count = 0
            for i, inscrit in enumerate(inscrits):
                if not isinstance(inscrit, BasePlanningSeparator):
                    if i % 2:
                        node = template_lines[1].cloneNode(1)
                    else:
                        node = template_lines[0].cloneNode(1)
                    fields = [('nom', inscrit.nom),
                              ('prenom', inscrit.prenom),
                              ('label', inscrit.label),
                              ('arrivee-depart', inscrit.GetHeureArriveeDepart()),
                              ('arrivee', inscrit.GetHeureArrivee()),
                              ('depart', inscrit.GetHeureDepart())]
                    self.replace_cell_fields(node, fields)
                    table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
                    lines_count += 1

            # Footer
            for line in template_footer:
                node = line.cloneNode(1)
                self.replace_cell_fields(node, [('count', lines_count)])
                table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

            date += datetime.timedelta(1)

        for line in template_header + template_lines + template_footer:
            table.removeChild(line)

    def modify_content_123apetitpas(self, dom):
        # Basé sur le template de Julien, mais avec un onglet par jour
        spreadsheet_template = dom.getElementsByTagName('office:spreadsheet').item(0)

        HEADER_LINE_COUNT = 5
        BODY_LINE_COUNT = 2
        FOOTER_LINE_COUNT = 0
        TEMPLATE_LINE_COUNT = HEADER_LINE_COUNT + BODY_LINE_COUNT + FOOTER_LINE_COUNT

        date = self.start
        while date <= self.end:
            if date not in database.creche.jours_fermeture:
                spreadsheet = spreadsheet_template.cloneNode(1)
                spreadsheet_template.parentNode.insertBefore(spreadsheet, spreadsheet_template)

                table = spreadsheet.getElementsByTagName("table:table")[0]
                table_name = "%s %s" % (days[date.weekday()], date2str(date))
                table_name = table_name.replace("/", "|")
                table.setAttribute("table:name", table_name)
                lignes = table.getElementsByTagName("table:table-row")

                template_header = lignes[:HEADER_LINE_COUNT]
                template_lines = lignes[HEADER_LINE_COUNT:HEADER_LINE_COUNT + BODY_LINE_COUNT]
                template_footer = lignes[HEADER_LINE_COUNT + BODY_LINE_COUNT:TEMPLATE_LINE_COUNT]

                for groupe in database.creche.groupes:
                    # Header
                    for line in template_header:
                        node = line.cloneNode(1)
                        self.replace_cell_fields(node, [
                            ('semaine', date.isocalendar()[1]),
                            ('jour', days[date.weekday()]),
                            ('date', date2str(date)),
                            ('groupe', groupe.nom)
                        ])
                        table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

                    # Body
                    inscrits = GetLines(date, database.creche.inscrits, site=self.site, groupe=groupe)
                    lines_count = 0
                    for i, inscrit in enumerate(inscrits):
                        if i % 2:
                            node = template_lines[1].cloneNode(1)
                        else:
                            node = template_lines[0].cloneNode(1)
                        fields = [('nom', inscrit.nom),
                                  ('prenom', inscrit.prenom),
                                  ('label', inscrit.label),
                                  ('arrivee-depart', inscrit.GetHeureArriveeDepart()),
                                  ('arrivee', inscrit.GetHeureArrivee()),
                                  ('depart', inscrit.GetHeureDepart())]
                        self.replace_cell_fields(node, fields)
                        table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
                        lines_count += 1

                    # Footer
                    for line in template_footer:
                        node = line.cloneNode(1)
                        self.replace_cell_fields(node, [('count', lines_count)])
                        table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

                # Remove the template lines
                for line in template_header + template_lines + template_footer:
                    table.removeChild(line)

            date += datetime.timedelta(1)

        spreadsheet_template.parentNode.removeChild(spreadsheet_template)

    def modify_content_default(self, dom):
        # Garderie Ribambelle, planning detaillé

        debut, fin = GetMonthStart(self.start), GetMonthEnd(self.start)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        self.replace_cell_fields(lignes, [('mois', months[self.start.month - 1]),
                                          ('annee', self.start.year)])

        template = lignes[6]
        semaines_template = lignes[3]
        total_template = lignes[7]
        montant_template = lignes[9]

        c = 0
        numero = debut.isocalendar()[1]
        while 1:
            cell = self.get_cell(semaines_template, c)
            if cell is None:
                break
            c += 1
            if self.replace_cell_fields(cell, [('numero-semaine', numero)]):
                numero += 1

        inscriptions = database.creche.select_inscriptions(debut, fin)
        for index, inscription in enumerate(inscriptions):
            inscrit = inscription.inscrit
            row = template.cloneNode(1)
            # print(row.toprettyxml())
            date = debut
            cell = 0
            weekday = date.weekday()
            if weekday == 6:
                date += datetime.timedelta(1)
            elif weekday == 5:
                date += datetime.timedelta(2)
            elif weekday > 0:
                cell = weekday * 2 + 1
            tranches = [(database.creche.ouverture, 12), (14, database.creche.fermeture)]
            while date <= fin:
                weekday = date.weekday()
                if weekday == 2 or weekday >= 5:
                    date += datetime.timedelta(1)
                    continue
                if weekday == 0:
                    cell += 1
                journee = inscrit.GetJournee(date)
                for t in range(2):
                    if journee and IsPresentDuringTranche(journee, tranches[t][0] * 12, tranches[t][1] * 12):
                        heures = HeuresTranche(journee, tranches[t][0] * 12, tranches[t][1] * 12)
                        self.replace_cell_fields(self.get_cell(row, cell), [('p', heures)])
                    cell += 1
                date += datetime.timedelta(1)
            table.insertBefore(row, template)
            self.replace_text_fields(self.get_cell(row, 0), GetInscritFields(inscription.inscrit))
            self.replace_cell_fields(row, [('p', '')])
            cellules = row.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('7', '%d' % (7 + index))
                    cellule.setAttribute('table:formula', formule)

        table.removeChild(template)

        for template in (total_template, montant_template):
            cellules = template.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('9', '%d' % (7 + len(inscriptions)))
                    formule = formule.replace('8', '%d' % (6 + len(inscriptions)))
                    cellule.setAttribute('table:formula', formule)

        return True


class PlanningDetailleDraw(OpenDocumentDraw, PlanningDetailleMixin):
    template = "Planning detaille.odg"

    def __init__(self, start, end, site=None, groupe=None):
        OpenDocumentDraw.__init__(self)
        PlanningDetailleMixin.__init__(self, start, end, site, groupe)
        if self.start == self.end:
            self.set_default_output("Planning presences %s.odg" % GetDateString(self.start, weekday=False))
        else:
            self.set_default_output("Planning presences %s-%s.odg" % (GetDateString(self.start, weekday=False), GetDateString(self.end, weekday=False)))
        self.metas = {"format": 0,
                      "left": 1.5,
                      "right": 2.0,
                      "top": 6.0,
                      "label-length": 20,
                      "labels-width": 3.5,
                      "line-height": 0.75,
                      "lines-max": 25,
                      "lignes-vides": False,
                      "summary": True
                      }

    def modify_content(self, dom):
        OpenDocumentDraw.modify_content(self, dom)
        if self.metas["format"] == "one-page":
            return self.modify_content_one_page( dom)
        else:
            return self.modify_content_default(dom)

    @staticmethod
    def get_timeslot_shape(shapes, timeslot, salarie=False):
        key1 = "activite-%s-%s" % ("salarie" if salarie else "enfant", timeslot.activity.label)
        key2 = "activite-%s" % timeslot.activity.label
        key3 = "activite-%d" % (timeslot.activity.mode if timeslot.activity.mode <= 0 else database.creche.activites.index(timeslot.activity) + 1)
        if key1 in shapes:
            return shapes[key1]
        elif key2 in shapes:
            return shapes[key2]
        elif key3 in shapes:
            return shapes[key3]
        else:
            print("Pas de forme pour l'activité %s: %s, %s, %s" % (timeslot.activity.label, key1, key2, key3))
            return None

    def modify_content_default(self, dom):
        affichage_min = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))
        affichage_max = int(database.creche.affichage_max * (60 // BASE_GRANULARITY))
        step = (21.0-self.metas["left"]-self.metas["right"]-self.metas["labels-width"]) / (affichage_max - affichage_min)

        drawing = dom.getElementsByTagName('office:drawing').item(0)
        if not drawing:
            drawing = dom.getElementsByTagName('office:presentation').item(0)

        template = drawing.getElementsByTagName("draw:page").item(0)
        # print(template.toprettyxml())
        shapes = self.get_named_shapes(template)
        # print(shapes)
        for shape in shapes:
            if shape in ["legende-heure", "ligne-heure", "ligne-quart-heure", "libelle", "separateur", "ligne-cahier", "category"] or shape.startswith("activite-"):
                template.removeChild(shapes[shape])
        drawing.removeChild(template)
        if not "activite-%d" % PRESENCE_SALARIE in shapes:
            shapes["activite-%d" % PRESENCE_SALARIE] = shapes["activite-%d" % 0]

        def AddCategoryShape(page, text, y):
            if "category" in shapes:
                node = shapes["category"].cloneNode(1)
                node.setAttribute('svg:y', '%fcm' % y)
                self.replace_text_fields(node, [('category', text)])
                page.appendChild(node)

        date = self.start
        while date <= self.end:
            if date in database.creche.jours_fermeture:
                date += datetime.timedelta(1)
                continue

            lines_enfants = ChildPlanningLine.select(date, self.site, self.groupe)
            lines_salaries = SalariePlanningLine.select(date, self.site)
            if not self.metas["lignes-vides"]:
                lines_enfants = [line for line in lines_enfants if line.state > 0]
                lines_salaries = [line for line in lines_salaries if line.state > 0]

            lines = lines_enfants
            if lines_salaries:
                lines += [BasePlanningSeparator("Salariés")] + lines_salaries

            pages_count = 1 + (len(lines)) // self.metas["lines-max"]
            for page_index in range(pages_count):
                lines_count = min(self.metas["lines-max"], len(lines)-page_index*self.metas["lines-max"])
                page = template.cloneNode(1)
                page.setAttribute("draw:name", GetDateString(date))
                drawing.appendChild(page)

                # le quadrillage et l'echelle
                h = affichage_min
                while h <= affichage_max:
                    if h % (60 // BASE_GRANULARITY) == 0:
                        node = shapes["legende-heure"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] - 0.5 + (float(h)-affichage_min) * step))
                        # node.setAttribute('svg:y', '1cm')
                        node.setAttribute('svg:width', '1cm')
                        node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % int(round(h/(60 // BASE_GRANULARITY))))
                        page.appendChild(node)
                        node = shapes["ligne-heure"].cloneNode(1)
                    else:
                        node = shapes["ligne-quart-heure"].cloneNode(1)
                    node.setAttribute('svg:x1', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h-affichage_min) * step))
                    # node.setAttribute('svg:y1', '2cm')
                    node.setAttribute('svg:x2', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h-affichage_min) * step))
                    # node.setAttribute('svg:y2', '29cm')
                    page.appendChild(node)
                    h += database.creche.granularite // BASE_GRANULARITY

                if "ligne-cahier" in shapes:
                    ligne_cahier = shapes["ligne-cahier"].cloneNode(1)
                    ligne_cahier.setAttribute('svg:x1', '%fcm' % self.metas["left"])
                    ligne_cahier.setAttribute('svg:x2', '%fcm' % (21.0 - self.metas["right"]))
                else:
                    ligne_cahier = None

                ajoute_ligne_cahier = False

                # les enfants et salaries
                for i in range(lines_count):
                    line_idx = i + self.metas["lines-max"] * page_index
                    line = lines[line_idx]
                    if isinstance(line, BasePlanningSeparator):
                        AddCategoryShape(page, line.label, 0.20 + self.metas["top"] + self.metas["line-height"] * i)
                        ajoute_ligne_cahier = False
                    else:
                        if ajoute_ligne_cahier and ligne_cahier and database.creche.tri_planning & TRI_LIGNES_CAHIER:
                            node = ligne_cahier.cloneNode(1)
                            node.setAttribute('svg:y1', '%fcm' % (self.metas["top"] + self.metas["line-height"] * i))
                            node.setAttribute('svg:y2', '%fcm' % (self.metas["top"] + self.metas["line-height"] * i))
                            page.appendChild(node)
                        else:
                            ajoute_ligne_cahier = True
                        node = shapes["libelle"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % self.metas["left"])
                        node.setAttribute('svg:y', '%fcm' % (self.metas["top"] + self.metas["line-height"] * i))
                        node.setAttribute('svg:width', '%fcm' % self.metas["labels-width"])
                        fields = [('nom', line.who.nom),
                                  ('prenom', line.who.prenom),
                                  ('label', line.label)]
                        self.replace_text_fields(node, fields)
                        page.appendChild(node)
                        for timeslot in line.timeslots:
                            if timeslot.activity.has_horaires():
                                shape = self.get_timeslot_shape(shapes, timeslot)
                                if shape:
                                    node = shape.cloneNode(1)
                                    node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + float(timeslot.debut - affichage_min) * step))
                                    node.setAttribute('svg:y', '%fcm' % (0.10 + self.metas["top"] + self.metas["line-height"] * i))
                                    node.setAttribute('svg:width', '%fcm' % ((timeslot.fin - timeslot.debut) * step))
                                    allergies = line.who.get_allergies() if isinstance(line.who, Inscrit) else []
                                    self.replace_text_fields(node, [("texte", ""), ("commentaire", line.commentaire), ("allergies", ", ".join(allergies))])
                                    page.appendChild(node)

                if self.metas["summary"] and page_index + 1 == pages_count:
                    AddCategoryShape(page, "Totaux", 0.20 + self.metas["top"] + self.metas["line-height"] * lines_count)

                    # le récapitulatif par activité
                    i = lines_count
                    summary = get_lines_summary(lines)[0]
                    for activity in summary:
                        i += 1
                        node = shapes["libelle"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % self.metas["left"])
                        node.setAttribute('svg:y', '%fcm' % (self.metas["top"] + self.metas["line-height"] * i))
                        node.setAttribute('svg:width', '%fcm' % self.metas["labels-width"])
                        fields = [('nom', ''),
                                  ('prenom', activity.label),
                                  ('label', activity.label)]
                        self.replace_text_fields(node, fields)
                        page.appendChild(node)
                        line = summary[activity]
                        for timeslot in line:
                            shape = self.get_timeslot_shape(shapes, timeslot)
                            if shape:
                                node = shape.cloneNode(1)
                                node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (float(timeslot.debut - affichage_min) * step)))
                                node.setAttribute('svg:y', '%fcm' % (0.10 + self.metas["top"] + self.metas["line-height"] * i))
                                node.setAttribute('svg:width', '%fcm' % (float(timeslot.fin - timeslot.debut) * step))
                                self.replace_text_fields(node, [('texte', str(timeslot.value))])
                                page.appendChild(node)
                fields = GetCrecheFields(database.creche) + GetSiteFields(self.site)
                if pages_count > 1:
                    fields.append(('date', GetDateString(date) + " (%d/%d)" % (page_index + 1, pages_count)))
                else:
                    fields.append(('date', GetDateString(date)))
                self.replace_text_fields(page, fields)
            date += datetime.timedelta(1)
        return True

    def modify_content_one_page(self, dom):
        affichage_min = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))
        affichage_max = int(database.creche.affichage_max * (60 // BASE_GRANULARITY))
        step = (21.0 - self.metas["left"] - self.metas["right"] - self.metas["labels-width"]) / (affichage_max - affichage_min)

        drawing = dom.getElementsByTagName('office:drawing').item(0)
        if not drawing:
            drawing = dom.getElementsByTagName('office:presentation').item(0)

        template = drawing.getElementsByTagName("draw:page").item(0)
        # print(template.toprettyxml())
        shapes = self.get_named_shapes(template)
        # print(shapes)
        for shape in shapes:
            if shape in ["legende-heure", "ligne-heure", "ligne-quart-heure", "libelle", "jour", "separateur", "ligne-cahier", "category"] or shape.startswith("activite-"):
                template.removeChild(shapes[shape])
        drawing.removeChild(template)
        if not "activite-%d" % PRESENCE_SALARIE in shapes:
            shapes["activite-%d" % PRESENCE_SALARIE] = shapes["activite-%d" % 0]

        def draw_page(people, days, salaries=False):
            page = template.cloneNode(1)
            page.setAttribute("draw:name", GetDateString(self.start))
            drawing.appendChild(page)

            # le quadrillage
            h = affichage_min
            while h <= affichage_max:
                if h % (60 // BASE_GRANULARITY) == 0:
                    node = shapes["ligne-heure"].cloneNode(1)
                else:
                    node = shapes["ligne-quart-heure"].cloneNode(1)
                node.setAttribute('svg:x1', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h - affichage_min) * step))
                node.setAttribute('svg:x2', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h - affichage_min) * step))
                page.appendChild(node)
                h += database.creche.granularite // BASE_GRANULARITY

            current_top = self.metas["top"] - 0.5

            for day in days:
                if day in database.creche.jours_fermeture:
                    continue

                # l'échelle
                h = affichage_min
                while h <= affichage_max:
                    if h % (60 // BASE_GRANULARITY) == 0:
                        node = shapes["legende-heure"].cloneNode(1)
                        node.setAttribute('svg:y', '%fcm' % current_top)
                        node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] - 0.5 + (float(h) - affichage_min) * step))
                        node.setAttribute('svg:width', '1cm')
                        node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % int(round(h / (60 // BASE_GRANULARITY))))
                        page.appendChild(node)
                    h += database.creche.granularite // BASE_GRANULARITY

                # le nom du jour
                node = shapes["jour"].cloneNode(1)
                node.setAttribute('svg:y', '%fcm' % current_top)
                fields = [('jour', GetDateString(day)),
                          ('jour-sans-annee', GetDateString(day, annee=False))]
                self.replace_text_fields(node, fields)
                page.appendChild(node)
                current_top += self.metas["line-height"]

                lines = GetLines(day, people, presence=not self.metas["lignes-vides"], site=self.site, groupe=self.groupe, summary=SUMMARY_ENFANT)
                lines = GetEnfantsTriesSelonParametreTriPlanning(lines)
                for line in lines:
                    node = shapes["libelle"].cloneNode(1)
                    # node.setAttribute('svg:x', '%fcm' % self.metas["left"])
                    node.setAttribute('svg:y', '%fcm' % current_top)
                    # node.setAttribute('svg:width', '%fcm' % self.metas["labels-width"])
                    fields = [('nom', line.nom),
                              ('prenom', line.prenom),
                              ('label', truncate(line.label, self.metas["label-length"]))]
                    self.replace_text_fields(node, fields)
                    page.appendChild(node)
                    timeslots = line.timeslots[:]
                    timeslots.sort(key=lambda timeslot: timeslot.activity.idx)
                    for timeslot in timeslots:
                        if timeslot.activity.mode >= 0:
                            shape = self.get_timeslot_shape(shapes, timeslot, salaries)
                            if shape:
                                node = shape.cloneNode(1)
                                node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + float(timeslot.debut - affichage_min) * step))
                                node.setAttribute('svg:y', '%fcm' % (0.20 + current_top))
                                node.setAttribute('svg:width', '%fcm' % ((timeslot.fin - timeslot.debut) * step))
                                page.appendChild(node)

                    fields = GetCrecheFields(database.creche) + GetSiteFields(self.site)
                    self.replace_text_fields(page, fields)
                    current_top += self.metas["line-height"]

                if "line-per-day" in self.metas:
                    current_top += self.metas["line-height"] * (self.metas["line-per-day"] - len(lines))

        working_days = [(self.start + datetime.timedelta(i)) for i in range(5)]
        draw_page(database.creche.inscrits, working_days)
        draw_page(database.creche.salaries, working_days, salaries=True)
        if "split-saturdays" in self.metas:
            saturdays = [(self.start + datetime.timedelta(5 + 7 * i)) for i in range(5)]
            draw_page(database.creche.inscrits, saturdays)

        return True


PlanningDetailleDocument = choose_document(
    PlanningDetailleSpreadsheet,
    PlanningDetailleDraw)


def test_planning_detaille():
    import random
    from document_dialog import StartLibreOffice
    database.init("databases/opagaio.db")
    database.load()
    database.creche.nom = "Micro-crèche Opagaïo-Bissy"
    document = PlanningDetailleDocument(datetime.date(2017, 11, 27), datetime.date(2017, 12, 3))
    document.generate("./test-%f.odt" % random.random())
    StartLibreOffice(document)


if __name__ == '__main__':
    test_planning_detaille()
