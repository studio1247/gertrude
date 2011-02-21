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

class SyntheseFinanciereModifications(object):
    def __init__(self, annee):
        self.template = 'Synthese financiere.ods'
        self.default_output = "Synthese financiere %d.ods" % annee
        self.annee = annee
        self.factures = {}
        self.errors = {}

    def execute(self, filename, dom):
        if filename == 'styles.xml':
            fields = [('nom-creche', creche.nom),
                      ('adresse-creche', creche.adresse),
                      ('code-postal-creche', str(creche.code_postal)),
                      ('ville-creche', creche.ville),
                      ('capacite', creche.capacite),
                     ]
            ReplaceTextFields(dom, fields)
            return []

        elif filename == 'content.xml':
            global_indexes = getTriParCommuneEtNomIndexes(range(len(creche.inscrits)))
    
            spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
            tables = spreadsheet.getElementsByTagName("table:table")
            table = tables.item(0)
            lines = table.getElementsByTagName("table:table-row")
            # line_heures_ouvrees = lines[2]
    
            fields = []
            for mois in range(1, 13):
                jours_ouvres = GetJoursOuvres(self.annee, mois)
                heures_ouvrees = jours_ouvres * (creche.fermeture - creche.ouverture)
                
                heures_facturees = 0.0
                heures_facturees_par_mode = [0.0] * 33
                cotisations_facturees = 0.0
                
                debut = datetime.date(self.annee, mois, 1)
                fin = getMonthEnd(debut)
                for inscrit in creche.inscrits:
                    if inscrit.GetInscriptions(debut, fin):
                        facture = FactureFinMois(inscrit, self.annee, mois)
                        for mode in (MODE_FORFAIT_MENSUEL, MODE_HALTE_GARDERIE):                        
                            heures_facturees_par_mode[mode] += facture.heures_facturees_par_mode[mode]
                        heures_facturees += facture.heures_facturees
                        cotisations_facturees += facture.total

                fields.append(("heures-ouvrees[%d]" % (mois), heures_ouvrees*creche.capacite))
                fields.append(("heures-facturees[forfait][%d]" % (mois), heures_facturees_par_mode[MODE_FORFAIT_MENSUEL]))
                fields.append(("heures-facturees[hg][%d]" % (mois), heures_facturees_par_mode[MODE_HALTE_GARDERIE]))
                fields.append(("heures-facturees[%d]" % (mois), heures_facturees))
                fields.append(("cotisations[%d]" % (mois), cotisations_facturees))
                fields.append(("charges[%d]" % (mois), creche.charges[datetime.date(self.annee, mois, 1)].charges))

            ReplaceFields(lines, fields)
            
            
#                debut = datetime.date(annee, mois+1, 1)
#                fin = getMonthEnd(debut)
#                for inscrit in creche.inscrits:
#                    try:
#                        if inscrit.GetInscriptions(debut, fin):
#                            facture = FactureFinMois(inscrit, annee, mois+1)
#                            heures_contractualisees += facture.heures_contractualisees
#                            heures_realisees += facture.heures_realisees                       
#                            heures_facturees += sum(facture.heures_facturees)
#                            cotisations_contractualisees += facture.cotisation_mensuelle
#                            cotisations_realisees += facture.total_realise
#                            cotisations_facturees += facture.total
#                    except Exception, e:
#                        erreurs.append((inscrit, e))
                        
            # LES 4 TRIMESTRES
 
        return self.errors

 

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    filename = 'synthese_financiere_%d.ods' % (today.year - 1)
    print GenerateOODocument(SyntheseFinanciereModifications(today.year - 1), filename)
    print u'Fichier %s généré' % filename
