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
from database import Creche, Site
from generation.email_helpers import SendToParentsMixin
from generation.opendocument import OpenDocumentText


class AttestationPaiementDocument(OpenDocumentText, SendToParentsMixin):
    title = "Attestation mensuelle"
    template = "Attestation paiement.odt"

    def __init__(self, who, debut, fin):
        OpenDocumentText.__init__(self)
        self.debut, self.fin = debut, fin
        if isinstance(who, list):
            self.inscrits = [inscrit for inscrit in who if inscrit.get_inscriptions(debut, fin)]
        elif isinstance(who, Creche):
            self.inscrits = [inscrit for inscrit in who.inscrits if inscrit.get_inscriptions(debut, fin)]
        elif isinstance(who, Site):
            self.inscrits = []
            for inscrit in database.creche.inscrits:
                for inscription in inscrit.get_inscriptions(debut, fin):
                    if inscription.site == who:
                        self.inscrits.append(inscrit)
                        break
        else:
            self.inscrits = [who]

        self.inscrits = GetEnfantsTriesSelonParametreTriFacture(self.inscrits)

        if len(self.inscrits) > 1:
            output_start = "Attestations de paiement"
        else:
            output_start = "Attestation de paiement %s" % GetPrenomNom(self.inscrits[0])
        if debut.year == fin.year and debut.month == fin.month:
            self.set_default_output(output_start + " %s %d" % (months[debut.month - 1], debut.year))
        else:
            self.set_default_output(output_start + " %s-%s %d" % (months[debut.month - 1], months[fin.month - 1], debut.year))

        SendToParentsMixin.__init__(self, self.default_output[:-4], "Accompagnement attestation paiement.txt", [], "%(count)d attestations envoyées")

    def split(self, who):
        return AttestationPaiementDocument(who, self.debut, self.fin)

    def modify_content(self, dom):
        OpenDocumentText.modify_content(self, dom)
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
                    if facture.total != 0:
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
                self.errors[GetPrenomNom(inscrit)] = e.errors
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
                ('date', date2str(datetime.date.today())),
                ('date-debut-mois-suivant', date2str(GetNextMonthStart(self.debut))),
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

            bureau = Select(database.creche.bureaux, datetime.date.today())
            if bureau:
                fields.extend(GetBureauFields(bureau))
            
            empty_fields = [(field[0], " ") for field in fields]

            for template in templates:
                section = template.cloneNode(1)
                section_name = section.getAttribute("text:name")
                autorisation = inscrit.famille.autorisation_attestation_paje
                if (section_name == "Famille uniquement" and autorisation) or (section_name == "Structure uniquement" and not autorisation):
                    continue
                elif (section_name == "Famille" and autorisation) or (section_name == "Structure" and not autorisation):
                    self.replace_text_fields(section, empty_fields)
                else:
                    self.replace_text_fields(section, fields)
                doc.appendChild(section)
                
        return True
