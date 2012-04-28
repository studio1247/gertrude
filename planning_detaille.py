# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from constants import *
from functions import *
from facture import *
from cotisation import CotisationException
from ooffice import *

left = 1.5
right = 2.0
top = 6.0
labels_width = 3.5
line_height = 0.75
lines_max = 25
    
class PlanningDetailleModifications(object):
    def __init__(self, site, periode):
        self.multi = False
        self.site = site
        self.start, self.end = periode
        if IsTemplateFile("Planning detaille.ods"):
            self.template = 'Planning detaille.ods'
            self.default_output = "Planning detaille %s %d.ods" % (months[self.start.month-1], self.start.year)
        else:
            self.template = 'Planning detaille.odg'
            if self.start == self.end:
                self.default_output = "Planning presences %s.odg" % GetDateString(self.start, weekday=False)
            else:
                self.default_output = "Planning presences %s-%s.odg" % (GetDateString(self.start, weekday=False), GetDateString(self.end, weekday=False))
        self.errors = {}
        self.email = None
        self.site = None

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        if IsTemplateFile("Planning detaille.ods"):
            return self.ExecuteTemplateDetaille(filename, dom)
        else:
            affichage_min = int(creche.affichage_min * 60 / BASE_GRANULARITY)
            affichage_max = int(creche.affichage_max * 60 / BASE_GRANULARITY)
            step = (21.0-left-right-labels_width) / (affichage_max - affichage_min)
            
            drawing = dom.getElementsByTagName('office:drawing').item(0)
            template = drawing.getElementsByTagName("draw:page").item(0)
            # print template.toprettyxml()
            shapes = getNamedShapes(template)
            # print shapes
            for shape in shapes.keys():
                if shape in ["legende-heure", "ligne-heure", "ligne-quart-heure", "libelle", "separateur"] or shape.startswith("activite-"):
                    template.removeChild(shapes[shape])
            drawing.removeChild(template)
        
            day = self.start
            while day <= self.end:
                if day in creche.jours_fermeture:
                    day += datetime.timedelta(1)
                    continue
                
                lines = GetLines(self.site, day, creche.inscrits)
                pages_count = 1 + (len(lines) - 1) / lines_max
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
                    
                    # les enfants
                    for i in range(lines_count):
                        line = lines[i+lines_max*page_index]
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
                                v = v & (~PREVISIONNEL)
                                # print a,b,v
                                node = shapes["activite-%d" % v].cloneNode(1)
                                node.setAttribute('svg:x', '%fcm' % (left + labels_width + float(a-affichage_min) * step))
                                node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                                node.setAttribute('svg:width', '%fcm' % ((b-a)*step))
                                ReplaceTextFields(node, [('texte', '')])
                                page.appendChild(node)
                                
                    if page_index+1 == pages_count:
                        # ligne séparatrice
                        if "separateur" in shapes:
                            node = shapes["separateur"].cloneNode(1)
                            node.setAttribute('svg:x1', '%fcm' % left)
                            node.setAttribute('svg:y1', '%fcm' % (0.25 + top + line_height * lines_count))
                            node.setAttribute('svg:x2', '%fcm' % (21.0-right))
                            node.setAttribute('svg:y2', '%fcm' % (0.25 + top + line_height * lines_count))
                            page.appendChild(node)
                        
                        # le récapitulatif par activité
                        i = lines_count
                        summary = GetActivitiesSummary(creche, lines)[0]
                        for activity in summary.keys():
                            i += 1
                            if activity == 0:
                                label = u"Présences"
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
                            v = 0
                            a = 0
                            while x <= affichage_max:
                                if x == affichage_max:
                                    nv = 0
                                else:
                                    nv = line[x]
                                if nv != v:
                                    if v != 0:
                                        # print a, x, v
                                        node = shapes["activite-%d" % activity].cloneNode(1)
                                        node.setAttribute('svg:x', '%fcm' % (left + labels_width + (float(a-affichage_min) * step)))
                                        node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                                        node.setAttribute('svg:width', '%fcm' % (float(x-a)*step))
                                        ReplaceTextFields(node, [('texte', '%d' % v)])
                                        page.appendChild(node)
                                    a = x    
                                    v = nv
                                x += creche.granularite / BASE_GRANULARITY
        
                    fields = [('nom-creche', creche.nom)]
                    if pages_count > 1:
                        fields.append(('date', GetDateString(day) + " (%d/%d)" % (page_index+1, pages_count)))
                    else:
                        fields.append(('date', GetDateString(day)))
    
                    ReplaceTextFields(page, fields)
                day += datetime.timedelta(1)
            
        return None
    
    def ExecuteTemplateDetaille(self, filename, dom):
        # Garderie Ribambelle, planning detaille

        debut, fin = getMonthStart(self.start), getMonthEnd(self.start)
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
                    journee = inscrit.getReferenceDayCopy(date)
                for t in range(2):
                    if journee and IsPresentDuringTranche(journee, tranches[t][0]*12, tranches[t][1]*12):
                        heures = HeuresTranche(journee, tranches[t][0]*12, tranches[t][1]*12)
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
                    formule = formule.replace('9', '%d' % (7+len(inscriptions)))
                    formule = formule.replace('8', '%d' % (6+len(inscriptions)))
                    cellule.setAttribute('table:formula', formule)
                    
        return None    

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    filename = 'planning-details-1.ods'
    try:
        GenerateOODocument(PlanningDetailleModifications((datetime.date(2011, 9, 16), datetime.date(2009, 2, 20))), filename)
        print u'Fichier %s généré' % filename
    except CotisationException, e:
        print e.errors

