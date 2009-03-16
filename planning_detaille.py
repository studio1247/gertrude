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
        line1_template = template.getElementsByTagName("draw:line").item(0)
        line2_template = template.getElementsByTagName("draw:line").item(1)
        frame_template = template.getElementsByTagName("draw:frame").item(0)
        shape_templates = template.getElementsByTagName("draw:custom-shape")
        label_template = template.getElementsByTagName("draw:frame").item(1)
        template.removeChild(line1_template)
        template.removeChild(line2_template)
        template.removeChild(frame_template)
        template.removeChild(label_template)
        for t in shape_templates:
            template.removeChild(t)
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
                    node = frame_template.cloneNode(1)
                    node.setAttribute('svg:x', '%fcm' % (left + labels_width - 0.5 + (float(h)-creche.affichage_min) * step))
                    # node.setAttribute('svg:y', '1cm')
                    node.setAttribute('svg:width', '1cm')
                    node.firstChild.firstChild.firstChild.firstChild.replaceWholeText('%dh' % h)
                    page.appendChild(node)
                    node = line1_template.cloneNode(1)
                else:
                    node = line2_template.cloneNode(1)
                node.setAttribute('svg:x1', '%fcm' % (left + labels_width + (h-creche.affichage_min) * step))
                # node.setAttribute('svg:y1', '2cm')
                node.setAttribute('svg:x2', '%fcm' % (left + labels_width + (h-creche.affichage_min) * step))
                # node.setAttribute('svg:y2', '29cm')
                page.appendChild(node)
                h += 0.25
            
            # les enfants
            lines = getLines(day, creche.inscrits)
            for i, line in enumerate(lines):
                node = label_template.cloneNode(1)
                node.setAttribute('svg:x', '%fcm' % left)
                node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                node.setAttribute('svg:width', '%fcm' % labels_width)
                fields = [('nom', line.nom),
                          ('prenom', line.prenom),
                          ('label', line.label)]
                ReplaceTextFields(node, fields)
                page.appendChild(node)
                for a, b, v in line.get_activities():
                    a = float(a) / 4
                    b = float(b) / 4
                    # print a,b,v
                    node = shape_templates[v].cloneNode(1)
                    node.setAttribute('svg:x', '%fcm' % (left + labels_width + (float(a)-creche.affichage_min) * step))
                    node.setAttribute('svg:y', '%fcm' % (top + line_height * i))
                    node.setAttribute('svg:width', '%fcm' % ((b-a)*step))
                    page.appendChild(node)
            
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

