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

from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from sqlobjects import Inscription
from ooffice import *

left = 1.5
right = 2.0
top = 6.0
labels_width = 3.5
line_height = 0.75
lines_max = 25


class PlanningDetailleModifications(object):
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
        self.metas = {"Format": 0}
        self.email = None

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print meta.toprettyxml()
                name = meta.getAttribute('meta:name')
                if len(meta.childNodes) > 0:
                    value = meta.childNodes[0].wholeText
                    if meta.getAttribute('meta:value-type') == 'float':
                        self.metas[name] = int(value)
                    else:
                        self.metas[name] = value
            return None        
        elif filename != 'content.xml':
            return None
        elif IsTemplateFile("Planning detaille.ods"):
            if self.metas["Format"] == 1:
                return self.executeTemplateCalcJulien(filename, dom)
            elif self.metas["Format"] == 2:
                return self.executeTemplateCalc123APetitsPas(filename, dom)
            else:
                return self.executeTemplateCalc(filename, dom)
        else:
            return self.executeTemplateDraw(filename, dom)

    def executeTemplateDraw(self, filename, dom):
        affichage_min = int(creche.affichage_min * 60 / BASE_GRANULARITY)
        affichage_max = int(creche.affichage_max * 60 / BASE_GRANULARITY)
        step = (21.0-left-right-labels_width) / (affichage_max - affichage_min)
       
        drawing = dom.getElementsByTagName('office:drawing').item(0)            
        if not drawing:
            drawing = dom.getElementsByTagName('office:presentation').item(0)
            
        template = drawing.getElementsByTagName("draw:page").item(0)
        # print template.toprettyxml()
        shapes = getNamedShapes(template)
        # print shapes
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

        lignes_vides = self.metas["lignes-vides"] if "lignes-vides" in self.metas else False

        day = self.start
        while day <= self.end:
            if day in creche.jours_fermeture:
                day += datetime.timedelta(1)
                continue

            lines_enfants = GetLines(day, creche.inscrits, presence=not lignes_vides, site=self.site, groupe=self.groupe, summary=SUMMARY_ENFANT)
            lines_enfants = GetEnfantsTriesSelonParametreTriPlanning(lines_enfants)
            lines_salaries = GetLines(day, creche.salaries, site=self.site, summary=SUMMARY_SALARIE)

            if lines_salaries:
                lines = lines_enfants + ["Salariés"] + lines_salaries
            else:
                lines = lines_enfants
            
            pages_count = 1 + (len(lines)) / lines_max
            for page_index in range(pages_count):
                lines_count = min(lines_max, len(lines)-page_index*lines_max)
                page = template.cloneNode(1)
                page.setAttribute("draw:name", GetDateString(day))
                drawing.appendChild(page)
                
                # le quadrillage et l'echelle
                h = affichage_min
                while h <= affichage_max:
                    if h % (60 / BASE_GRANULARITY) == 0:
                        node = shapes["legende-heure"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % (left + labels_width - 0.5 + (float(h)-affichage_min) * step))
                        # node.setAttribute('svg:y', '1cm')
                        node.setAttribute('svg:width', '1cm')
                        node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % int(round(h/(60 / BASE_GRANULARITY))))
                        page.appendChild(node)
                        node = shapes["ligne-heure"].cloneNode(1)
                    else:
                        node = shapes["ligne-quart-heure"].cloneNode(1)
                    node.setAttribute('svg:x1', '%fcm' % (left + labels_width + (h-affichage_min) * step))
                    # node.setAttribute('svg:y1', '2cm')
                    node.setAttribute('svg:x2', '%fcm' % (left + labels_width + (h-affichage_min) * step))
                    # node.setAttribute('svg:y2', '29cm')
                    page.appendChild(node)
                    h += creche.granularite / BASE_GRANULARITY

                if "ligne-cahier" in shapes:
                    ligne_cahier = shapes["ligne-cahier"].cloneNode(1)
                    ligne_cahier.setAttribute('svg:x1', '%fcm' % left)
                    ligne_cahier.setAttribute('svg:x2', '%fcm' % (21.0 - right))
                else:
                    ligne_cahier = None

                ajoute_ligne_cahier = False

                # les enfants et salaries
                for i in range(lines_count):
                    line_idx = i + lines_max * page_index
                    line = lines[line_idx]
                    if isinstance(line, basestring):
                        AddCategoryShape(page, line, 0.20 + top + line_height * i)
                        ajoute_ligne_cahier = False
                    else:
                        if ajoute_ligne_cahier and ligne_cahier and creche.tri_planning & TRI_LIGNES_CAHIER:
                            node = ligne_cahier.cloneNode(1)
                            node.setAttribute('svg:y1', '%fcm' % (top + line_height * i))
                            node.setAttribute('svg:y2', '%fcm' % (top + line_height * i))
                            page.appendChild(node)
                        else:
                            ajoute_ligne_cahier = True
                        node = shapes["libelle"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % left)
                        node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                        node.setAttribute('svg:width', '%fcm' % labels_width)
                        fields = [('nom', line.nom),
                                  ('prenom', line.prenom),
                                  ('label', line.label)]
                        ReplaceTextFields(node, fields)
                        page.appendChild(node)
                        for a, b, v in line.activites:
                            if v >= 0:
                                v &= ~PREVISIONNEL
                                key = "activite-%d" % v
                                if key in shapes:
                                    # print a,b,v
                                    node = shapes[key].cloneNode(1)
                                    node.setAttribute('svg:x', '%fcm' % (left + labels_width + float(a - affichage_min) * step))
                                    node.setAttribute('svg:y', '%fcm' % (0.10 + top + line_height * i))
                                    node.setAttribute('svg:width', '%fcm' % ((b - a) * step))
                                    if isinstance(line.inscription, Inscription):
                                        allergies = ', '.join(line.inscription.inscrit.GetAllergies())
                                    else:
                                        allergies = ''                                    
                                    ReplaceTextFields(node, [('texte', ''), ('allergies', allergies)])
                                    page.appendChild(node)
                                else:
                                    print "Pas de forme pour %s" % key
                            
                if page_index + 1 == pages_count:
                    AddCategoryShape(page, "Totaux", 0.20 + top + line_height * lines_count)
                    
                    # le récapitulatif par activité
                    i = lines_count
                    summary = GetActivitiesSummary(creche, lines)[0]
                    for activity in summary.keys():
                        i += 1
                        if activity == PRESENCE_SALARIE:
                            label = "Présences salariés"
                        elif activity == 0:
                            label = "Présences"
                        else:
                            label = creche.activites[activity].label
                        node = shapes["libelle"].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % left)
                        node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                        node.setAttribute('svg:width', '%fcm' % labels_width)
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
                                nv, nw = line[x]
                                
                            if activity == 0 and (nw == 0 or nv > creche.GetCapacite(day.weekday()) or float(nv)/nw > 6.5):
                                nw = activity | SUPPLEMENT
                            else:
                                nw = activity
                                
                            if nv != v or nw != w:
                                if v != 0:
                                    # print a, x, v
                                    key = "activite-%d" % w
                                    if key in shapes:
                                        node = shapes[key].cloneNode(1)
                                    else:
                                        key = "activite-%d" % (w & ~SUPPLEMENT)
                                        if key in shapes:
                                            node = shapes[key].cloneNode(1)
                                        else:
                                            print "Pas de forme pour %s" % key
                                            node = None
                                    if node:
                                        node.setAttribute('svg:x', '%fcm' % (left + labels_width + (float(a - affichage_min) * step)))
                                        node.setAttribute('svg:y', '%fcm' % (0.10 + top + line_height * i))
                                        node.setAttribute('svg:width', '%fcm' % (float(x - a) * step))
                                        ReplaceTextFields(node, [('texte', '%d' % v)])
                                        page.appendChild(node)
                                a = x    
                                v, w = nv, nw
                            x += creche.granularite / BASE_GRANULARITY
    
                fields = GetCrecheFields(creche) + GetSiteFields(self.site)
                if pages_count > 1:
                    fields.append(('date', GetDateString(day) + " (%d/%d)" % (page_index + 1, pages_count)))
                else:
                    fields.append(('date', GetDateString(day)))

                ReplaceTextFields(page, fields)
            day += datetime.timedelta(1)
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
            
        inscriptions = GetInscriptions(debut, fin)
        for index, inscription in enumerate(inscriptions):
            inscrit = inscription.inscrit
            row = template.cloneNode(1)
            # print row.toprettyxml()
            date = debut
            cell = 0
            weekday = date.weekday()
            if weekday == 6:
                date += datetime.timedelta(1)
            elif weekday == 5:
                date += datetime.timedelta(2)
            elif weekday > 0:
                cell = weekday * 2 + 1
            tranches = [(creche.ouverture, 12), (14, creche.fermeture)]
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
            if date in creche.jours_fermeture:
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
            inscrits = GetLines(date, creche.inscrits, site=self.site, groupe=self.groupe)
            linesCount = 0
            for i, inscrit in enumerate(inscrits):
                if inscrit is not None and not isinstance(inscrit, basestring):
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
            if date in creche.jours_fermeture:
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

            for groupe in creche.groupes:
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
                inscrits = GetLines(date, creche.inscrits, site=self.site, groupe=groupe)
                linesCount = 0
                for i, inscrit in enumerate(inscrits):
                    if inscrit is not None and not isinstance(inscrit, basestring):
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
