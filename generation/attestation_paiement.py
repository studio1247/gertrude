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
from __future__ import division

from facture import *
from cotisation import CotisationException
from ooffice import *
from database import Creche, Site


class AttestationModifications(object):
    title = "Attestation mensuelle"
    template = "Attestation paiement.odt"

    def __init__(self, who, debut, fin, attestation_mensuelle=False):
        self.debut, self.fin = debut, fin
        self.attestation_mensuelle = False
        if attestation_mensuelle and IsTemplateFile("Attestation mensuelle.odt"):
            self.template = "Attestation mensuelle.odt"
            self.attestation_mensuelle = True
        if isinstance(who, list):
            self.inscrits = [inscrit for inscrit in who if inscrit.get_inscriptions(debut, fin)]
            self.SetDefaultMultiParam()
        elif isinstance(who, Creche):
            self.inscrits = [inscrit for inscrit in who.inscrits if inscrit.get_inscriptions(debut, fin)]
            self.SetDefaultMultiParam()
        elif isinstance(who, Site):
            self.inscrits = []
            for inscrit in database.creche.inscrits:
                for inscription in inscrit.get_inscriptions(debut, fin):
                    if inscription.site == who:
                        self.inscrits.append(inscrit)
                        break
            self.SetDefaultMultiParam()
        else:
            self.inscrits = [who]
            if debut.year == fin.year and debut.month == fin.month:
                self.email_subject = "Attestation de paiement %s %s %s %d" % (who.prenom, who.nom, months[debut.month - 1], debut.year)
            else:
                self.email_subject = "Attestation de paiement %s %s %s-%s %d" % (who.prenom, who.nom, months[debut.month - 1], months[fin.month - 1], debut.year)
            self.email_to = list(set([parent.email for parent in who.famille.parents if parent and parent.email]))
            self.multi = False
        self.default_output = self.email_subject + ".odt"
        self.inscrits = GetEnfantsTriesSelonParametreTriFacture(self.inscrits)
        self.email = True
        self.site = None
        self.introduction_filename = "Accompagnement attestation paiement.txt"
        self.reservataire = None

    def GetIntroductionFields(self):
        return []

    def get_attachments(self):
        return []

    def SetDefaultMultiParam(self):
        if self.debut.year == self.fin.year and self.debut.month == self.fin.month:
            self.email_subject = "Attestations de paiement %s %d" % (months[self.debut.month - 1], self.debut.year)
        else:
            self.email_subject = "Attestations de paiement %s-%s %d" % (months[self.debut.month - 1], months[self.fin.month - 1], self.debut.year)
        self.email_to = None
        self.multi = True

    def get_simple_filename(self, filename, inscrit):
        result = filename.replace("Attestations de paiement", "Attestation de paiement %s" % GetPrenomNom(inscrit)) \
                         .replace("Attestations", "Attestation %s" % GetPrenomNom(inscrit)) \
                         .replace("<enfant>", GetPrenomNom(inscrit)) \
                         .replace("<prenom>", inscrit.prenom) \
                         .replace("<nom>", inscrit.nom)
        if result == filename:
            result = "[%s] %s" % (GetPrenomNom(inscrit), filename)
        return result

    def get_simple_modifications(self, filename):
        return [(self.get_simple_filename(filename, inscrit), AttestationModifications(inscrit, self.debut, self.fin, self.attestation_mensuelle)) for inscrit in self.inscrits]
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        errors = {}
        tresorier = ""
        directeur = ""
        bureau = Select(database.creche.bureaux, today)
        if bureau:
            tresorier = bureau.tresorier
            directeur = bureau.directeur
        
        # print dom.toprettyxml()
        doc = dom.getElementsByTagName("office:text")[0]
        templates = doc.getElementsByTagName("text:section")
        for template in templates:
            doc.removeChild(template)

        for inscrit in self.inscrits:
            facture_debut = facture_fin = None
            date = self.debut
            heures_contractualisees, heures_facturees, heures_facture, heures_realisees, total_sans_activites = 0.0, 0.0, 0.0, 0.0, 0.0
            total = 0.0
            site = None
            try:
                while date <= self.fin:
                    facture = Facture(inscrit, date.year, date.month, NO_NUMERO)
                    site = facture.site
                    if facture.total != 0 or (self.attestation_mensuelle and len(self.inscrits) == 1):
                        if facture_debut is None:
                            facture_debut = date
                        facture_fin = GetMonthEnd(date)
                        total += facture.total
                        total_sans_activites += facture.total - facture.supplement_activites
                        heures_realisees += facture.heures_realisees
                        heures_facturees += facture.heures_facturees
                        heures_facture += facture.heures_facture
                        heures_contractualisees += facture.heures_contractualisees
                    date = GetNextMonthStart(date)
            except CotisationException as e:
                errors[GetPrenomNom(inscrit)] = e.errors
                continue
            
            if facture_debut is None:
                continue
            
            last_inscription = None
            for tmp in inscrit.inscriptions:
                if not last_inscription or not last_inscription.fin or (tmp.fin and tmp.fin > last_inscription.fin):
                    last_inscription = tmp 
            
            # Les champs de l'attestation
            fields = GetCrecheFields(database.creche) + GetInscritFields(inscrit) + GetInscriptionFields(last_inscription) + [
                ('de-debut', '%s %d' % (GetDeMoisStr(facture_debut.month - 1), facture_debut.year)),
                ('de-fin', '%s %d' % (GetDeMoisStr(facture_fin.month - 1), facture_fin.year)),
                ('tresorier', tresorier),
                ('directeur', directeur),
                ('date', '%.2d/%.2d/%d' % (today.day, today.month, today.year)),
                ('heures-facture', GetHeureString(heures_facture)),
                ('ceil-heures-facture', GetHeureString(math.ceil(heures_facture))),
                ('heures-facturees', GetHeureString(heures_facturees)),
                ('heures-contractualisees', GetHeureString(heures_contractualisees)),
                ('ceil-heures-facturees', GetHeureString(math.ceil(heures_facturees))),
                ('ceil-heures-realisees', GetHeureString(math.ceil(heures_realisees))),
                ('total-sans-activites', "%.2f" % total_sans_activites),
                ('total', '%.2f' % total),
                ('site', GetNom(site)),
                ('dernier-mois', GetBoolStr(last_inscription.fin and last_inscription.fin <= facture_fin)),
            ]
            
            if self.attestation_mensuelle:
                fields.extend([
                    ('mois', months[facture_debut.month - 1]),
                    ('annee', facture_debut.year)
                ])
            
            empty_fields = [(field[0], " ") for field in fields]

            for template in templates:
                section = template.cloneNode(1)
                section_name = section.getAttribute("text:name")
                autorisation = inscrit.famille.autorisation_attestation_paje
                if (section_name == "Famille uniquement" and autorisation) or (section_name == "Structure uniquement" and not autorisation):
                    continue
                elif (section_name == "Famille" and autorisation) or (section_name == "Structure" and not autorisation):
                    ReplaceTextFields(section, empty_fields)
                else:
                    ReplaceTextFields(section, fields)
                doc.appendChild(section)
                
        return errors
