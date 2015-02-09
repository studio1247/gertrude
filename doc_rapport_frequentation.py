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

template_total_lines_count = 19
template_first_line = 4
template_lines_count = 8

class RapportFrequentationModifications(object):
    def __init__(self, site, annee):
        self.multi = False
        self.template = 'Rapport frequentation.ods'
        self.default_output = "Rapport frequentation %d.ods" % annee
        self.annee = annee
        self.factures = {}
        self.errors = {}
        self.email = None
        self.site = site
        self.metas = { "colonne-jour": 2,
                       "colonne-mois": -1,
                       "colonne-annee": 4,
                       "colonne-jours-ouverture": 6,
                       "ligne-taux-occupation": 5,
                       "colonne-total-jours-ouverture": 7,
                       "ligne-total-heures-presence": 3,
                       "ligne-total-jours-ouverture": -1,
                       "ligne-recap-jours-ouverture": -1,
                       "colonne-annee-heures-facturees": -1 }
    
    def execute(self, filename, dom):
        fields = GetCrecheFields(creche)
                      
        if filename == 'styles.xml':
            ReplaceTextFields(dom, fields)
            return []
        
        elif filename == 'meta.xml':
            metas = dom.getElementsByTagName('meta:user-defined')
            for meta in metas:
                # print meta.toprettyxml()
                name = meta.getAttribute('meta:name')
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = int(value)
                else:
                    self.metas[name] = value
            return None        

        elif filename == 'content.xml':
            if "Format" in self.metas and self.metas["Format"] == 1:
                ReplaceFields(dom, fields)
                spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
                feuille = spreadsheet.getElementsByTagName("table:table").item(0)
                lines = feuille.getElementsByTagName("table:table-row")
                template = lines[0:13]
                for line in template:
                    feuille.removeChild(line)
                after = lines[13]
                for mois in range(1, 13):
                    debut = datetime.date(self.annee, mois, 1)
                    fin = GetMonthEnd(debut)
                    if fin > today:
                        break

                    heures_accueil = GetHeuresAccueil(self.annee, mois, self.site)
                    heures_realisees = {}
                    heures_facturees = {}
                    for categorie in creche.categories:
                        nom = categorie.nom.lower()
                        heures_realisees[nom] = 0.0
                        heures_facturees[nom] = 0.0
                    total_heures_realisees = 0.0
                    total_heures_facturees = 0.0
                    inscrits = GetInscrits(debut, fin, self.site)
                    for inscrit in inscrits:
                        inscriptions = inscrit.GetInscriptions(debut, fin)
                        if inscriptions and (self.site is None or inscriptions[0].site == self.site):
                            try:
                                facture = Facture(inscrit, self.annee, mois)
                                facture_heures_realisees = facture.heures_realisees
                                if config.options & HEURES_CONTRAT:
                                    facture_heures_facturees = facture.heures_facture
                                else:
                                    facture_heures_facturees = facture.heures_facturees
                                if inscrit.categorie:
                                    nom = inscrit.categorie.nom.lower()
                                    heures_realisees[nom] += facture_heures_realisees 
                                    heures_facturees[nom] += facture_heures_facturees 
                                total_heures_realisees += facture_heures_realisees
                                total_heures_facturees += facture_heures_facturees
                            except CotisationException, e:
                                self.errors[GetPrenomNom(inscrit)] = e.errors

                    taux_remplissage = 0.0
                    if heures_accueil:
                        taux_remplissage = (100.0 * total_heures_facturees) / heures_accueil
                    
                    fields = [('mois', months[mois-1]),
                              ('annee', self.annee),
                              ('heures-realisees', total_heures_realisees),
                              ('heures-facturees', total_heures_facturees),
                              ('taux-remplissage', taux_remplissage)
                              ]
                    
                    fields += [('heures-realisees-%s' % tmp, heures_realisees[tmp]) for tmp in heures_realisees]
                    fields += [('heures-facturees-%s' % tmp, heures_realisees[tmp]) for tmp in heures_facturees]
                    
                    #print fields
                    
                    for line in template:
                        clone = line.cloneNode(1)   
                        ReplaceFields(clone, fields)
                        feuille.insertBefore(clone, after)
                    
            else:
                ReplaceFields(dom, fields)
                spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
                tables = spreadsheet.getElementsByTagName("table:table")
                
                inscrits_annee = {}
                inscrits_annee_details = {}
                jours_mois = []
                total_heures_facturees = {}
    
                # les 12 mois
                colonne_jour = self.metas['colonne-jour']
                template = tables.item(0)
                for mois in range(1, 13):
                    debut = datetime.date(self.annee, mois, 1)
                    fin = GetMonthEnd(debut)
                    if fin > today:
                        break
        
                    inscrits = GetInscrits(debut, fin, self.site)
                    inscrits.sort(lambda x, y: cmp(x.nom.lower(), y.nom.lower()))
                    if not inscrits:
                        continue
                    
                    jours = [jour for jour in range(debut.day, fin.day+1) if datetime.date(debut.year, debut.month, jour) not in creche.jours_fermeture]
                    
                    table = template.cloneNode(1)
                    spreadsheet.insertBefore(table, template)
                    table.setAttribute("table:name", months[mois-1])
                    columns = table.getElementsByTagName("table:table-column")
                    column_template = columns[colonne_jour]
                    lines = table.getElementsByTagName("table:table-row")
                    first_line = lines[0]
                    ReplaceTextFields(first_line, [('mois', months[mois-1])])
                    line_template = lines[1]
                    sum_line = lines[2]
                    cell_template = line_template.getElementsByTagName("table:table-cell")[colonne_jour]
                    first_line_cell_template = first_line.getElementsByTagName("table:table-cell")[colonne_jour]
                    sum_line_cell_template = sum_line.getElementsByTagName("table:table-cell")[1]
                    for jour in jours:
                        column = column_template.cloneNode(1)
                        table.insertBefore(column, column_template)
                        cell = first_line_cell_template.cloneNode(1)
                        first_line.insertBefore(cell, first_line_cell_template)
                        ReplaceFields(cell, [('jour', jour)])
                        cell = cell_template.cloneNode(1)
                        line_template.insertBefore(cell, cell_template)
                        cell = sum_line_cell_template.cloneNode(1)
                        sum_line.insertBefore(cell, sum_line_cell_template)
                    table.removeChild(column_template)
                    first_line.removeChild(first_line_cell_template)
                    line_template.removeChild(cell_template)
                    sum_line.removeChild(sum_line_cell_template)
                    
                    for i, inscrit in enumerate(inscrits):
                        line = line_template.cloneNode(1)
                        table.insertBefore(line, line_template)
                        ReplaceFields(line, GetInscritFields(inscrit))
                        cells = line.getElementsByTagName("table:table-cell")
                        for j, jour in enumerate(jours):
                            date = datetime.date(debut.year, debut.month, jour)
                            state = inscrit.GetState(date)
                            if inscrit in total_heures_facturees:
                                total_heures_facturees[inscrit] += state.heures_facturees
                            else:
                                total_heures_facturees[inscrit] = state.heures_facturees
                            if not state.heures_facturees:
                                state.heures_facturees = ""
                            if not state.heures_realisees:
                                state.heures_realisees = ""
                            ReplaceFields(cells[colonne_jour+j], [('heures-realisees', state.heures_realisees),
                                                                  ('heures-facturees', state.heures_facturees)])
                        total_cell = cells[len(jours)+colonne_jour]
                        total_cell.setAttribute("table:formula", "of:=SUM([.%s%d:.%s%d])" % (GetColumnName(colonne_jour), i+2, GetColumnName(colonne_jour-1+len(jours)), i+2))
                        if i == 0:
                            IncrementFormulas(cells[len(jours)+colonne_jour+2:], column=len(jours)-1)
                            cells[len(jours)+self.metas['colonne-jours-ouverture']-1].setAttribute("table:formula", "of:=COUNT([.%s1:.%s1])" % (GetColumnName(colonne_jour), GetColumnName(colonne_jour-1+len(jours))))
                            jours_mois.append("%s.%s2" % (months[mois-1], GetColumnName(self.metas['colonne-jours-ouverture']-1+len(jours))))
                            for cell in line_template.getElementsByTagName("table:table-cell")[len(jours)+3:]:
                                line_template.removeChild(cell)
                        key = GetPrenomNom(inscrit)
                        if key not in inscrits_annee:
                            inscrits_annee[key] = inscrit
                            inscrits_annee_details[key] = {}
                        inscrits_annee_details[key][mois] = "%s.%s%d" % (months[mois-1], GetColumnName(colonne_jour+len(jours)), i+2)
                    table.removeChild(line_template)
                    last_line = 1 + len(inscrits)
                    for i, cell in enumerate(sum_line.getElementsByTagName("table:table-cell")[1:2+len(jours)]):
                        column = GetColumnName(colonne_jour+i)
                        cell.setAttribute("table:formula", "of:=SUM([.%s2:.%s%d])" % (column, column, last_line))
                    
                spreadsheet.removeChild(template)
                
                # La recap de l'annee
                colonne_mois = self.metas['colonne-mois']
                colonne_annee = self.metas['colonne-annee']
                table = tables[-1]
                lines = table.getElementsByTagName("table:table-row")
                
                if colonne_mois >= 0:
                    line = lines[0]
                    cells = line.getElementsByTagName("table:table-cell")
                    cell_template = cells[colonne_mois]
                    for m in range(12):
                        cell = cell_template.cloneNode(1)
                        ReplaceFields([cell], [('mois', months[m])])
                        line.insertBefore(cell, cell_template)
                    line.removeChild(cell_template)
                        
                template = lines[1]
                keys = inscrits_annee.keys()
                keys.sort()
                for i, key in enumerate(keys):
                    inscrit = inscrits_annee[key] 
                    line = template.cloneNode(1)
                    table.insertBefore(line, template)
                    ReplaceFields(line, GetInscritFields(inscrit) + [("total-heures-facturees", total_heures_facturees[inscrit])])
                    cells = line.getElementsByTagName("table:table-cell")
                    cells[colonne_annee].setAttribute("table:formula", "of:=SUM(%s)" % ';'.join(["[%s]" % c for c in inscrits_annee_details[key].values()]))
                    if i == 0 and self.metas['colonne-total-jours-ouverture'] >= 0:
                        cells[self.metas['colonne-total-jours-ouverture']].setAttribute("table:formula", "of:=SUM(%s)" % ';'.join(["[%s]" % m for m in jours_mois]))
                        for cell in template.getElementsByTagName("table:table-cell")[colonne_annee+1:]:
                            template.removeChild(cell)
                    if colonne_mois >= 0:
                        cell_template = cells[colonne_mois]
                        for m in range(1, 13):
                            cell = cell_template.cloneNode(1)
                            if m in inscrits_annee_details[key]:
                                cell.setAttribute("table:formula", "of:=%s" % inscrits_annee_details[key][m])
                            else:
                                cell.setAttribute("table:formula", "of:=0")
                            line.insertBefore(cell, cell_template)
                        line.removeChild(cell_template)
                    
                table.removeChild(template)
                
                ligne_recap = self.metas["ligne-recap-jours-ouverture"]
                if ligne_recap >= 0:
                    line = lines[ligne_recap] 
                    cells = line.getElementsByTagName("table:table-cell")
                    cell_template = cells[colonne_mois]
                    for m in jours_mois:
                        cell = cell_template.cloneNode(1)
                        cell.setAttribute("table:formula", "of:=%s" % m)
                        line.insertBefore(cell, cell_template)
                    line.removeChild(cell_template)
                
                total_cell = lines[self.metas['ligne-total-heures-presence']].getElementsByTagName("table:table-cell")[2]
                if colonne_mois >= 0:
                    colname = GetColumnName(colonne_annee+11)
                else:
                    colname = 'E'
                total_cell.setAttribute("table:formula", "of:=SUM([.%s2:.%s%d])" % (colname, colname, 1+len(keys)))
                
                if self.metas["ligne-total-jours-ouverture"] >= 0:
                    total_cell = lines[self.metas['ligne-total-jours-ouverture']].getElementsByTagName("table:table-cell")[2]
                    total_cell.setAttribute("table:formula", "of:=SUM(%s)" % ';'.join(["[%s]" % m for m in jours_mois]))
                
                ligne_taux_occuptation = self.metas['ligne-taux-occupation']
                if ligne_taux_occuptation >= 0:
                    taux_occupation_cell = lines[ligne_taux_occuptation].getElementsByTagName("table:table-cell")[2]
                    taux_occupation_cell.setAttribute("table:formula", "of:=E%d/G2" % (3+len(keys)))
                    demi_journees_reelles_cell = lines[6].getElementsByTagName("table:table-cell")[2]
                    demi_journees_reelles_cell.setAttribute("table:formula", "of:=J2*I2*C%d" % (6+len(keys)))
               
        return self.errors
