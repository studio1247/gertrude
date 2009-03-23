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
from cotisation import Cotisation, CotisationException
from ooffice import *

left = 1.5
right = 2.0
top = 6.0
labels_width = 3.5
line_height = 0.75
    
class PlanningDetailleModifications(object):
    def __init__(self, periode):
        self.periode = periode
        self.errors = {}

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            # ReplaceTextFields(dom, fields)
            return []
        
        step = (21.0-left-right-labels_width) / (creche.affichage_max - creche.affichage_min)
        
        drawing = dom.getElementsByTagName('office:drawing').item(0)
        template = drawing.getElementsByTagName("draw:page").item(0)
        # print template.toprettyxml()
        shapes = getNamedShapes(template)
        # print shapes
        for shape in shapes:
            template.removeChild(shapes[shape])
        drawing.removeChild(template)     
    
        day, end = self.periode
        while day <= end:
            if day in creche.jours_fermeture:
                day += datetime.timedelta(1)
                continue
            page = template.cloneNode(1)
            page.setAttribute("draw:name", getDateStr(day))
            drawing.appendChild(page)
            
            # le quadrillage et l'echelle
            h = creche.affichage_min
            while h <= creche.affichage_max:
                if h == int(h):
                    node = shapes["legende-heure"].cloneNode(1)
                    node.setAttribute('svg:x', '%fcm' % (left + labels_width - 0.5 + (float(h)-creche.affichage_min) * step))
                    # node.setAttribute('svg:y', '1cm')
                    node.setAttribute('svg:width', '1cm')
                    node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % h)
                    page.appendChild(node)
                    node = shapes["ligne-heure"].cloneNode(1)
                else:
                    node = shapes["ligne-quart-heure"].cloneNode(1)
                node.setAttribute('svg:x1', '%fcm' % (left + labels_width + (h-creche.affichage_min) * step))
                # node.setAttribute('svg:y1', '2cm')
                node.setAttribute('svg:x2', '%fcm' % (left + labels_width + (h-creche.affichage_min) * step))
                # node.setAttribute('svg:y2', '29cm')
                page.appendChild(node)
                h += 0.25
            
            # les enfants
            lines = getLines(day, creche.inscrits)
            for i, line in enumerate(lines):
                node = shapes["libelle"].cloneNode(1)
                node.setAttribute('svg:x', '%fcm' % left)
                node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                node.setAttribute('svg:width', '%fcm' % labels_width)
                fields = [('nom', line.nom),
                          ('prenom', line.prenom),
                          ('label', line.label)]
                ReplaceTextFields(node, fields)
                page.appendChild(node)
                for a, b, v in line.get_activities():
                    if v >= 0:
                        a = float(a) / 4
                        b = float(b) / 4
                        v = v & (~PREVISIONNEL)
                        # print a,b,v
                        node = shapes["activite-%d" % v].cloneNode(1)
                        node.setAttribute('svg:x', '%fcm' % (left + labels_width + (float(a)-creche.affichage_min) * step))
                        node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                        node.setAttribute('svg:width', '%fcm' % ((b-a)*step))
                        ReplaceTextFields(node, [('texte', '')])
                        page.appendChild(node)
                        
            # ligne séparatrice
            i = len(lines)
            if "separateur" in shapes:
                node = shapes["separateur"].cloneNode(1)
                node.setAttribute('svg:x1', '%fcm' % left)
                node.setAttribute('svg:y1', '%fcm' % (0.25 + top + line_height * i))
                node.setAttribute('svg:x2', '%fcm' % (21.0-right))
                node.setAttribute('svg:y2', '%fcm' % (0.25 + top + line_height * i))
                page.appendChild(node)
            
            # le récapitulatif par activité
            summary = getActivitiesSummary(creche, lines)
            debut = int(creche.affichage_min*4)
            fin = int(creche.affichage_max*4)
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
                x = debut
                v = 0
                a = 0
                while x <= fin:
                    if x == fin:
                        nv = 0
                    else:
                        nv = line[x]
                    if nv != v:
                        if v != 0:
                            # print a, x, v
                            node = shapes["activite-%d" % activity].cloneNode(1)
                            node.setAttribute('svg:x', '%fcm' % (left + labels_width + (float(a)/4-creche.affichage_min) * step))
                            node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                            node.setAttribute('svg:width', '%fcm' % (float(x-a)*step/4))
                            ReplaceTextFields(node, [('texte', '%d' % v)])
                            page.appendChild(node)
                        a = x    
                        v = nv
                    x += 1

            fields = [('nom-creche', creche.nom),
                      ('date', getDateStr(day))]
            ReplaceTextFields(page, fields)
            day += datetime.timedelta(1)
            
        return []


def GenerePlanningDetaille(periode, oofilename):
    return GenerateDocument('Planning detaille.odg', oofilename, PlanningDetailleModifications(periode))

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    #GenereCoordonneesParents("coordonnees.odt")
    #sys.exit(0)    
    filename = 'planning-details-1.odg'
    try:
        GenerePlanningDetaille((datetime.date(2009, 2, 16), datetime.date(2009, 2, 20)), filename)
        print u'Fichier %s généré' % filename
    except CotisationException, e:
        print e.errors

