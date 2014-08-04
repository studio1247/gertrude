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

PRESENCE_NON_FACTUREE = 256
CONGES = 257

couleurs = { SUPPLEMENT: 'A2',
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
    def __init__(self, inscrits, periode):
        self.template = 'Facture mensuelle.odt'
        self.multi = False
        self.inscrits = inscrits
        self.periode = periode
        self.periode_facturation = periode
        if creche.temps_facturation != FACTURATION_FIN_MOIS:
            self.periode_facturation = getMonthStart(periode - datetime.timedelta(1))
            
        self.email = True
        if len(inscrits) > 1:
            self.site = inscrits[0].GetInscriptions(self.periode_facturation, None)[0].site
            self.email_subject = u"Factures %s %d" % (months[periode.month - 1], periode.year)
            self.default_output = u"Factures %s %d.odt" % (months[periode.month - 1], periode.year)
            self.email_to = None
        else:
            who = inscrits[0]
            self.site = who.GetInscriptions(self.periode_facturation, None)[0].site
            self.email_subject = u"Facture %s %s %s %d" % (who.prenom, who.nom, months[periode.month - 1], periode.year)
            self.email_to = list(set([parent.email for parent in who.parents.values() if parent and parent.email]))
            self.default_output = self.email_subject + ".odt"

        if IsTemplateFile("Facture mensuelle simple.odt"):
            self.template = "Facture mensuelle simple.odt"
            if len(inscrits) > 1:
                self.multi = True
                self.default_output = u"Facture <prenom> <nom> %s %d.odt" % (months[periode.month - 1], periode.year)
        
        self.email_text = "Accompagnement facture.txt"

    def GetSimpleModifications(self, filename):
        return [(filename.replace("<prenom>", inscrit.prenom).replace("<nom>", inscrit.nom), FactureModifications([inscrit], self.periode)) for inscrit in self.inscrits]
    
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None

        errors = {}
        
        # print dom.toprettyxml()
        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.childNodes[:]
        
        styleC3, styleD3 = False, False
        for style in doc.getElementsByTagName('style:style'):
            if style.name == 'Presences.C3':
                styleC3 = True
            elif style.name == 'Presences.D3':
                styleD3 = True

        #if not styleC3:
        #    couleurs[CONGES] = 'B3'
        if not styleD3:
            couleurs[CONGES_DEPASSEMENT] = 'B3'
        
        for index, inscrit in enumerate(self.inscrits):
            try:
                facture = Facture(inscrit, self.periode.year, self.periode.month, options=TRACES)
            except CotisationException, e:
                errors["%s %s" % (inscrit.prenom, inscrit.nom)] = e.errors
                continue
           
            for template in templates:
                section = template.cloneNode(1)
                if section.nodeName in ("draw:frame", "draw:custom-shape"):
                    doc.insertBefore(section, template)
                else:
                    doc.appendChild(section)
                if section.hasAttribute("text:anchor-page-number"):
                    section.setAttribute("text:anchor-page-number", str(index+1))
            
                # D'abord le tableau des presences du mois
                empty_cells = facture.debut_recap.weekday()
                if "Week-end" in creche.feries and empty_cells > 4:
                    empty_cells -= 7
        
                # Création d'un tableau de cells
                for table in section.getElementsByTagName('table:table'):
                    table_name = table.getAttribute('table:name')
                    if table_name == 'Montants':
                        rows = table.getElementsByTagName('table:table-row')
                        if not facture.frais_inscription:
                            for row in rows:
                                if "Frais d'inscription" in row.toprettyxml():
                                    table.removeChild(row)
                                    break
                    elif table_name.startswith('Presences'):
                        rows = table.getElementsByTagName('table:table-row')[1:]
                        cells_count = GetCellsCount(rows[0])
                        cells = []
                        for i in range(len(rows)):
                            cells.append(rows[i].getElementsByTagName('table:table-cell'))
                            for cell in cells[i]:
                                cell.setAttribute('table:style-name', 'Tableau1.E2')
                                text_node = cell.getElementsByTagName('text:p')[0]
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
                                elif date in facture.jours_maladie:
                                    state = MALADE
                                elif inscrit.isDateConge(date):
                                    state = CONGES
                                elif date in facture.jours_conges_non_factures:
                                    state = VACANCES
                                elif date in facture.jours_vacances:
                                    state = CONGES_DEPASSEMENT
                                    print "depassement", date
                                else:
                                    state = ABSENT
                                text_node.firstChild.replaceWholeText('%d%s' % (date.day, details))
                                if date == datetime.date(2014, 7, 28):
                                    print date, state, couleurs[state]
                                cell.setAttribute('table:style-name', 'Presences.%s' % couleurs[state])
                            date += datetime.timedelta(1)
        
                        for i in range(row + 1, len(rows)):
                            table.removeChild(rows[i])

                # Les champs de la facture
                last_inscription = None
                for tmp in inscrit.inscriptions:
                    if not last_inscription or not last_inscription.fin or (tmp.fin and tmp.fin > last_inscription.fin):
                        last_inscription = tmp 
                
                fields = GetCrecheFields(creche) + GetInscritFields(inscrit) + GetInscriptionFields(last_inscription) + GetFactureFields(facture)
                ReplaceTextFields(section, fields)

        for template in templates:
            doc.removeChild(template)
        
        #print doc.toprettyxml() 
        return errors
