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

couleurs = { PRESENT+SUPPLEMENT: 'A2',
             MALADE: 'B2',
             PRESENT: 'C2',
             VACANCES: 'D2',
             ABSENT: 'E2'}

class FactureModifications(object):
    def __init__(self, who, periode):
        self.template = 'Facture mensuelle.odt'
        self.periode = periode
        if isinstance(who, list):
            self.default_output = u"Factures %s %d.odt" % (months[periode.month - 1], periode.year)
            self.inscrits = [inscrit for inscrit in who if inscrit.getInscription(periode) is not None]
        else:
            self.default_output = u"Facture %s %s %s %d.odt" % (who.prenom, who.nom, months[periode.month - 1], periode.year)
            self.inscrits = [who]

    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None

        errors = {}
        
        #print dom.toprettyxml()
        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.childNodes[:]
        
        for index, inscrit in enumerate(self.inscrits):
            try:
                facture = Facture(inscrit, self.periode.year, self.periode.month)
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue

            debut, fin = getMonthStart(self.periode), getMonthEnd(self.periode)
            inscriptions = inscrit.getInscriptions(debut, fin)
            
            for template in templates:
                section = template.cloneNode(1)
                if section.nodeName in ("draw:frame", "draw:custom-shape"):
                    doc.insertBefore(section, template)
                else:
                    doc.appendChild(section)
                if section.hasAttribute("text:anchor-page-number"):
                    section.setAttribute("text:anchor-page-number", str(index+1))
            
                # D'abord le tableau des presences du mois
                empty_cells = debut.weekday()
                if empty_cells > 4:
                    empty_cells -= 7
        
                # Création d'un tableau de cells
                for table in section.getElementsByTagName('table:table'):
                    if table.getAttribute('table:name') == 'Presences':
                        rows = table.getElementsByTagName('table:table-row')[1:]
                        cells = []
                        for i in range(len(rows)):
                            cells.append(rows[i].getElementsByTagName('table:table-cell'))
                            for cell in cells[i]:
                                cell.setAttribute('table:style-name', 'Tableau1.E2')
                                text_node = cell.getElementsByTagName('text:p')[0]
                                text_node.firstChild.replaceWholeText(' ')
        
                        date = debut
                        while date.month == debut.month:
                            col = date.weekday()
                            if col < 5:
                                row = (date.day + empty_cells) / 7
                                cell = cells[row][col]
                                # ecriture de la date dans la cellule
                                text_node = cell.getElementsByTagName('text:p')[0]
                                text_node.firstChild.replaceWholeText('%d' % date.day)
                                if not date in creche.jours_fermeture:
                                    # changement de la couleur de la cellule
                                    state = inscrit.getState(date)[0]
                                    if state > 0:
                                        state = state % PREVISIONNEL
                                    cell.setAttribute('table:style-name', 'Presences.%s' % couleurs[state])
                            date += datetime.timedelta(1)
        
                        for i in range(row + 1, len(rows)):
                            table.removeChild(rows[i])
    
                # Les champs de la facture
                fields = [('nom-creche', creche.nom),
                        ('adresse-creche', creche.adresse),
                        ('code-postal-creche', str(creche.code_postal)),
                        ('ville-creche', creche.ville),
                        ('telephone-creche', creche.telephone),
                        ('email-creche', creche.email),
                        ('adresse', inscrit.adresse),
                        ('code-postal', str(inscrit.code_postal)),
                        ('ville', inscrit.ville),
                        ('mois', '%s %d' % (months[debut.month - 1], debut.year)),
                        ('de-mois', '%s %d' % (getDeMoisStr(debut.month - 1), debut.year)),
                        ('prenom', inscrit.prenom),
                        ('parents', getParentsStr(inscrit)),
                        ('date', '%.2d/%.2d/%d' % (debut.day, debut.month, debut.year)),
                        ('numfact', '%.2d%.4d%.2d%.4d' % (inscriptions[0].mode + 1, debut.year, debut.month, inscriptions[0].idx)),
                        ('cotisation-mensuelle', '%.2f' % facture.cotisation_mensuelle),
                        ('tarif-horaire', '%.2f' % facture.tarif_horaire),
                        ('heures-contrat', '%.2f' % facture.heures_contrat),
                        ('heures-supplementaires', '%.2f' % facture.heures_supplementaires),
                        ('supplement', '%.2f' % facture.supplement),
                        ('deduction', '- %.2f' % facture.deduction),
                        ('raison-deduction', facture.raison_deduction),
                        ('supplement-activites', '%.2f' % facture.supplement_activites),
                        ('total', '%.2f' % facture.total)
                        ]
        
                ReplaceTextFields(section, fields)

        for template in templates:
            doc.removeChild(template)
        
        #print doc.toprettyxml() 
        return errors
