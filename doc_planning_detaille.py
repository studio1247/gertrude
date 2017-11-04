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

from constants import *
from database import Inscription
from functions import *
from facture import *
from cotisation import CotisationException
from planning_line import BasePlanningSeparator
from ooffice import *


class PlanningDetailleModifications:
    title = "Planning détaillé"
    template = "Planning detaille.odg"

    def __init__(self, periode, site=None, groupe=None):
        self.multi = False
        self.site = site
        self.groupe = groupe
        self.start, self.end = periode
        if IsTemplateFile("Planning detaille.ods"):
            self.template = 'Planning detaille.ods'
            self.default_output = "Planning detaille %s %d.ods" % (months[self.start.month - 1], self.start.year)
        else:
            self.template = 'Planning detaille.odg'
            if self.start == self.end:
                self.default_output = "Planning presences %s.odg" % GetDateString(self.start, weekday=False)
            else:
                self.default_output = "Planning presences %s-%s.odg" % (GetDateString(self.start, weekday=False), GetDateString(self.end, weekday=False))
        self.errors = {}
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
        self.email = None

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print(meta.toprettyxml())
                name = meta.getAttribute('meta:name').lower()
                if len(meta.childNodes) > 0:
                    value = meta.childNodes[0].wholeText
                    value_type = meta.getAttribute('meta:value-type')
                    if value_type == "float":
                        self.metas[name] = float(value)
                    elif value_type == "boolean":
                        self.metas[name] = True if value == "true" else False
                    else:
                        self.metas[name] = value
            # for name in self.metas:
            #     print("Meta", name, type(self.metas[name]), self.metas[name])
            return None
        elif filename != 'content.xml':
            return None
        elif IsTemplateFile("Planning detaille.ods"):
            if self.metas["format"] == 1:
                return self.executeTemplateCalcJulien(filename, dom)
            elif self.metas["format"] == 2:
                return self.executeTemplateCalc123APetitsPas(filename, dom)
            else:
                return self.executeTemplateCalc(filename, dom)
        else:
            if self.metas["format"] == "one-page":
                return self.executeTemplateOnePage(filename, dom)
            else:
                return self.executeTemplateDraw(filename, dom)

    def executeTemplateDraw(self, filename, dom):
        affichage_min = int(database.creche.affichage_min * 60 / BASE_GRANULARITY)
        affichage_max = int(database.creche.affichage_max * 60 / BASE_GRANULARITY)
        step = (21.0-self.metas["left"]-self.metas["right"]-self.metas["labels-width"]) / (affichage_max - affichage_min)

        drawing = dom.getElementsByTagName('office:drawing').item(0)
        if not drawing:
            drawing = dom.getElementsByTagName('office:presentation').item(0)

        template = drawing.getElementsByTagName("draw:page").item(0)
        # print(template.toprettyxml())
        shapes = getNamedShapes(template)
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
                ReplaceTextFields(node, [('category', text)])
                page.appendChild(node)

        day = self.start
        while day <= self.end:
            if day in database.creche.jours_fermeture:
                day += datetime.timedelta(1)
                continue

            lines_enfants = GetLines(day, database.creche.inscrits, presence=not self.metas["lignes-vides"], site=self.site, groupe=self.groupe, summary=SUMMARY_ENFANT)
            lines_enfants = GetEnfantsTriesSelonParametreTriPlanning(lines_enfants)
            lines_salaries = GetLines(day, database.creche.salaries, site=self.site, summary=SUMMARY_SALARIE)

            if lines_salaries:
                lines = lines_enfants + [BasePlanningSeparator("Salariés")] + lines_salaries
            else:
                lines = lines_enfants

            pages_count = 1 + (len(lines)) / self.metas["lines-max"]
            for page_index in range(pages_count):
                lines_count = min(self.metas["lines-max"], len(lines)-page_index*self.metas["lines-max"])
                page = template.cloneNode(1)
                page.setAttribute("draw:name", GetDateString(day))
                drawing.appendChild(page)

                # le quadrillage et l'echelle
                h = affichage_min
                while h <= affichage_max:
                    if h % (60 / BASE_GRANULARITY) == 0:
                        node = shapes["legende-heure"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] - 0.5 + (float(h)-affichage_min) * step))
                        # node.setAttribute('svg:y', '1cm')
                        node.setAttribute('svg:width', '1cm')
                        node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % int(round(h/(60 / BASE_GRANULARITY))))
                        page.appendChild(node)
                        node = shapes["ligne-heure"].cloneNode(1)
                    else:
                        node = shapes["ligne-quart-heure"].cloneNode(1)
                    node.setAttribute('svg:x1', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h-affichage_min) * step))
                    # node.setAttribute('svg:y1', '2cm')
                    node.setAttribute('svg:x2', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h-affichage_min) * step))
                    # node.setAttribute('svg:y2', '29cm')
                    page.appendChild(node)
                    h += database.creche.granularite / BASE_GRANULARITY

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
                        fields = [('nom', line.nom),
                                  ('prenom', line.prenom),
                                  ('label', line.label)]
                        ReplaceTextFields(node, fields)
                        page.appendChild(node)
                        for timeslot in line.timeslots:
                            a, b, v = timeslot.debut, timeslot.fin, timeslot.value
                            if v >= 0:
                                key = "activite-%d" % v
                                if key in shapes:
                                    # print(a,b,v)
                                    node = shapes[key].cloneNode(1)
                                    node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + float(a - affichage_min) * step))
                                    node.setAttribute('svg:y', '%fcm' % (0.10 + self.metas["top"] + self.metas["line-height"] * i))
                                    node.setAttribute('svg:width', '%fcm' % ((b - a) * step))
                                    if isinstance(line.inscription, Inscription):
                                        allergies = ', '.join(line.inscription.inscrit.get_allergies())
                                    else:
                                        allergies = ''
                                    ReplaceTextFields(node, [('texte', ''), ('allergies', allergies)])
                                    page.appendChild(node)
                                else:
                                    print("Pas de forme pour %s" % key)

                if self.metas["summary"] and page_index + 1 == pages_count:
                    AddCategoryShape(page, "Totaux", 0.20 + self.metas["top"] + self.metas["line-height"] * lines_count)

                    # le récapitulatif par activité
                    i = lines_count
                    summary = GetActivitiesSummary(lines)[0]
                    for activity in summary.keys():
                        i += 1
                        if activity == PRESENCE_SALARIE:
                            label = "Présences salariés"
                        elif activity == 0:
                            label = "Présences"
                        else:
                            label = database.creche.activites[activity].label
                        node = shapes["libelle"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % self.metas["left"])
                        node.setAttribute('svg:y', '%fcm' % (self.metas["top"] + self.metas["line-height"] * i))
                        node.setAttribute('svg:width', '%fcm' % self.metas["labels-width"])
                        fields = [('nom', ''),
                                  ('prenom', label),
                                  ('label', label)]
                        ReplaceTextFields(node, fields)
                        page.appendChild(node)
                        line = summary[activity]
                        x = affichage_min
                        v, w = 0, 0
                        a = 0
                        while x <= affichage_max:
                            if x == affichage_max:
                                nv, nw = 0, 0
                            else:
                                nv, nw = line.array[x]

                            if activity == 0 and (nw == 0 or nv > database.creche.GetCapacite(day.weekday()) or float(nv)/nw > 6.5):
                                nw = activity | SUPPLEMENT
                            else:
                                nw = activity

                            if nv != v or nw != w:
                                if v != 0:
                                    # print(a, x, v)
                                    key = "activite-%d" % w
                                    if key in shapes:
                                        node = shapes[key].cloneNode(1)
                                    else:
                                        key = "activite-%d" % (w & ~SUPPLEMENT)
                                        if key in shapes:
                                            node = shapes[key].cloneNode(1)
                                        else:
                                            print("Pas de forme pour %s" % key)
                                            node = None
                                    if node:
                                        node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (float(a - affichage_min) * step)))
                                        node.setAttribute('svg:y', '%fcm' % (0.10 + self.metas["top"] + self.metas["line-height"] * i))
                                        node.setAttribute('svg:width', '%fcm' % (float(x - a) * step))
                                        ReplaceTextFields(node, [('texte', '%d' % v)])
                                        page.appendChild(node)
                                a = x
                                v, w = nv, nw
                            x += database.creche.granularite / BASE_GRANULARITY
                fields = GetCrecheFields(database.creche) + GetSiteFields(self.site)
                if pages_count > 1:
                    fields.append(('date', GetDateString(day) + " (%d/%d)" % (page_index + 1, pages_count)))
                else:
                    fields.append(('date', GetDateString(day)))

                ReplaceTextFields(page, fields)
            day += datetime.timedelta(1)
        return None

    def executeTemplateOnePage(self, filename, dom):
        affichage_min = int(database.creche.affichage_min * 60 / BASE_GRANULARITY)
        affichage_max = int(database.creche.affichage_max * 60 / BASE_GRANULARITY)
        step = (21.0 - self.metas["left"] - self.metas["right"] - self.metas["labels-width"]) / (affichage_max - affichage_min)

        drawing = dom.getElementsByTagName('office:drawing').item(0)
        if not drawing:
            drawing = dom.getElementsByTagName('office:presentation').item(0)

        template = drawing.getElementsByTagName("draw:page").item(0)
        # print(template.toprettyxml())
        shapes = getNamedShapes(template)
        # print(shapes)
        for shape in shapes:
            if shape in ["legende-heure", "ligne-heure", "ligne-quart-heure", "libelle", "jour", "separateur", "ligne-cahier", "category"] or shape.startswith("activite-"):
                template.removeChild(shapes[shape])
        drawing.removeChild(template)
        if not "activite-%d" % PRESENCE_SALARIE in shapes:
            shapes["activite-%d" % PRESENCE_SALARIE] = shapes["activite-%d" % 0]

        def drawPage(people, days, salaries=False):
            page = template.cloneNode(1)
            page.setAttribute("draw:name", GetDateString(self.start))
            drawing.appendChild(page)

            # le quadrillage
            h = affichage_min
            while h <= affichage_max:
                if h % (60 / BASE_GRANULARITY) == 0:
                    node = shapes["ligne-heure"].cloneNode(1)
                else:
                    node = shapes["ligne-quart-heure"].cloneNode(1)
                node.setAttribute('svg:x1', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h - affichage_min) * step))
                node.setAttribute('svg:x2', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + (h - affichage_min) * step))
                page.appendChild(node)
                h += database.creche.granularite / BASE_GRANULARITY

            current_top = self.metas["top"] - 0.5

            for day in days:
                if day in database.creche.jours_fermeture:
                    continue

                # l'échelle
                h = affichage_min
                while h <= affichage_max:
                    if h % (60 / BASE_GRANULARITY) == 0:
                        node = shapes["legende-heure"].cloneNode(1)
                        node.setAttribute('svg:y', '%fcm' % current_top)
                        node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] - 0.5 + (float(h) - affichage_min) * step))
                        node.setAttribute('svg:width', '1cm')
                        node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % int(round(h / (60 / BASE_GRANULARITY))))
                        page.appendChild(node)
                    h += database.creche.granularite / BASE_GRANULARITY

                # le nom du jour
                node = shapes["jour"].cloneNode(1)
                node.setAttribute('svg:y', '%fcm' % current_top)
                fields = [('jour', GetDateString(day))]
                ReplaceTextFields(node, fields)
                page.appendChild(node)
                current_top += self.metas["line-height"]

                lines = GetLines(day, people, presence=not self.metas["lignes-vides"], site=self.site, groupe=self.groupe, summary=SUMMARY_ENFANT)
                lines = GetEnfantsTriesSelonParametreTriPlanning(lines)
                for i, line in enumerate(lines):
                    node = shapes["libelle"].cloneNode(1)
                    # node.setAttribute('svg:x', '%fcm' % self.metas["left"])
                    node.setAttribute('svg:y', '%fcm' % current_top)
                    # node.setAttribute('svg:width', '%fcm' % self.metas["labels-width"])
                    fields = [('nom', line.nom),
                              ('prenom', line.prenom),
                              ('label', truncate(line.label, self.metas["label-length"]))]
                    ReplaceTextFields(node, fields)
                    page.appendChild(node)
                    for timeslot in line.timeslots:
                        a, b, v = timeslot.debut, timeslot.fin, timeslot.value
                        if v >= 0:
                            if v == 0 and salaries:
                                label = "presence-salarie"
                            elif v in database.creche.activites:
                                label = database.creche.activites[v].label
                            else:
                                label = ""
                            shape = shapes.get("activite-%s" % label, shapes.get("activite-%d" % v, None))
                            if shape:
                                # print(a,b,v)
                                node = shape.cloneNode(1)
                                node.setAttribute('svg:x', '%fcm' % (self.metas["left"] + self.metas["labels-width"] + float(a - affichage_min) * step))
                                node.setAttribute('svg:y', '%fcm' % (0.20 + current_top))
                                node.setAttribute('svg:width', '%fcm' % ((b - a) * step))
                                page.appendChild(node)
                            else:
                                print("Pas de forme pour l'activité", v, label)

                    fields = GetCrecheFields(database.creche) + GetSiteFields(self.site)
                    ReplaceTextFields(page, fields)
                    current_top += self.metas["line-height"]

                if "line-per-day" in self.metas:
                    current_top += self.metas["line-height"] * (self.metas["line-per-day"] - len(lines))

        working_days = [(self.start + datetime.timedelta(i)) for i in range(5)]
        drawPage(database.creche.inscrits, working_days)
        drawPage(database.creche.salaries, working_days, salaries=True)
        if "split-saturdays" in self.metas:
            saturdays = [(self.start + datetime.timedelta(5 + 7 * i)) for i in range(5)]
            drawPage(database.creche.inscrits, saturdays)

        return None

    def executeTemplateCalc(self, filename, dom):
        # Garderie Ribambelle, planning detaillé

        debut, fin = GetMonthStart(self.start), GetMonthEnd(self.start)
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes, [('mois', months[self.start.month-1]),
                               ('annee', self.start.year)])

        template = lignes[6]
        semaines_template = lignes[3]
        total_template = lignes[7]
        montant_template = lignes[9]
        
        c = 0
        numero = debut.isocalendar()[1]
        while 1:
            cell = GetCell(semaines_template, c)
            if cell is None:
                break
            c += 1
            if ReplaceFields(cell, [('numero-semaine', numero)]):
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
                
                if date in inscrit.journees:
                    journee = inscrit.journees[date]
                else:
                    journee = inscrit.GetJourneeReferenceCopy(date)
                for t in range(2):
                    if journee and IsPresentDuringTranche(journee, tranches[t][0]*12, tranches[t][1]*12):
                        heures = HeuresTranche(journee, tranches[t][0] * 12, tranches[t][1]*12)
                        ReplaceFields(GetCell(row, cell), [('p', heures)])
                    cell += 1
                date += datetime.timedelta(1)    
            table.insertBefore(row, template)
            ReplaceTextFields(GetCell(row, 0), GetInscritFields(inscription.inscrit))
            ReplaceFields(row, [('p', '')])
            cellules = row.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('7', '%d' % (7+index))
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
                    
        return None

    def executeTemplateCalcJulien(self, filename, dom):
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")
        
        HEADER_LINE_COUNT = 5
        BODY_LINE_COUNT = 2
        FOOTER_LINE_COUNT = 1
        TEMPLATE_LINE_COUNT = HEADER_LINE_COUNT+BODY_LINE_COUNT+FOOTER_LINE_COUNT
        
        templateHeader = lignes[:HEADER_LINE_COUNT]
        templateLines = lignes[HEADER_LINE_COUNT:HEADER_LINE_COUNT + BODY_LINE_COUNT]
        templateFooter = lignes[HEADER_LINE_COUNT + BODY_LINE_COUNT:TEMPLATE_LINE_COUNT]

        date = self.start
        while date <= self.end:
            if date in database.creche.jours_fermeture:
                date += datetime.timedelta(1)
                continue

            # Header            
            for line in templateHeader:
                node = line.cloneNode(1)
                ReplaceFields(node, [('semaine', date.isocalendar()[1]),
                                     ('jour', days[date.weekday()]),
                                     ('date', date2str(date))])
                table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
            
            # Body
            inscrits = GetLines(date, database.creche.inscrits, site=self.site, groupe=self.groupe)
            linesCount = 0
            for i, inscrit in enumerate(inscrits):
                if not isinstance(inscrit, BasePlanningSeparator):
                    if i % 2:
                        node = templateLines[1].cloneNode(1)
                    else:
                        node = templateLines[0].cloneNode(1)
                    fields = [('nom', inscrit.nom),
                              ('prenom', inscrit.prenom),
                              ('label', inscrit.label),
                              ('arrivee-depart', inscrit.GetHeureArriveeDepart()),
                              ('arrivee', inscrit.GetHeureArrivee()),
                              ('depart', inscrit.GetHeureDepart())]
                    ReplaceFields(node, fields)
                    table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
                    linesCount += 1

            # Footer
            for line in templateFooter:
                node = line.cloneNode(1)
                ReplaceFields(node, [('count', linesCount)])
                table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
            
            date += datetime.timedelta(1)
        
        for line in templateHeader + templateLines + templateFooter:
            table.removeChild(line)

    def executeTemplateCalc123APetitsPas(self, filename, dom):
        # Basé sur le template de Julien, mais avec un onglet par jour
        spreadsheet_template = dom.getElementsByTagName('office:spreadsheet').item(0)

        HEADER_LINE_COUNT = 5
        BODY_LINE_COUNT = 2
        FOOTER_LINE_COUNT = 0
        TEMPLATE_LINE_COUNT = HEADER_LINE_COUNT + BODY_LINE_COUNT + FOOTER_LINE_COUNT

        date = self.start
        while date <= self.end:
            if date in database.creche.jours_fermeture:
                date += datetime.timedelta(1)
                continue

            spreadsheet = spreadsheet_template.cloneNode(1)
            spreadsheet_template.parentNode.insertBefore(spreadsheet, spreadsheet_template)

            table = spreadsheet.getElementsByTagName("table:table")[0]
            table_name = "%s %s" % (days[date.weekday()], date2str(date))
            table_name = table_name.replace("/", "|")
            table.setAttribute("table:name", table_name)
            lignes = table.getElementsByTagName("table:table-row")

            templateHeader = lignes[:HEADER_LINE_COUNT]
            templateLines = lignes[HEADER_LINE_COUNT:HEADER_LINE_COUNT + BODY_LINE_COUNT]
            templateFooter = lignes[HEADER_LINE_COUNT + BODY_LINE_COUNT:TEMPLATE_LINE_COUNT]

            for groupe in database.creche.groupes:
                # Header
                for line in templateHeader:
                    node = line.cloneNode(1)
                    ReplaceFields(node, [('semaine', date.isocalendar()[1]),
                                         ('jour', days[date.weekday()]),
                                         ('date', date2str(date)),
                                         ('groupe', groupe.nom)
                                         ])
                    table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

                # Body
                inscrits = GetLines(date, database.creche.inscrits, site=self.site, groupe=groupe)
                linesCount = 0
                for i, inscrit in enumerate(inscrits):
                    if i % 2:
                        node = templateLines[1].cloneNode(1)
                    else:
                        node = templateLines[0].cloneNode(1)
                    fields = [('nom', inscrit.nom),
                              ('prenom', inscrit.prenom),
                              ('label', inscrit.label),
                              ('arrivee-depart', inscrit.GetHeureArriveeDepart()),
                              ('arrivee', inscrit.GetHeureArrivee()),
                              ('depart', inscrit.GetHeureDepart())]
                    ReplaceFields(node, fields)
                    table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])
                    linesCount += 1

                # Footer
                for line in templateFooter:
                    node = line.cloneNode(1)
                    ReplaceFields(node, [('count', linesCount)])
                    table.insertBefore(node, lignes[TEMPLATE_LINE_COUNT])

            # Remove the template lines
            for line in templateHeader + templateLines + templateFooter:
                table.removeChild(line)

            date += datetime.timedelta(1)

        spreadsheet_template.parentNode.removeChild(spreadsheet_template)


if __name__ == '__main__':
    import random
    database.init("databases/opagaio.db")
    database.load()
    modifications = PlanningDetailleModifications((datetime.date(2017, 7, 3), datetime.date(2017, 7, 7)))
    filename = "./test-%f.odt" % random.random()
    errors = GenerateOODocument(modifications, filename=filename, gauge=None)
    StartLibreOffice(filename)
